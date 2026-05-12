# AVM Reporting Engine — Sprint 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Analysis & Reporting mode to the AVM AI Agent — users upload an Excel/CSV file, request one of four AVM report types, receive a structured report with anomaly flags, then drill down via follow-up chat.

**Architecture:** A new `src/reporting/` package handles parsing, tool dispatch, and Claude Opus 4.7-powered report generation. `app.py` detects file uploads through `message.elements`, stores parsed data in session, routes report-intent messages to `ReportingEngine`, and injects completed reports into history for drill-down Q&A. All report generation uses Claude Opus 4.7 (extended reasoning for complex analysis); everything else keeps Sonnet 4.6.

**Tech Stack:** Python 3.12, Anthropic SDK (claude-opus-4-7), openpyxl, Chainlit, existing Pinecone/Voyage RAG stack, pytest

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `src/reporting/__init__.py` | Create | Package marker |
| `src/reporting/parser.py` | Create | Parse Excel/CSV bytes → structured dict |
| `src/reporting/models.py` | Create | `ReportState` dataclass + JSON serialization |
| `src/reporting/tools.py` | Create | Claude tools: `generate_report`, `flag_anomaly`; `dispatch_report_tool()` |
| `src/reporting/engine.py` | Create | `ReportingEngine` — Claude Opus tool-use loop |
| `src/reporting/intent.py` | Create | `detect_report_intent()` — keyword matcher returning report type string |
| `requirements.txt` | Modify | Add `openpyxl>=3.1.0,<4.0.0` |
| `app.py` | Modify | File upload detection, report routing, drill-down injection |
| `tests/test_reporting_parser.py` | Create | Parser unit tests |
| `tests/test_reporting_models.py` | Create | ReportState serialization tests |
| `tests/test_reporting_tools.py` | Create | Tool dispatch tests |
| `tests/test_reporting_engine.py` | Create | Engine tests (mocked Claude) |
| `tests/test_reporting_intent.py` | Create | Intent detection tests |
| `tests/test_app_routing.py` | Modify | Update existing tests to pass new `route_message` params; add report routing tests |

---

## Task 1: Data Parser

**Files:**
- Create: `src/reporting/__init__.py`
- Create: `src/reporting/parser.py`
- Modify: `requirements.txt`
- Create: `tests/test_reporting_parser.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_reporting_parser.py
import io
import csv
import openpyxl
from src.reporting.parser import parse_uploaded_file


def _make_excel_bytes(sheets: dict[str, list[dict]]) -> bytes:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for sheet_name, rows in sheets.items():
        ws = wb.create_sheet(sheet_name)
        if rows:
            headers = list(rows[0].keys())
            ws.append(headers)
            for row in rows:
                ws.append([row.get(h) for h in headers])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _make_csv_bytes(rows: list[dict]) -> bytes:
    if not rows:
        return b""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def test_parse_csv_returns_rows():
    rows = [{"customer": "Alpha", "revenue": "100"}, {"customer": "Beta", "revenue": "200"}]
    result = parse_uploaded_file(_make_csv_bytes(rows), "data.csv")
    assert result["file_name"] == "data.csv"
    assert "Sheet1" in result["sheets"]
    assert len(result["sheets"]["Sheet1"]) == 2
    assert result["sheets"]["Sheet1"][0]["customer"] == "Alpha"


def test_parse_excel_returns_sheets():
    data = {"Revenue": [{"customer": "Alpha", "amount": 100}, {"customer": "Beta", "amount": 200}]}
    result = parse_uploaded_file(_make_excel_bytes(data), "report.xlsx")
    assert result["file_name"] == "report.xlsx"
    assert "Revenue" in result["sheets"]
    assert len(result["sheets"]["Revenue"]) == 2


def test_parse_excel_skips_empty_rows():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(["col_a", "col_b"])
    ws.append(["val1", "val2"])
    ws.append([None, None])   # empty row — should be excluded
    ws.append(["val3", "val4"])
    buf = io.BytesIO()
    wb.save(buf)
    result = parse_uploaded_file(buf.getvalue(), "test.xlsx")
    assert len(result["sheets"]["Data"]) == 2


def test_parse_excel_multiple_sheets():
    data = {
        "Module2": [{"activity_center": "Finance", "normal_capacity": 480}],
        "Module3": [{"activity": "Budgeting", "actual_time": 60}],
    }
    result = parse_uploaded_file(_make_excel_bytes(data), "avm.xlsx")
    assert "Module2" in result["sheets"]
    assert "Module3" in result["sheets"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_reporting_parser.py -v`
