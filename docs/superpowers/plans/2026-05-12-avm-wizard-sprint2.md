# AVM Wizard Engine — Sprint 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two guided wizard modes to the existing AVM AI Agent — a Setup Wizard that walks companies through 4-module AVM implementation, and a Diagnosis Wizard that performs symptom-driven root-cause analysis.

**Architecture:** Wizards run as a separate system-prompt mode within the same Chainlit chat. A `WizardEngine` class manages Claude tool-use loops with wizard-specific prompts; `detect_wizard_intent()` triggers the right wizard from natural language. `app.py` routes each message to either the wizard engine or the existing Q&A agent depending on session state.

**Tech Stack:** Python 3.12, Anthropic SDK (claude-sonnet-4-6), Chainlit, existing Pinecone/Voyage RAG stack, pytest

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `src/wizard/__init__.py` | Create | Package marker |
| `src/wizard/state.py` | Create | `WizardState` dataclass + JSON serialization |
| `src/wizard/intent.py` | Create | Keyword-based wizard trigger detection |
| `src/wizard/tools.py` | Create | `WIZARD_TOOLS` list (`save_wizard_data`, `complete_wizard`, `search_avm_knowledge`) |
| `src/wizard/prompts.py` | Create | Setup + diagnosis system prompt builders |
| `src/wizard/engine.py` | Create | `WizardEngine` — runs wizard steps via Claude tool-use loop |
| `src/agent/prompt.py` | Modify | Rename `_AVM_CORE_KNOWLEDGE` → `AVM_CORE_KNOWLEDGE` so wizards can import it |
| `app.py` | Modify | Add `route_message()` helper + wizard routing in `on_message` |
| `tests/test_wizard_state.py` | Create | State serialization tests |
| `tests/test_wizard_intent.py` | Create | Intent detection tests (EN + ZH) |
| `tests/test_wizard_tools.py` | Create | Wizard tool dispatch tests |
| `tests/test_wizard_prompts.py` | Create | Prompt structure/content tests |
| `tests/test_wizard_engine.py` | Create | Engine step tests (mocked Claude) |
| `tests/test_app_routing.py` | Create | `route_message()` unit tests |

---

## Task 1: WizardState Data Model

**Files:**
- Create: `src/wizard/__init__.py`
- Create: `src/wizard/state.py`
- Create: `tests/test_wizard_state.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_wizard_state.py
import json
from src.wizard.state import WizardState

def test_default_fields():
    s = WizardState(wizard_type="setup")
    assert s.current_step == 0
    assert s.collected_data == {}
    assert s.is_complete is False

def test_serialization_roundtrip():
    s = WizardState(
        wizard_type="diagnosis",
        current_step=2,
        collected_data={"symptom": "losing money"},
        is_complete=False,
    )
    s2 = WizardState.from_json(s.to_json())
    assert s2.wizard_type == "diagnosis"
    assert s2.current_step == 2
    assert s2.collected_data["symptom"] == "losing money"
    assert s2.is_complete is False

def test_json_preserves_chinese_characters():
    s = WizardState(wizard_type="setup", collected_data={"名稱": "測試公司"})
    s2 = WizardState.from_json(s.to_json())
    assert s2.collected_data["名稱"] == "測試公司"

def test_complete_flag_roundtrip():
    s = WizardState(wizard_type="setup", is_complete=True)
    s2 = WizardState.from_json(s.to_json())
    assert s2.is_complete is True
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_wizard_state.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.wizard'`

- [ ] **Step 3: Create the package marker**

```python
# src/wizard/__init__.py
# (empty file)
```

- [ ] **Step 4: Implement WizardState**

```python
# src/wizard/state.py
import json
from dataclasses import dataclass, field


@dataclass
class WizardState:
    wizard_type: str          # "setup" | "diagnosis"
    current_step: int = 0
    collected_data: dict = field(default_factory=dict)
    is_complete: bool = False

    def to_json(self) -> str:
        return json.dumps(
            {
                "wizard_type": self.wizard_type,
                "current_step": self.current_step,
                "collected_data": self.collected_data,
                "is_complete": self.is_complete,
            },
            ensure_ascii=False,
            indent=2,
        )

    @classmethod
    def from_json(cls, data: str) -> "WizardState":
        d = json.loads(data)
        return cls(
            wizard_type=d["wizard_type"],
            current_step=d["current_step"],
            collected_data=d["collected_data"],
            is_complete=d["is_complete"],
        )
```

