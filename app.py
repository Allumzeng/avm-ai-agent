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

_pinecone_index = None
_embedder = None
_agent = None
_wizard_engine = None


def _get_singletons():
    global _pinecone_index, _embedder, _agent, _wizard_engine
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
    return _agent, _wizard_engine


def route_message(
    message_text: str,
    wizard_state: Optional[WizardState],
) -> tuple[Literal["wizard_continue", "wizard_start", "qa"], Union[WizardState, str, None]]:
    if wizard_state and not wizard_state.is_complete:
        return "wizard_continue", wizard_state
    intent = detect_wizard_intent(message_text)
    if intent:
        return "wizard_start", intent
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
    _get_singletons()


@cl.on_message
async def on_message(message: cl.Message):
    role: str = cl.user_session.get("role", "analyst")
    history: list = cl.user_session.get("history", [])
    wizard_state: Optional[WizardState] = cl.user_session.get("wizard_state")

    history.append({"role": "user", "content": message.content})

    response_msg = cl.Message(content="Thinking...")
    await response_msg.send()

    route, payload = route_message(message.content, wizard_state)

    agent, wizard_engine = _get_singletons()

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

    else:
        response_text = agent.get_response(history=history, role=role)

    response_msg.content = response_text
    await response_msg.update()

    history.append({"role": "assistant", "content": response_text})
    cl.user_session.set("history", history)