Expected: `ModuleNotFoundError: No module named 'src.reporting'`

- [ ] **Step 3: Add openpyxl to requirements.txt**

Open `requirements.txt` and add after the last entry:
```
openpyxl>=3.1.0,<4.0.0
```

- [ ] **Step 4: Install openpyxl**

Run: `pip install openpyxl`

- [ ] **Step 5: Create the package marker**

Create `src/reporting/__init__.py` as an empty file.

- [ ] **Step 6: Implement the parser**

Create `src/reporting/parser.py`:

```python
import csv
import io

import openpyxl


def parse_uploaded_file(file_bytes: bytes, file_name: str) -> dict:
    """Parse an Excel (.xlsx) or CSV file into a structured dict.

    Returns:
        {
            "file_name": str,
            "sheets": {
                "<sheet_name>": [{"<col>": <value>, ...}, ...]
            }
        }
    """
    if file_name.lower().endswith(".csv"):
        return _parse_csv(file_bytes, file_name)
    return _parse_excel(file_bytes, file_name)


def _parse_excel(file_bytes: bytes, file_name: str) -> dict:
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    sheets = {}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = []
        headers: list[str] | None = None
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                headers = [
                    str(c) if c is not None else f"col_{j}"
                    for j, c in enumerate(row)
                ]
            else:
                if any(c is not None for c in row) and headers:
                    rows.append(dict(zip(headers, row)))
        if rows:
            sheets[sheet_name] = rows
    return {"file_name": file_name, "sheets": sheets}


def _parse_csv(file_bytes: bytes, file_name: str) -> dict:
    text = file_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = [dict(row) for row in reader]
    return {"file_name": file_name, "sheets": {"Sheet1": rows}}
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest tests/test_reporting_parser.py -v`
Expected: 4 PASSED

- [ ] **Step 8: Commit**

```bash
git add src/reporting/__init__.py src/reporting/parser.py requirements.txt tests/test_reporting_parser.py
git commit -m "feat(reporting): add Excel/CSV parser for uploaded data files"
```

---

## Task 2: Report Models

**Files:**
- Create: `src/reporting/models.py`
- Create: `tests/test_reporting_models.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_reporting_models.py
import json
from src.reporting.models import ReportState


def test_report_state_defaults():
    state = ReportState(report_type="profitability", source_data={"file_name": "x.xlsx", "sheets": {}})
    assert state.report_text == ""
    assert state.anomalies == []
    assert state.is_complete is False


def test_report_state_to_json():
    state = ReportState(
        report_type="capacity",
        source_data={"file_name": "data.xlsx", "sheets": {"S1": [{"a": 1}]}},
        report_text="## Report",
        anomalies=["Idle capacity at 35%"],
        is_complete=True,
    )
    raw = state.to_json()
    d = json.loads(raw)
    assert d["report_type"] == "capacity"
    assert d["report_text"] == "## Report"
    assert d["anomalies"] == ["Idle capacity at 35%"]
    assert d["is_complete"] is True


def test_report_state_roundtrip():
    state = ReportState(
        report_type="attribute",
        source_data={"file_name": "avm.xlsx", "sheets": {}},
        report_text="# Attribute Dashboard",
        anomalies=["NVA > 30%"],
        is_complete=True,
    )
    restored = ReportState.from_json(state.to_json())
    assert restored.report_type == state.report_type
    assert restored.report_text == state.report_text
    assert restored.anomalies == state.anomalies
    assert restored.is_complete == state.is_complete


def test_report_state_anomalies_isolated():
    # Verify that default anomalies list is not shared between instances
    a = ReportState(report_type="profitability", source_data={})
    b = ReportState(report_type="capacity", source_data={})
    a.anomalies.append("issue")
    assert b.anomalies == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_reporting_models.py -v`
