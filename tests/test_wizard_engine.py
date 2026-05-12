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


def test_step_raises_on_unexpected_stop_reason():
    import pytest
    engine = _make_engine()
    state = WizardState(wizard_type="setup")

    mock_response = MagicMock()
    mock_response.stop_reason = "max_tokens"
    mock_response.content = []

    with patch.object(engine.client.messages, "create", return_value=mock_response):
        with pytest.raises(RuntimeError, match="max_tokens"):
            engine.step(state, [{"role": "user", "content": "hi"}], "analyst")