- [ ] **Step 5: Run tests to verify they pass**

```
pytest tests/test_wizard_state.py -v
```
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/wizard/__init__.py src/wizard/state.py tests/test_wizard_state.py
git commit -m "feat: wizard state dataclass with json serialization"
```

---

## Task 2: Wizard Intent Detection

**Files:**
- Create: `src/wizard/intent.py`
- Create: `tests/test_wizard_intent.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_wizard_intent.py
from src.wizard.intent import detect_wizard_intent

# --- Setup triggers ---
def test_detects_setup_english():
    assert detect_wizard_intent("I want to start the AVM setup wizard") == "setup"

def test_detects_setup_shorthand():
    assert detect_wizard_intent("start wizard") == "setup"

def test_detects_setup_implement():
    assert detect_wizard_intent("help me implement AVM") == "setup"

def test_detects_setup_chinese():
    assert detect_wizard_intent("開始AVM設置精靈") == "setup"

# --- Diagnosis triggers ---
def test_detects_diagnosis_losing_money():
    assert detect_wizard_intent("We're losing money, help diagnose") == "diagnosis"

def test_detects_diagnosis_chinese_loss():
    assert detect_wizard_intent("我們公司最近在虧損") == "diagnosis"

def test_detects_diagnosis_margins():
    assert detect_wizard_intent("our margins are shrinking") == "diagnosis"

def test_detects_diagnosis_capacity():
    assert detect_wizard_intent("our capacity feels wasted") == "diagnosis"

def test_detects_diagnosis_esg():
    assert detect_wizard_intent("we need ESG reporting") == "diagnosis"

def test_detects_diagnosis_explicit():
    assert detect_wizard_intent("start diagnosis wizard") == "diagnosis"

# --- No match ---
def test_returns_none_for_normal_qa():
    assert detect_wizard_intent("What is idle capacity cost?") is None

def test_returns_none_for_chinese_qa():
    assert detect_wizard_intent("什麼是AVM模組二？") is None

def test_returns_none_for_empty():
    assert detect_wizard_intent("") is None
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_wizard_intent.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.wizard.intent'`

- [ ] **Step 3: Implement intent detection**

```python
# src/wizard/intent.py
import re


_SETUP_PATTERNS = [
    r"start.*setup.*wizard",
    r"setup.*wizard",
    r"start wizard",
    r"implement.*avm",
    r"avm.*implement",
    r"avm.*setup",
    r"開始.*設置",
    r"設置.*精靈",
    r"avm.*精靈",
]

_DIAGNOSIS_PATTERNS = [
    r"diagnos",
    r"losing money",
    r"lose money",
    r"margin.*shrink",
    r"shrink.*margin",
    r"capacity.*wast",
    r"wast.*capacity",
    r"esg.*report",
    r"start.*diagnosis",
    r"diagnosis.*wizard",
    r"虧損",
    r"診斷",
    r"產能.*浪費",
    r"毛利.*下降",
]


def detect_wizard_intent(text: str) -> str | None:
    """Return 'setup', 'diagnosis', or None based on message content."""
    if not text:
        return None
    lower = text.lower()
    for pattern in _SETUP_PATTERNS:
        if re.search(pattern, lower):
            return "setup"
    for pattern in _DIAGNOSIS_PATTERNS:
        if re.search(pattern, lower):
            return "diagnosis"
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_wizard_intent.py -v
```
Expected: 13 passed

- [ ] **Step 5: Commit**

```bash
git add src/wizard/intent.py tests/test_wizard_intent.py
git commit -m "feat: wizard intent detection for setup and diagnosis triggers"
```

---

## Task 3: Wizard Tools