Expected: `ModuleNotFoundError: No module named 'src.reporting.models'`

- [ ] **Step 3: Implement ReportState**

Create `src/reporting/models.py`:

```python
import json
from dataclasses import dataclass, field
from typing import Literal

ReportType = Literal["profitability", "capacity", "attribute", "value_object"]


@dataclass
class ReportState:
    report_type: ReportType
    source_data: dict
    report_text: str = ""
    anomalies: list[str] = field(default_factory=list)
    is_complete: bool = False

    def to_json(self) -> str:
        return json.dumps(
            {
                "report_type": self.report_type,
                "source_data": self.source_data,
                "report_text": self.report_text,
                "anomalies": self.anomalies,
                "is_complete": self.is_complete,
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, data: str) -> "ReportState":
        d = json.loads(data)
        return cls(
            report_type=d["report_type"],
            source_data=d["source_data"],
            report_text=d["report_text"],
            anomalies=d["anomalies"],
            is_complete=d["is_complete"],
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_reporting_models.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/reporting/models.py tests/test_reporting_models.py
git commit -m "feat(reporting): add ReportState dataclass with JSON serialization"
```

---

## Task 3: Report Tools

**Files:**
- Create: `src/reporting/tools.py`
- Create: `tests/test_reporting_tools.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_reporting_tools.py
from src.reporting.models import ReportState
from src.reporting.tools import dispatch_report_tool


def _make_state() -> ReportState:
    return ReportState(report_type="profitability", source_data={})


def test_generate_report_sets_text_and_complete():
    state = _make_state()
    result = dispatch_report_tool(
        "generate_report",
        {"report_text": "# Profitability Report\n\nAll good."},
        state,
    )
    assert state.report_text == "# Profitability Report\n\nAll good."
    assert state.is_complete is True
    assert "generated" in result.lower()


def test_flag_anomaly_appends_to_list():
    state = _make_state()
    dispatch_report_tool("flag_anomaly", {"anomaly": "Customer X has negative margin"}, state)
    dispatch_report_tool("flag_anomaly", {"anomaly": "Idle capacity at 40%"}, state)
    assert state.anomalies == ["Customer X has negative margin", "Idle capacity at 40%"]


def test_dispatch_unknown_tool_returns_error_string():
    state = _make_state()
    result = dispatch_report_tool("nonexistent_tool", {}, state)
    assert "Unknown" in result
    assert "nonexistent_tool" in result


def test_generate_report_does_not_affect_anomalies():
    state = _make_state()
    state.anomalies = ["existing anomaly"]
    dispatch_report_tool("generate_report", {"report_text": "Report text"}, state)
    assert state.anomalies == ["existing anomaly"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_reporting_tools.py -v`
Expected: `ModuleNotFoundError: No module named 'src.reporting.tools'`

- [ ] **Step 3: Implement report tools**

Create `src/reporting/tools.py`:

```python
from src.reporting.models import ReportState

REPORT_TOOLS = [
    {
        "name": "generate_report",
        "description": (
            "Generate the complete AVM management report in markdown format. "
            "Call this ONCE with the full report after all anomalies have been flagged. "
            "Structure the report with: Executive Summary, Key Metrics Table, "
            "Detailed Analysis by cost object, Hidden Costs section (capital cost, "
            "risk cost, inventory holding cost — include only if data is present), "
            "and Recommendations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "report_text": {
                    "type": "string",
                    "description": "Full report in GitHub-flavored markdown.",
                },
            },
            "required": ["report_text"],
        },
    },
    {
        "name": "flag_anomaly",
        "description": (
            "Flag a notable finding that deserves immediate user attention. "
            "Call this for each anomaly BEFORE calling generate_report. "
            "Trigger conditions: negative net margin for any cost object; "
            "idle capacity exceeding 20% of normal capacity at any activity center; "
            "non-value-added activities exceeding 30% of total activity cost; "
            "any customer or product with large revenue but negative long-term value."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "anomaly": {
                    "type": "string",
                    "description": "One clear sentence describing the anomaly, e.g. 'Customer Alpha generates NT$2M revenue but carries NT$2.4M in fully-allocated costs, yielding a -20% margin.'",
                },
            },
            "required": ["anomaly"],
        },
    },
]


def dispatch_report_tool(name: str, input_data: dict, state: ReportState) -> str:
    if name == "generate_report":
        state.report_text = input_data["report_text"]
        state.is_complete = True
        return "Report generated and stored."

    if name == "flag_anomaly":
        state.anomalies.append(input_data["anomaly"])
        return f"Anomaly flagged: {input_data['anomaly']}"

    return f"Unknown report tool: {name}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_reporting_tools.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/reporting/tools.py tests/test_reporting_tools.py
git commit -m "feat(reporting): add Claude tools for report generation and anomaly flagging"
```

