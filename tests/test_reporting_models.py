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