**Files:**
- Create: `src/wizard/tools.py`
- Create: `tests/test_wizard_tools.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_wizard_tools.py
from unittest.mock import MagicMock
from src.wizard.state import WizardState
from src.wizard.tools import WIZARD_TOOLS, dispatch_wizard_tool


def test_tools_list_has_three_tools():
    names = [t["name"] for t in WIZARD_TOOLS]
    assert "search_avm_knowledge" in names
    assert "save_wizard_data" in names
    assert "complete_wizard" in names


def test_save_wizard_data_updates_state():
    state = WizardState(wizard_type="setup")
    retriever = MagicMock()
    result = dispatch_wizard_tool(
        "save_wizard_data",
        {"key": "expense_categories", "value": ["salaries", "rent"]},
        state,
        retriever,
    )
    assert state.collected_data["expense_categories"] == ["salaries", "rent"]
    assert state.current_step == 1
    assert "expense_categories" in result


def test_complete_wizard_marks_done():
    state = WizardState(wizard_type="diagnosis", current_step=3)
    retriever = MagicMock()
    dispatch_wizard_tool(
        "complete_wizard",
        {"summary": "Root cause: non-value-added activities in Module 3"},
        state,
        retriever,
    )
    assert state.is_complete is True


def test_search_calls_retriever():
    state = WizardState(wizard_type="setup")
    retriever = MagicMock(return_value=["chunk1", "chunk2"])
    result = dispatch_wizard_tool(
        "search_avm_knowledge",
        {"query": "idle capacity", "module_filter": 2},
        state,
        retriever,
    )
    retriever.assert_called_once_with("idle capacity", module_filter=2)
    assert "chunk1" in result


def test_search_returns_no_content_message_when_empty():
    state = WizardState(wizard_type="setup")
    retriever = MagicMock(return_value=[])
    result = dispatch_wizard_tool(
        "search_avm_knowledge",
        {"query": "something obscure"},
        state,
        retriever,
    )
    assert "No relevant" in result


def test_unknown_tool_returns_error():
    state = WizardState(wizard_type="setup")
    result = dispatch_wizard_tool("nonexistent_tool", {}, state, MagicMock())
    assert "Unknown" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_wizard_tools.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.wizard.tools'`

- [ ] **Step 3: Implement wizard tools**

```python
# src/wizard/tools.py
from typing import Callable
from src.wizard.state import WizardState

WIZARD_TOOLS = [
    {
        "name": "search_avm_knowledge",
        "description": (
            "Search the AVM knowledge base for context relevant to the current wizard step. "
            "Use this to retrieve module-specific content before asking the user a question, "
            "or to explain an AVM concept during the wizard. "
            "Optionally filter by module (1=Resource, 2=ActivityCenter, 3=Activity, 4=ValueObject)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query in the user's language."},
                "module_filter": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 4,
                    "description": "Optional AVM module to restrict the search.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "save_wizard_data",
        "description": (
            "Save a validated piece of information collected from the user. "
            "Call this ONLY when the user has provided a clear, complete answer to a wizard question. "
            "If the answer is vague or incomplete, ask for clarification first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": (
                        "Descriptive field name, e.g. 'module1_expense_categories', "
                        "'module2_executors', 'symptom', 'root_cause_hypothesis'."
                    ),
                },
                "value": {
                    "description": "The extracted, structured data from the user's answer."
                },
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "complete_wizard",
        "description": (
            "Call this when the wizard is fully done — all required information has been "
            "collected (Setup: all 4 modules; Diagnosis: symptom + follow-ups + diagnosis given). "
            "Provide a concise summary of everything collected or concluded."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Summary of all collected data or diagnosis conclusions.",
                }
            },
            "required": ["summary"],
        },
    },
]


def dispatch_wizard_tool(
    name: str,
    input_data: dict,
    state: WizardState,
    retriever: Callable,
) -> str:
    if name == "save_wizard_data":
        key = input_data["key"]
        value = input_data["value"]
        state.collected_data[key] = value
        state.current_step += 1
        return f"Saved '{key}' to wizard state (step {state.current_step})."

    if name == "complete_wizard":
        state.is_complete = True
        return f"Wizard marked complete. Summary: {input_data.get('summary', '')}"

    if name == "search_avm_knowledge":
        query = input_data["query"]
        module_filter = input_data.get("module_filter")
        chunks = retriever(query, module_filter=module_filter)
        if not chunks:
            return "No relevant AVM knowledge found for this query."
        return "\n\n---\n\n".join(chunks)

    return f"Unknown wizard tool: {name}"
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_wizard_tools.py -v
```
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/wizard/tools.py tests/test_wizard_tools.py
git commit -m "feat: wizard tool definitions and dispatch (save_wizard_data, complete_wizard, search)"
```

---

## Task 4: Wizard System Prompts

**Files:**
- Modify: `src/agent/prompt.py` (rename `_AVM_CORE_KNOWLEDGE` → `AVM_CORE_KNOWLEDGE`)
- Create: `src/wizard/prompts.py`
- Create: `tests/test_wizard_prompts.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_wizard_prompts.py
from src.wizard.state import WizardState
from src.wizard.prompts import build_setup_system_prompt, build_diagnosis_system_prompt


