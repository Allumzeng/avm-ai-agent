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