---

## Task 4: Reporting Engine

**Files:**
- Create: `src/reporting/engine.py`
- Create: `tests/test_reporting_engine.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_reporting_engine.py
from unittest.mock import MagicMock, patch
from src.reporting.engine import ReportingEngine
from src.reporting.models import ReportState


def _make_engine() -> ReportingEngine:
    return ReportingEngine(api_key="test-key")


def _make_source_data() -> dict:
    return {
        "file_name": "avm_data.xlsx",
        "sheets": {
            "Revenue": [
                {"customer": "Alpha", "revenue": 1000000, "cost": 800000},
                {"customer": "Beta", "revenue": 500000, "cost": 600000},
            ]
        },
    }


def _mock_tool_use_then_end_turn(tool_calls: list[tuple[str, dict]]):
    """Build a mock Claude response sequence: tool_use calls then end_turn."""
    # First response: tool_use
    tool_blocks = []
    for i, (tool_name, tool_input) in enumerate(tool_calls):
        block = MagicMock()
        block.type = "tool_use"
        block.name = tool_name
        block.input = tool_input
        block.id = f"tool_{i}"
        tool_blocks.append(block)

    tool_response = MagicMock()
    tool_response.stop_reason = "tool_use"
    tool_response.content = tool_blocks

    # Second response: end_turn
    end_response = MagicMock()
    end_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = ""
    end_response.content = [text_block]

    return [tool_response, end_response]


def test_generate_returns_complete_report_state():
    engine = _make_engine()
    responses = _mock_tool_use_then_end_turn([
        ("generate_report", {"report_text": "# Profitability Report\n\nAlpha: profitable. Beta: loss."}),
    ])
    with patch.object(engine.client.messages, "create", side_effect=responses):
        state = engine.generate("profitability", _make_source_data(), "analyst")

    assert isinstance(state, ReportState)
    assert state.is_complete is True
    assert "Profitability Report" in state.report_text
    assert state.report_type == "profitability"


def test_generate_collects_anomalies_before_report():
    engine = _make_engine()
    responses = _mock_tool_use_then_end_turn([
        ("flag_anomaly", {"anomaly": "Beta has negative margin of -20%"}),
        ("flag_anomaly", {"anomaly": "Idle capacity at Finance center is 35%"}),
        ("generate_report", {"report_text": "# Capacity Report\n\nSee anomalies above."}),
    ])
    with patch.object(engine.client.messages, "create", side_effect=responses):
        state = engine.generate("capacity", _make_source_data(), "manager")

    assert len(state.anomalies) == 2
    assert "Beta" in state.anomalies[0]
    assert state.is_complete is True


def test_generate_raises_on_unexpected_stop_reason():
    import pytest
    engine = _make_engine()
    bad_response = MagicMock()
    bad_response.stop_reason = "max_tokens"
    bad_response.content = []
    with patch.object(engine.client.messages, "create", return_value=bad_response):
        with pytest.raises(RuntimeError, match="max_tokens"):
            engine.generate("profitability", _make_source_data(), "analyst")


def test_format_data_truncates_long_sheets():
    from src.reporting.engine import _format_data_for_claude
    rows = [{"a": i, "b": i * 2} for i in range(60)]
    source_data = {"file_name": "big.xlsx", "sheets": {"Sheet1": rows}}
    result = _format_data_for_claude(source_data)
    assert "truncated" in result
    # Should have exactly 50 data rows rendered
    assert result.count("| ") > 0


def test_generate_uses_opus_model():
    """Verify the engine calls claude-opus-4-7, not sonnet."""
    engine = _make_engine()
    responses = _mock_tool_use_then_end_turn([
        ("generate_report", {"report_text": "Report"}),
    ])
    calls = []

    def capture_create(**kwargs):
        calls.append(kwargs)
        return responses[len(calls) - 1]

    with patch.object(engine.client.messages, "create", side_effect=capture_create):
        engine.generate("profitability", _make_source_data(), "analyst")

    assert calls[0]["model"] == "claude-opus-4-7"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_reporting_engine.py -v`
