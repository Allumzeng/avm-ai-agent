_INTENT_PATTERNS: dict[str, list[str]] = {
    "profitability": [
        "profitability report",
        "profit report",
        "profitability analysis",
        "customer profitability",
        "product profitability",
        "獲利分析",
        "利潤報告",
        "盈利報告",
        "顧客獲利",
        "產品獲利",
        "獲利報告",
    ],
    "capacity": [
        "capacity report",
        "capacity analysis",
        "idle capacity",
        "capacity utilization",
        "activity center report",
        "產能分析",
        "產能報告",
        "閒置產能",
        "作業中心報告",
        "產能利用",
    ],
    "attribute": [
        "attribute report",
        "attribute dashboard",
        "activity attribute",
        "value-added analysis",
        "non-value-added",
        "屬性報告",
        "作業屬性",
        "附加價值分析",
        "無附加價值",
        "屬性分析",
    ],
    "value_object": [
        "value object report",
        "value object analysis",
        "long-term value",
        "customer value report",
        "product value report",
        "價值標的報告",
        "長期價值",
        "顧客價值",
        "產品價值",
        "價值標的分析",
    ],
}


def detect_report_intent(text: str) -> str | None:
    """Return report type string if text contains a report generation request, else None."""
    lower = text.lower()
    for report_type, patterns in _INTENT_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in lower:
                return report_type
    return None