def test_setup_prompt_is_list_of_dicts():
    state = WizardState(wizard_type="setup")
    prompt = build_setup_system_prompt(state, "analyst")
    assert isinstance(prompt, list)
    assert all(isinstance(p, dict) for p in prompt)
    assert all("type" in p and "text" in p for p in prompt)


def test_setup_prompt_first_block_is_cached():
    state = WizardState(wizard_type="setup")
    prompt = build_setup_system_prompt(state, "analyst")
    assert prompt[0].get("cache_control") == {"type": "ephemeral"}


def test_setup_prompt_contains_module_phases():
    state = WizardState(wizard_type="setup")
    prompt = build_setup_system_prompt(state, "manager")
    full_text = " ".join(p["text"] for p in prompt)
    assert "Module 1" in full_text
    assert "Module 2" in full_text
    assert "Module 3" in full_text
    assert "Module 4" in full_text


def test_setup_prompt_includes_collected_data():
    state = WizardState(
        wizard_type="setup",
        current_step=1,
        collected_data={"module1_expense_categories": ["salaries", "rent"]},
    )
    prompt = build_setup_system_prompt(state, "analyst")
    full_text = " ".join(p["text"] for p in prompt)
    assert "module1_expense_categories" in full_text


def test_diagnosis_prompt_contains_symptom_map():
    state = WizardState(wizard_type="diagnosis")
    prompt = build_diagnosis_system_prompt(state, "executive")
    full_text = " ".join(p["text"] for p in prompt)
    assert "Module 4" in full_text
    assert "Module 3" in full_text
    assert "Module 2" in full_text
    assert "C-PVM" in full_text


def test_diagnosis_prompt_first_block_is_cached():
    state = WizardState(wizard_type="diagnosis")
    prompt = build_diagnosis_system_prompt(state, "analyst")
    assert prompt[0].get("cache_control") == {"type": "ephemeral"}
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_wizard_prompts.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.wizard.prompts'`

- [ ] **Step 3: Expose AVM_CORE_KNOWLEDGE in prompt.py**

In `src/agent/prompt.py`, rename `_AVM_CORE_KNOWLEDGE` to `AVM_CORE_KNOWLEDGE` (remove leading underscore) and update the reference inside `build_system_prompt`:

```python
# src/agent/prompt.py  — change line 1 and line 63
AVM_CORE_KNOWLEDGE = """   # <-- was _AVM_CORE_KNOWLEDGE
...
""".strip()

def build_system_prompt(role: str) -> list[dict]:
    return [
        {
            "type": "text",
            "text": AVM_CORE_KNOWLEDGE,   # <-- was _AVM_CORE_KNOWLEDGE
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": (
                f"The current user's role is: {role}. "
                "Apply the response calibration guidelines above with this role as the baseline default."
            ),
        },
    ]
```

- [ ] **Step 4: Implement wizard prompts**

