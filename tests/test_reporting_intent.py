from src.reporting.intent import detect_report_intent


def test_detect_profitability_english():
    assert detect_report_intent("generate a profitability report") == "profitability"


def test_detect_profitability_chinese():
    assert detect_report_intent("幫我做獲利分析") == "profitability"


def test_detect_capacity_english():
    assert detect_report_intent("show me the capacity analysis") == "capacity"


def test_detect_capacity_chinese():
    assert detect_report_intent("我想看閒置產能報告") == "capacity"


def test_detect_attribute_english():
    assert detect_report_intent("create an activity attribute dashboard") == "attribute"


def test_detect_attribute_chinese():
    assert detect_report_intent("請做作業屬性分析") == "attribute"


def test_detect_value_object_english():
    assert detect_report_intent("generate a value object report") == "value_object"


def test_detect_value_object_chinese():
    assert detect_report_intent("分析長期價值") == "value_object"


def test_no_match_returns_none():
    assert detect_report_intent("what is AVM?") is None
    assert detect_report_intent("help me with module 2") is None


def test_case_insensitive():
    assert detect_report_intent("Profitability Report please") == "profitability"
    assert detect_report_intent("CAPACITY ANALYSIS") == "capacity"