Expected: `ModuleNotFoundError: No module named 'src.reporting.engine'`

- [ ] **Step 3: Implement the reporting engine**

Create `src/reporting/engine.py`:

```python
import anthropic
from src.agent.prompt import AVM_CORE_KNOWLEDGE
from src.reporting.models import ReportState, ReportType
from src.reporting.tools import REPORT_TOOLS, dispatch_report_tool

_REPORT_DESCRIPTIONS = {
    "profitability": (
        "Customer/Product Profitability Report — show revenue, fully-allocated cost "
        "(including AVM hidden costs: capital cost, risk cost, inventory holding cost where data is present), "
        "and net profit per customer and product. Flag customers or products with negative margins."
    ),
    "capacity": (
        "Capacity Analysis Report — compare normal capacity vs actual capacity by activity center, "
        "calculate idle capacity cost and over-utilization cost. "
        "Flag any activity center with idle capacity exceeding 20% of normal capacity."
    ),
    "attribute": (
        "Activity Attribute Dashboard — break down activity costs by the five AVM attribute types: "
        "quality (preventive / appraisal / internal failure / external failure), "
        "capacity (productive / non-productive / idle), "
        "value-added vs non-value-added, customer service stages, and ESG categories. "
        "Flag if non-value-added activities exceed 30% of total activity cost."
    ),
    "value_object": (
        "Value Object Report — analyze long-term vs short-term value per customer or product. "
        "Flag any value object where large revenue coexists with low or negative long-term value "
        "(the 'large client, actually unprofitable' AVM pattern)."
    ),
}


def _build_report_system_prompt(report_type: str, role: str) -> str:
    return f"""{AVM_CORE_KNOWLEDGE}

You are generating a {_REPORT_DESCRIPTIONS[report_type]}

The current user role is: {role}. Calibrate the level of detail accordingly.

Instructions:
1. First, call `flag_anomaly` for each significant finding you identify in the data.
2. Then call `generate_report` once with the complete structured report in GitHub-flavored markdown.
3. Report structure: Executive Summary → Key Metrics Table → Detailed Analysis by cost object → Hidden Costs (only if data present) → Recommendations.
4. Respond in the same language as the column headers of the uploaded data (Traditional Chinese if headers are in Chinese, English otherwise).
5. Do NOT produce any text outside of tool calls — all output goes through the tools."""


def _format_data_for_claude(source_data: dict) -> str:
    """Convert parsed data dict to a compact markdown table for Claude context."""
    lines = [f"**File:** {source_data.get('file_name', 'unknown')}"]
    for sheet_name, rows in source_data.get("sheets", {}).items():
        lines.append(f"\n### Sheet: {sheet_name} ({len(rows)} rows)")
        if not rows:
            continue
        headers = list(rows[0].keys())
        lines.append("| " + " | ".join(str(h) for h in headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        display_rows = rows[:50]
        for row in display_rows:
            lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
        if len(rows) > 50:
            lines.append(f"_... {len(rows) - 50} more rows truncated_")
    return "\n".join(lines)


class ReportingEngine:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, report_type: ReportType, source_data: dict, role: str) -> ReportState:
        state = ReportState(report_type=report_type, source_data=source_data)
        system = _build_report_system_prompt(report_type, role)
        data_text = _format_data_for_claude(source_data)

        messages = [
            {
                "role": "user",
                "content": (
                    f"Here is the uploaded AVM data:\n\n{data_text}\n\n"
                    f"Please generate the {report_type} report."
                ),
            }
        ]

        while True:
            response = self.client.messages.create(
                model="claude-opus-4-7",
                max_tokens=8192,
                system=system,
                messages=messages,
                tools=REPORT_TOOLS,
            )

            if response.stop_reason == "end_turn":
                return state

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = dispatch_report_tool(block.name, block.input, state)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                raise RuntimeError(f"Unexpected stop_reason from Claude API: {response.stop_reason!r}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_reporting_engine.py -v`
Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/reporting/engine.py tests/test_reporting_engine.py
git commit -m "feat(reporting): add ReportingEngine using Claude Opus 4.7 for AVM report generation"
```

---

## Task 5: Report Intent Detection

**Files:**
- Create: `src/reporting/intent.py`
- Create: `tests/test_reporting_intent.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_reporting_intent.py
from src.reporting.intent import detect_report_intent


