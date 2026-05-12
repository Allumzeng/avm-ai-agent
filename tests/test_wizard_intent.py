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

def test_esg_question_does_not_trigger_wizard():
    assert detect_wizard_intent("What is ESG reporting in AVM?") is None

def test_diagnosis_noun_does_not_trigger_wizard():
    assert detect_wizard_intent("What does AVM diagnosis mean?") is None