```python
# src/wizard/prompts.py
import json
from src.wizard.state import WizardState
from src.agent.prompt import AVM_CORE_KNOWLEDGE

_SETUP_INSTRUCTIONS = """
## Current Mode: AVM Setup Wizard

You are guiding the user through implementing AVM across all 4 modules. Ask ONE focused question at a time. Validate each answer before saving it.

### Phase Progression
- **Phase 1 — Module 1 (Resource Module):** Collect the company's expense categories. Classify each as controllable (部門可自行管理) or uncontrollable (總部分攤). Save as `module1_expense_categories` and `module1_classification`.
- **Phase 2 — Module 2 (Activity Center Module):** Define activity executors (人員 or 機器). For each, collect normal capacity (標準時間, e.g., 480 minutes/day or hours/period). Calculate unit standard cost = resource cost ÷ normal capacity. Save as `module2_executors`.
- **Phase 3 — Module 3 (Activity Module):** Collect actual time spent per key activity. Tag each with one of the 5 attribute types: quality, capacity, value-added, customer service, ESG. Compare actual vs. normal capacity to reveal idle or over-utilized capacity. Save as `module3_activities`.
- **Phase 4 — Module 4 (Value Object Module):** Define value objects (products, customers, employee groups, ESG targets). Assign activity costs from Module 3 to each value object. Flag long-term vs. short-term value mismatches. Save as `module4_value_objects`.

### Rules
- Ask one question at a time. Do not list multiple questions at once.
- If the answer is vague or incomplete, ask for clarification before calling save_wizard_data.
- Use search_avm_knowledge() (with module_filter) when you need AVM context or the user asks a concept question.
- Call save_wizard_data(key, value) with a descriptive key for each validated answer.
- Call complete_wizard(summary) only after all 4 phases are complete.
- Respond in the same language as the user (Traditional Chinese or English).
""".strip()

_DIAGNOSIS_INSTRUCTIONS = """
## Current Mode: AVM Diagnosis Wizard

You are helping the user identify the root cause of their business problem using the AVM framework.

### Symptom → Module Mapping
- **Losing money / low profitability** → Module 4: check which value objects (customers/products) consume costs without generating adequate value. Investigate full-cost allocation including hidden costs (capital, risk, inventory holding).
- **Shrinking margins** → Module 3: identify non-value-added activities. What activities exist that add cost but no customer value?
- **Capacity feels wasted / underutilized** → Module 2 vs Module 3 delta: quantify idle capacity cost = (normal capacity − actual capacity) × unit standard cost.
- **Need ESG reporting** → Module 3 ESG-tagged activities + C-PVM: map carbon emissions to activity-level financial data.

### Diagnostic Flow
1. If no symptom is collected yet: ask the user to describe their business problem in their own words.
2. Map the symptom to the relevant AVM module(s).
3. Use search_avm_knowledge(module_filter=N) to retrieve relevant content for those modules.
4. Ask 3–5 targeted follow-up questions to gather enough detail for a diagnosis.
5. Call save_wizard_data() for each validated answer (keys: 'symptom', 'follow_up_1' … 'follow_up_5').
6. After the symptom + at least 2 follow-up answers are collected, call complete_wizard() with:
   - Ranked probable causes (most to least likely)
   - Specific recommended AVM actions for each cause
7. Respond in the same language as the user.
""".strip()


def build_setup_system_prompt(state: WizardState, role: str) -> list[dict]:
    collected_text = (
        json.dumps(state.collected_data, ensure_ascii=False, indent=2)
        if state.collected_data
        else "(nothing collected yet)"
    )
    return [
        {"type": "text", "text": AVM_CORE_KNOWLEDGE, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": _SETUP_INSTRUCTIONS},
        {
            "type": "text",
            "text": (
                f"User role: {role}.\n"
                f"Current wizard step: {state.current_step}.\n"
                f"Data collected so far:\n{collected_text}"
            ),
        },
    ]


def build_diagnosis_system_prompt(state: WizardState, role: str) -> list[dict]:
    collected_text = (
        json.dumps(state.collected_data, ensure_ascii=False, indent=2)
        if state.collected_data
        else "(nothing collected yet)"
    )
    return [
        {"type": "text", "text": AVM_CORE_KNOWLEDGE, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": _DIAGNOSIS_INSTRUCTIONS},
        {
            "type": "text",
            "text": (
                f"User role: {role}.\n"
                f"Current wizard step: {state.current_step}.\n"
                f"Data collected so far:\n{collected_text}"
            ),
        },
    ]
```

- [ ] **Step 5: Run tests to verify they pass**

```
pytest tests/test_wizard_prompts.py tests/test_agent_prompt.py -v
```

