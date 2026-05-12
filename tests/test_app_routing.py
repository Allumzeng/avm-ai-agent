# tests/test_app_routing.py
from typing import Optional
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
    source_data = {"file_name": "new.xlsx", "sheets": {}}
    old_report = ReportState(report_type="capacity", source_data={}, is_complete=True)
    route, payload = route_message("generate capacity report", None, source_data, old_report)
    assert route == "report_generate"
    assert payload == "capacity"
