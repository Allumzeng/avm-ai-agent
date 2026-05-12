import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from typing import Literal, Optional, Union
import chainlit as cl

from src.config import (
    ANTHROPIC_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    VOYAGE_API_KEY,
)
from src.auth.users import authenticate
from src.rag.embedder import create_embedder
from src.rag.store import create_vector_store
from src.agent.client import AVMAgentClient
from src.wizard.engine import WizardEngine
from src.wizard.intent import detect_wizard_intent
from src.wizard.state import WizardState
from src.ingestion.chunker import _detect_language
from src.reporting.engine import ReportingEngine
from src.reporting.intent import detect_report_intent
from src.reporting.models import ReportState
from src.reporting.parser import parse_uploaded_file

_pinecone_index = None
_embedder = None
_agent = None
_wizard_engine = None
_reporting_engine = None


def _get_singletons():
    global _pinecone_index, _embedder, _agent, _wizard_engine, _reporting_engine
    if _agent is None:
        _pinecone_index = create_vector_store(PINECONE_API_KEY, PINECONE_INDEX_NAME)
        _embedder = create_embedder(VOYAGE_API_KEY)
        _agent = AVMAgentClient(
            api_key=ANTHROPIC_API_KEY,
            pinecone_index=_pinecone_index,
            embedder=_embedder,
        )
        _wizard_engine = WizardEngine(
            api_key=ANTHROPIC_API_KEY,
            pinecone_index=_pinecone_index,
            embedder=_embedder,
        )
        _reporting_engine = ReportingEngine(api_key=ANTHROPIC_API_KEY)
    return _agent, _wizard_engine, _reporting_engine


def route_message(
    message_text: str,
    wizard_state: Optional[WizardState],
    source_data: Optional[dict],
    report_state: Optional[ReportState],
) -> tuple[
    Literal["wizard_continue", "wizard_start", "report_generate", "report_drilldown", "qa"],
    Union[WizardState, str, ReportState, None],
]:
    # 1. Active wizard takes priority
    if wizard_state and not wizard_state.is_complete:
        return "wizard_continue", wizard_state

    # 2. Wizard intent
    wizard_intent = detect_wizard_intent(message_text)
    if wizard_intent:
        return "wizard_start", wizard_intent

    # 3. Report generation intent (requires uploaded data)
    report_intent = detect_report_intent(message_text)
    if report_intent and source_data is not None:
        return "report_generate", report_intent

    # 4. Drill-down on completed report
    if report_state and report_state.is_complete:
        return "report_drilldown", report_state

    return "qa", None


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    user = authenticate(username, password)
    if user:
        return cl.User(
            identifier=username,
            metadata={"role": user["role"], "group": user["group"]},
        )
    return None


@cl.on_chat_start
async def on_chat_start():
    user = cl.user_session.get("user")
    role = user.metadata.get("role", "analyst") if user else "analyst"
    cl.user_session.set("role", role)
    cl.user_session.set("history", [])
    cl.user_session.set("wizard_state", None)
    cl.user_session.set("source_data", None)
    cl.user_session.set("report_state", None)
    _get_singletons()