def test_detect_profitability_english():
    assert detect_report_intent("generate a profitability report") == "profitability"


def test_detect_profitability_chinese():
    assert detect_report_intent("幫我做獲利分析") == "profitability"


def test_detect_capacity_english():
    assert detect_report_intent("show me the capacity analysis") == "capacity"


def test_detect_capacity_chinese():
    assert detect_report_intent("我想看閒置產能報告") == "capacity"


def test_detect_attribute_english():
    assert detect_report_intent("create an activity attribute dashboard") == "attribute"


def test_detect_attribute_chinese():
    assert detect_report_intent("請做作業屬性分析") == "attribute"


def test_detect_value_object_english():
    assert detect_report_intent("generate a value object report") == "value_object"


def test_detect_value_object_chinese():
    assert detect_report_intent("分析長期價值") == "value_object"


def test_no_match_returns_none():
    assert detect_report_intent("what is AVM?") is None
    assert detect_report_intent("help me with module 2") is None


def test_case_insensitive():
    assert detect_report_intent("Profitability Report please") == "profitability"
    assert detect_report_intent("CAPACITY ANALYSIS") == "capacity"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_reporting_intent.py -v`
Expected: `ModuleNotFoundError: No module named 'src.reporting.intent'`

- [ ] **Step 3: Implement intent detection**

Create `src/reporting/intent.py`:

```python
_INTENT_PATTERNS: dict[str, list[str]] = {
    "profitability": [
        "profitability report",
        "profit report",
        "profitability analysis",
        "customer profitability",
        "product profitability",
        "獲利分析",
        "利潤報告",
        "盈利報告",
        "顧客獲利",
        "產品獲利",
        "獲利報告",
    ],
    "capacity": [
        "capacity report",
        "capacity analysis",
        "idle capacity",
        "capacity utilization",
        "activity center report",
        "產能分析",
        "產能報告",
        "閒置產能",
        "作業中心報告",
        "產能利用",
    ],
    "attribute": [
        "attribute report",
        "attribute dashboard",
        "activity attribute",
        "value-added analysis",
        "non-value-added",
        "屬性報告",
        "作業屬性",
        "附加價值分析",
        "無附加價值",
        "屬性分析",
    ],
    "value_object": [
        "value object report",
        "value object analysis",
        "long-term value",
        "customer value report",
        "product value report",
        "價值標的報告",
        "長期價值",
        "顧客價值",
        "產品價值",
        "價值標的分析",
    ],
}


def detect_report_intent(text: str) -> str | None:
    """Return report type string if text contains a report generation request, else None."""
    lower = text.lower()
    for report_type, patterns in _INTENT_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in lower:
                return report_type
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_reporting_intent.py -v`
Expected: 10 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/reporting/intent.py tests/test_reporting_intent.py
git commit -m "feat(reporting): add report intent detector for four AVM report types"
```

---

## Task 6: App Integration

**Files:**
- Modify: `app.py` (add `ReportingEngine` singleton, file upload detection, report routing, drill-down)
- Modify: `tests/test_app_routing.py` (update existing tests for new `route_message` signature; add report routing tests)

### Context

The current `route_message` signature is:
```python
def route_message(
    message_text: str,
    wizard_state: Optional[WizardState],
) -> tuple[Literal["wizard_continue", "wizard_start", "qa"], Union[WizardState, str, None]]:
```

