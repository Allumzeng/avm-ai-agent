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
    """Build mock Claude response sequence: one tool_use response then end_turn."""
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


def test_generate_uses_opus_model():
    """Verify the engine calls claude-opus-4-7, not sonnet."""
    engine = _make_engine()
    responses = _mock_tool_use_then_end_turn([
        ("generate_report", {"report_text": "Report"}),
    ])
    calls = []

    def capture_create(**kwargs):
        calls.append(kwargs)
        idx = len(calls) - 1
        return responses[idx]

    with patch.object(engine.client.messages, "create", side_effect=capture_create):
        engine.generate("profitability", _make_source_data(), "analyst")

    assert calls[0]["model"] == "claude-opus-4-7"
