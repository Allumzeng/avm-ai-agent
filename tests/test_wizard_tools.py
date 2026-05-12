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
