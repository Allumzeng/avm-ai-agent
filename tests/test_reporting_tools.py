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
