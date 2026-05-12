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