(If `test_agent_prompt.py` references `_AVM_CORE_KNOWLEDGE`, update that import too — replace `_AVM_CORE_KNOWLEDGE` with `AVM_CORE_KNOWLEDGE` in the test file.)

Expected: all pass

- [ ] **Step 6: Run full suite to confirm no regressions**

```
pytest tests/ -q
```
Expected: all existing tests still pass

- [ ] **Step 7: Commit**

```bash
git add src/agent/prompt.py src/wizard/prompts.py tests/test_wizard_prompts.py
git commit -m "feat: wizard system prompts for setup and diagnosis modes"
```

---

## Task 5: WizardEngine

**Files:**
- Create: `src/wizard/engine.py`
- Create: `tests/test_wizard_engine.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_wizard_engine.py
from unittest.mock import MagicMock, patch
from src.wizard.engine import WizardEngine
from src.wizard.state import WizardState


def _make_engine():
    return WizardEngine(
        api_key="test-key",
        pinecone_index=MagicMock(),
        embedder=MagicMock(),
    )


def test_start_setup_returns_state_and_intro():
    engine = _make_engine()
    state, intro = engine.start("setup")
    assert state.wizard_type == "setup"
    assert state.current_step == 0
    assert state.is_complete is False
    assert len(intro) > 50


def test_start_diagnosis_returns_state_and_intro():
    engine = _make_engine()
    state, intro = engine.start("diagnosis")
    assert state.wizard_type == "diagnosis"
    assert len(intro) > 20


def test_start_setup_chinese_returns_chinese_intro():
    engine = _make_engine()
    _, intro = engine.start("setup", language="zh-TW")
    # Should contain Chinese characters
    assert any('一' <= c <= '鿿' for c in intro)


def test_step_end_turn_returns_text():
    engine = _make_engine()
    state = WizardState(wizard_type="setup")

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Please list your expense categories."

    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [text_block]

    with patch.object(engine.client.messages, "create", return_value=mock_response):
        new_state, text = engine.step(state, [{"role": "user", "content": "hi"}], "analyst")

    assert text == "Please list your expense categories."
    assert new_state is state


def test_step_save_wizard_data_updates_state():
    engine = _make_engine()
    state = WizardState(wizard_type="setup")

    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "save_wizard_data"
    tool_block.input = {"key": "module1_expense_categories", "value": ["salaries", "rent"]}
    tool_block.id = "tu_1"

    response1 = MagicMock()
    response1.stop_reason = "tool_use"
    response1.content = [tool_block]

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Great. Now classify each as controllable or uncontrollable."

    response2 = MagicMock()
    response2.stop_reason = "end_turn"
    response2.content = [text_block]

    with patch.object(engine.client.messages, "create", side_effect=[response1, response2]):
        new_state, text = engine.step(
            state, [{"role": "user", "content": "salaries and rent"}], "analyst"
        )

    assert new_state.collected_data["module1_expense_categories"] == ["salaries", "rent"]
    assert new_state.current_step == 1
    assert "controllable" in text.lower()


def test_step_complete_wizard_marks_done():
    engine = _make_engine()
    state = WizardState(wizard_type="diagnosis", current_step=3,
                        collected_data={"symptom": "losing money"})

    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "complete_wizard"
    tool_block.input = {"summary": "Root cause: over-allocation of fixed costs to Product A"}
    tool_block.id = "tu_2"

    response1 = MagicMock()
    response1.stop_reason = "tool_use"
    response1.content = [tool_block]

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Based on our analysis, the primary root cause is..."

    response2 = MagicMock()
    response2.stop_reason = "end_turn"
    response2.content = [text_block]

    with patch.object(engine.client.messages, "create", side_effect=[response1, response2]):
        new_state, _ = engine.step(
            state, [{"role": "user", "content": "we serve 3 main customers"}], "manager"
        )

    assert new_state.is_complete is True
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_wizard_engine.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.wizard.engine'`

- [ ] **Step 3: Implement WizardEngine**