@cl.on_message
async def on_message(message: cl.Message):
    role: str = cl.user_session.get("role", "analyst")
    history: list = cl.user_session.get("history", [])
    wizard_state: Optional[WizardState] = cl.user_session.get("wizard_state")
    source_data: Optional[dict] = cl.user_session.get("source_data")
    report_state: Optional[ReportState] = cl.user_session.get("report_state")

    response_text = ""

    # Handle file upload: parse and store, reset any previous report
    file_uploaded_this_turn = False
    for element in message.elements:
        if hasattr(element, "path") and element.path and hasattr(element, "name"):
            with open(element.path, "rb") as f:
                file_bytes = f.read()
            try:
                source_data = parse_uploaded_file(file_bytes, element.name)
                cl.user_session.set("source_data", source_data)
                cl.user_session.set("report_state", None)
                report_state = None
                file_uploaded_this_turn = True
            except ValueError as e:
                response_msg = cl.Message(content=f"⚠️ Could not read file: {e}")
                await response_msg.send()
                return

    # Guard: empty file (no parseable data rows)
    if file_uploaded_this_turn and not source_data["sheets"]:
        response_msg = cl.Message(
            content=(
                f"⚠️ **{source_data['file_name']}** was uploaded but contained no data rows. "
                "Please check the file and try again."
            )
        )
        await response_msg.send()
        return

    history.append({"role": "user", "content": message.content})

    response_msg = cl.Message(content="Thinking...")
    await response_msg.send()

    # If file was uploaded while mid-wizard, show upload prompt instead of routing to wizard
    if file_uploaded_this_turn and wizard_state and not wizard_state.is_complete:
        response_text = (
            f"File **{source_data['file_name']}** uploaded successfully "
            f"({sum(len(rows) for rows in source_data['sheets'].values())} data rows across "
            f"{len(source_data['sheets'])} sheet(s)).\n\n"
            "Which report would you like?\n"
            "- **Profitability report** — revenue, cost, net margin by customer/product\n"
            "- **Capacity analysis** — idle capacity and over-utilization by activity center\n"
            "- **Activity attribute dashboard** — value-added vs. non-value-added breakdown\n"
            "- **Value object report** — long-term vs. short-term value by customer/product"
        )
        history.append({"role": "assistant", "content": response_text})
        cl.user_session.set("history", history)
        response_msg.content = response_text
        await response_msg.update()
        return

    route, payload = route_message(message.content, wizard_state, source_data, report_state)

    agent, wizard_engine, reporting_engine = _get_singletons()

    if route == "wizard_continue":
        new_state, response_text = wizard_engine.step(payload, history, role)
        if new_state.is_complete:
            cl.user_session.set("wizard_state", None)
            response_text += "\n\n---\n*Wizard complete — returning to normal chat mode.*"
        else:
            cl.user_session.set("wizard_state", new_state)

    elif route == "wizard_start":
        lang = _detect_language(message.content)
        new_state, response_text = wizard_engine.start(payload, language=lang)
        cl.user_session.set("wizard_state", new_state)

    elif route == "report_generate":
        report_type: str = payload
        new_report = reporting_engine.generate(report_type, source_data, role)
        cl.user_session.set("report_state", new_report)

        anomaly_block = ""
        if new_report.anomalies:
            items = "\n".join(f"- ⚠️ {a}" for a in new_report.anomalies)
            anomaly_block = f"**Anomalies detected:**\n{items}\n\n---\n\n"
        response_text = anomaly_block + new_report.report_text

    elif route == "report_drilldown":
        if report_state.report_text:
            drill_history = list(history)
            drill_history.insert(
                -1,
                {
                    "role": "assistant",
                    "content": (
                        f"[Previously generated report for reference:]\n\n"
                        f"{report_state.report_text}"
                    ),
                },
            )
            response_text = agent.get_response(history=drill_history, role=role)
        else:
            response_text = agent.get_response(history=history, role=role)

    else:
        response_text = agent.get_response(history=history, role=role)

    # If a file was uploaded this turn but routing didn't generate a report, prompt user
    if file_uploaded_this_turn and route != "report_generate":
        response_text = (
            f"File **{source_data['file_name']}** uploaded successfully "
            f"({sum(len(rows) for rows in source_data['sheets'].values())} data rows across "
            f"{len(source_data['sheets'])} sheet(s)).\n\n"
            "Which report would you like?\n"
            "- **Profitability report** — revenue, cost, net margin by customer/product\n"
            "- **Capacity analysis** — idle capacity and over-utilization by activity center\n"
            "- **Activity attribute dashboard** — value-added vs. non-value-added breakdown\n"
            "- **Value object report** — long-term vs. short-term value by customer/product"
        )

    response_msg.content = response_text
    await response_msg.update()

    history.append({"role": "assistant", "content": response_text})
    cl.user_session.set("history", history)