This task extends it to also handle reporting routes. The new signature adds `source_data` and `report_state`:
```python
def route_message(
    message_text: str,
    wizard_state: Optional[WizardState],
    source_data: Optional[dict],
    report_state: Optional[ReportState],
) -> tuple[
    Literal["wizard_continue", "wizard_start", "report_generate", "report_drilldown", "qa"],
    Union[WizardState, str, ReportState, None],
]:
```

Priority order (highest to lowest):
1. `wizard_continue` — active, incomplete wizard
2. `wizard_start` — wizard intent detected
3. `report_generate` — report intent detected AND `source_data` is not None
4. `report_drilldown` — a completed report exists in session (`report_state.is_complete`)
5. `qa` — fallback

Drill-down works by returning `"report_drilldown"` so `on_message` can inject the report text as context into the history before calling the Q&A agent.

File uploads arrive through `message.elements` as `cl.File` objects with `.path` (temp path on server) and `.name` attributes. Handle file detection before routing.

- [ ] **Step 1: Update existing routing tests and add new ones**

Open `tests/test_app_routing.py`. The file currently has 7 tests, all calling `route_message(text, wizard_state)` with 2 args. Update every call to pass the two new params as `None`:

```python
# tests/test_app_routing.py
from typing import Optional
from unittest.mock import MagicMock
from src.wizard.state import WizardState
from src.reporting.models import ReportState
from app import route_message


# ── Existing wizard tests (updated to pass new params) ──────────────────────

def test_active_wizard_returns_wizard_continue():
    state = WizardState(wizard_type="setup", is_complete=False)
    route, payload = route_message("hello", state, None, None)
    assert route == "wizard_continue"
    assert payload is state


def test_setup_intent_returns_wizard_start():
    route, payload = route_message("I want to set up AVM", None, None, None)
    assert route == "wizard_start"
    assert payload == "setup"


def test_diagnosis_intent_returns_wizard_start():
    route, payload = route_message("我想診斷成本問題", None, None, None)
    assert route == "wizard_start"


def test_no_intent_returns_qa():
    route, payload = route_message("what is idle capacity?", None, None, None)
    assert route == "qa"
    assert payload is None


def test_completed_wizard_returns_qa():
    state = WizardState(wizard_type="setup", is_complete=True)
    route, _ = route_message("what is idle capacity?", state, None, None)
    assert route == "qa"


def test_completed_wizard_can_restart():
    state = WizardState(wizard_type="setup", is_complete=True)
    route, payload = route_message("start AVM setup wizard", state, None, None)
    assert route == "wizard_start"
    assert payload == "setup"


def test_active_wizard_takes_priority_over_intent():
    state = WizardState(wizard_type="setup", is_complete=False)
    route, payload = route_message("start AVM setup wizard", state, None, None)
    assert route == "wizard_continue"
    assert payload is state


# ── New report routing tests ─────────────────────────────────────────────────

def test_report_intent_with_source_data_returns_report_generate():
    source_data = {"file_name": "x.xlsx", "sheets": {}}
    route, payload = route_message("generate a profitability report", None, source_data, None)
    assert route == "report_generate"
    assert payload == "profitability"


def test_report_intent_without_source_data_returns_qa():
    # No data uploaded yet — can't generate report
    route, payload = route_message("generate a profitability report", None, None, None)
    assert route == "qa"


def test_completed_report_returns_drilldown():
    report_state = ReportState(
        report_type="profitability",
        source_data={},
        report_text="# Report",
        is_complete=True,
    )
    route, payload = route_message("why is customer Alpha unprofitable?", None, None, report_state)
    assert route == "report_drilldown"
    assert payload is report_state


def test_wizard_takes_priority_over_report_drilldown():
    wizard_state = WizardState(wizard_type="setup", is_complete=False)
    report_state = ReportState(report_type="capacity", source_data={}, is_complete=True)
    route, payload = route_message("continue", wizard_state, None, report_state)
    assert route == "wizard_continue"


def test_report_generate_takes_priority_over_drilldown():
    # A new report intent with data uploaded should regenerate, not drilldown
    source_data = {"file_name": "new.xlsx", "sheets": {}}
    old_report = ReportState(report_type="capacity", source_data={}, is_complete=True)
    route, payload = route_message("generate capacity report", None, source_data, old_report)
    assert route == "report_generate"
    assert payload == "capacity"
```