```python
# src/wizard/engine.py
import anthropic
from src.wizard.state import WizardState
from src.wizard.tools import WIZARD_TOOLS, dispatch_wizard_tool
from src.wizard.prompts import build_setup_system_prompt, build_diagnosis_system_prompt
from src.rag.retriever import retrieve_chunks

_SETUP_INTRO_EN = (
    "Welcome to the **AVM Setup Wizard**!\n\n"
    "I'll guide you through implementing Activity Value Management across all 4 modules:\n"
    "1. **Module 1 — Resource Module**: classify your expense categories\n"
    "2. **Module 2 — Activity Center Module**: define executors and standard capacity\n"
    "3. **Module 3 — Activity Module**: record actual activities and tag attributes\n"
    "4. **Module 4 — Value Object Module**: assign costs to products, customers, and more\n\n"
    "Let's start with **Module 1**. Please list your company's main expense categories "
    "(e.g., salaries, depreciation, utilities, rent, materials). Don't worry about being "
    "exhaustive — we'll refine as we go."
)

_SETUP_INTRO_ZH = (
    "歡迎使用 **AVM 設置精靈**！\n\n"
    "我將引導您完成作業價值管理的四個模組實施：\n"
    "1. **模組一 — 資源模組**：分類您的費用項目\n"
    "2. **模組二 — 作業中心模組**：定義執行者和標準產能\n"
    "3. **模組三 — 作業模組**：記錄實際作業並標記屬性\n"
    "4. **模組四 — 價值標的模組**：將成本分配給產品、客戶等\n\n"
    "我們從**模組一**開始。請列出貴公司的主要費用項目（例如：薪資、折舊、水電費、租金、材料費）。"
    "不必列舉完整，我們可以逐步補充。"
)

_DIAGNOSIS_INTRO_EN = (
    "Welcome to the **AVM Diagnosis Wizard**.\n\n"
    "Please describe the business problem you're experiencing. "
    "For example: declining profitability, shrinking margins, wasted capacity, or needing ESG reporting. "
    "The more specific you are, the better I can pinpoint the root cause."
)

_DIAGNOSIS_INTRO_ZH = (
    "歡迎使用 **AVM 診斷精靈**。\n\n"
    "請描述您目前遇到的業務問題，例如：利潤下降、毛利萎縮、產能浪費，或需要ESG報告。"
    "描述越具體，我越能準確找出根本原因。"
)


class WizardEngine:
    def __init__(self, api_key: str, pinecone_index, embedder):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.pinecone_index = pinecone_index
        self.embedder = embedder

    def start(self, wizard_type: str, language: str = "en") -> tuple[WizardState, str]:
        state = WizardState(wizard_type=wizard_type)
        is_zh = language == "zh-TW"
        if wizard_type == "setup":
            intro = _SETUP_INTRO_ZH if is_zh else _SETUP_INTRO_EN
        else:
            intro = _DIAGNOSIS_INTRO_ZH if is_zh else _DIAGNOSIS_INTRO_EN
        return state, intro

    def step(self, state: WizardState, history: list, role: str) -> tuple[WizardState, str]:
        if state.wizard_type == "setup":
            system = build_setup_system_prompt(state, role)
        else:
            system = build_diagnosis_system_prompt(state, role)

        messages = list(history)

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system,
                messages=messages,
                tools=WIZARD_TOOLS,
            )

            if response.stop_reason == "end_turn":
                text = next(
                    (b.text for b in response.content if b.type == "text"), ""
                )
                return state, text

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = dispatch_wizard_tool(
                            block.name,
                            block.input,
                            state,
                            self._retriever,
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

    def _retriever(self, query: str, module_filter=None) -> list[str]:
        return retrieve_chunks(
            self.pinecone_index,
            self.embedder,
            query,
            module_filter=module_filter,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_wizard_engine.py -v
```
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/wizard/engine.py tests/test_wizard_engine.py
git commit -m "feat: wizard engine with claude tool-use loop for setup and diagnosis"
```

---

## Task 6: app.py Integration

**Files:**
- Modify: `app.py`
- Create: `tests/test_app_routing.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_app_routing.py
from src.wizard.state import WizardState
from app import route_message


def test_routes_wizard_continue_when_active():
    state = WizardState(wizard_type="setup", current_step=1)
    route, payload = route_message("salaries and rent", state)
    assert route == "wizard_continue"
    assert payload is state


