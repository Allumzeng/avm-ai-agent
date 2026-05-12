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


def test_active_wizard_takes_priority_over_intent():
    # Even if the message matches a wizard-start intent pattern,
    # an active (incomplete) wizard should still route to wizard_continue.
    state = WizardState(wizard_type="setup", current_step=2)
    route, payload = route_message("I want to start the AVM setup wizard", state)
    assert route == "wizard_continue"
    assert payload is state