- [ ] **Step 2: Run updated tests to verify they fail in the expected way**

Run: `pytest tests/test_app_routing.py -v`
Expected: The 7 existing tests fail with `TypeError` (wrong number of args); the 5 new tests fail with `TypeError` or import errors. This confirms the tests are wired to the real code.

- [ ] **Step 3: Update `app.py`**

Open `app.py`. Replace the entire file with the updated version below. Key changes:
- Import `ReportingEngine`, `ReportState`, `parse_uploaded_file`, `detect_report_intent`
- Add `_reporting_engine` to `_get_singletons()`
- Extend `route_message()` with two new params and three new routes
- Add file upload detection in `on_message` before routing
- Add report generation and drill-down branches in `on_message`

```python
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
from src.reporting.engine import ReportingEngine
from src.reporting.intent import detect_report_intent
from src.reporting.models import ReportState
from src.reporting.parser import parse_uploaded_file
from src.ingestion.chunker import _detect_language

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

    # Handle file upload: parse and store, reset any previous report
    for element in message.elements:
        if hasattr(element, "path") and element.path and hasattr(element, "name"):
            with open(element.path, "rb") as f:
                file_bytes = f.read()
            source_data = parse_uploaded_file(file_bytes, element.name)
            cl.user_session.set("source_data", source_data)
            cl.user_session.set("report_state", None)
            report_state = None

    history.append({"role": "user", "content": message.content})

    response_msg = cl.Message(content="Thinking...")
    await response_msg.send()

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

        # Build response: anomaly highlights + report body
        anomaly_block = ""
        if new_report.anomalies:
            items = "\n".join(f"- ⚠️ {a}" for a in new_report.anomalies)
            anomaly_block = f"**Anomalies detected:**\n{items}\n\n---\n\n"
        response_text = anomaly_block + new_report.report_text

    elif route == "report_drilldown":
        # Inject the existing report as context for Q&A drill-down
        drill_history = list(history)
        drill_history.insert(
            -1,  # before the current user message
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

    # If file was uploaded but no report generated yet, prompt user
    if source_data and route not in ("report_generate", "report_drilldown") and not message.elements:
        pass  # source_data acknowledged silently; user can request a report

    if source_data and message.elements and route not in ("report_generate",):
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
```

- [ ] **Step 4: Run all routing tests**

Run: `pytest tests/test_app_routing.py -v`
Expected: 12 PASSED (7 updated existing + 5 new)

- [ ] **Step 5: Run the full test suite**

Run: `pytest -v`
Expected: All tests PASS. Count should be previous total + new tests from this sprint.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_app_routing.py
git commit -m "feat(reporting): integrate ReportingEngine into app — file upload, report routing, drill-down Q&A"
```

---

## Verification Checklist

After all tasks are complete, verify end-to-end behavior:

1. **Parser**: `pytest tests/test_reporting_parser.py -v` — 4 PASSED
2. **Models**: `pytest tests/test_reporting_models.py -v` — 4 PASSED
3. **Tools**: `pytest tests/test_reporting_tools.py -v` — 4 PASSED
4. **Engine**: `pytest tests/test_reporting_engine.py -v` — 5 PASSED
5. **Intent**: `pytest tests/test_reporting_intent.py -v` — 10 PASSED
6. **Routing**: `pytest tests/test_app_routing.py -v` — 12 PASSED
7. **Full suite**: `pytest -v` — all tests PASS

Live verification (requires API credentials):
- Upload a sample CSV with customer revenue and cost columns → confirm file acknowledgement message appears with sheet/row count
- Type "generate profitability report" → confirm report is generated with anomaly flags
- Ask a follow-up question about a flagged anomaly → confirm drill-down uses report context
- Start a wizard (`"start AVM setup wizard"`) → confirm wizard routing is unaffected