def test_routes_wizard_start_on_setup_intent():
    route, payload = route_message("I want to start the AVM setup wizard", None)
    assert route == "wizard_start"
    assert payload == "setup"


def test_routes_wizard_start_on_diagnosis_intent():
    route, payload = route_message("we're losing money, help diagnose", None)
    assert route == "wizard_start"
    assert payload == "diagnosis"


def test_routes_qa_for_normal_message():
    route, payload = route_message("What is idle capacity cost?", None)
    assert route == "qa"
    assert payload is None


def test_completed_wizard_routes_to_qa():
    state = WizardState(wizard_type="setup", is_complete=True)
    route, payload = route_message("What is idle capacity cost?", state)
    assert route == "qa"
    assert payload is None


def test_completed_wizard_can_start_new_wizard():
    state = WizardState(wizard_type="setup", is_complete=True)
    route, payload = route_message("start diagnosis wizard", state)
    assert route == "wizard_start"
    assert payload == "diagnosis"
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_app_routing.py -v
```
Expected: `ImportError: cannot import name 'route_message' from 'app'`

- [ ] **Step 3: Update app.py**

Replace the entire `app.py` with the following (preserves all existing functionality, adds wizard routing):

```python
# app.py
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from typing import Optional
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


def route_message(
    message_text: str,
    wizard_state: Optional[WizardState],
) -> tuple[str, object]:
    """
    Returns ('wizard_continue', state) | ('wizard_start', wizard_type) | ('qa', None).
    Pure function — no side effects — so it can be unit-tested without Chainlit.
    """
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


@cl.on_message
async def on_message(message: cl.Message):
    role: str = cl.user_session.get("role", "analyst")
    history: list = cl.user_session.get("history", [])
    wizard_state: Optional[WizardState] = cl.user_session.get("wizard_state")

    history.append({"role": "user", "content": message.content})

    response_msg = cl.Message(content="Thinking...")
    await response_msg.send()

    route, payload = route_message(message.content, wizard_state)

    if route == "wizard_continue":
        new_state, response_text = _wizard_engine.step(payload, history, role)
        if new_state.is_complete:
            cl.user_session.set("wizard_state", None)
            response_text += "\n\n---\n*Wizard complete — returning to normal chat mode.*"
        else:
            cl.user_session.set("wizard_state", new_state)

    elif route == "wizard_start":
        lang = _detect_language(message.content)
        new_state, response_text = _wizard_engine.start(payload, language=lang)
        cl.user_session.set("wizard_state", new_state)

    else:
        response_text = _agent.get_response(history=history, role=role)

    response_msg.content = response_text
    await response_msg.update()

    history.append({"role": "assistant", "content": response_text})
    cl.user_session.set("history", history)
```

- [ ] **Step 4: Run the routing tests to verify they pass**

```
pytest tests/test_app_routing.py -v
```
Expected: 6 passed

- [ ] **Step 5: Run the full test suite**

```
pytest tests/ -q
```
Expected: all tests pass (39 existing + new wizard + routing tests)

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_app_routing.py
git commit -m "feat: wizard routing in app.py — setup and diagnosis wizard modes"
```

---

## Verification

After all tasks are complete, verify the full flow manually:

**Setup Wizard (English):**
1. Log in as `alice` / `password123`
2. Type: `I want to start the AVM setup wizard`
3. Expected: Setup wizard intro appears, asks about expense categories
4. Answer: `Our main expenses are salaries, depreciation, and utilities`
5. Expected: Claude validates and asks to classify as controllable/uncontrollable

**Diagnosis Wizard (Chinese):**
1. Type: `我們公司最近在虧損`
2. Expected: Diagnosis wizard intro in Chinese, asks to describe the problem
3. Answer: `我們的大客戶佔了大量成本，但利潤很低`
4. Expected: Claude maps to Module 4, asks follow-up about cost allocation

**Wizard completion:**
- After the diagnosis concludes, type: `What is AVM?`
- Expected: Returns to normal Q&A mode (wizard state cleared)

**Run final test suite:**
```
pytest tests/ -v
```
Expected: all tests pass
