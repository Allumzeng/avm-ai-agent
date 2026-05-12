import re


_SETUP_PATTERNS = [
    r"start.*setup.*wizard",
    r"setup.*wizard",
    r"start wizard",
    r"implement.*avm",
    r"avm.*implement",
    r"avm.*setup",
    r"開始.*設置",
    r"設置.*精靈",
    r"avm.*精靈",
]

_DIAGNOSIS_PATTERNS = [
    r"losing money",
    r"lose money",
    r"margin.*shrink",
    r"shrink.*margin",
    r"capacity.*wast",
    r"wast.*capacity",
    r"need.*esg",
    r"start.*diagnosis",
    r"diagnosis.*wizard",
    r"虧損",
    r"診斷",
    r"產能.*浪費",
    r"毛利.*下降",
]


def detect_wizard_intent(text: str) -> str | None:
    """Return 'setup', 'diagnosis', or None based on message content."""
    if not text:
        return None
    lower = text.lower()
    for pattern in _SETUP_PATTERNS:
        if re.search(pattern, lower):
            return "setup"
    for pattern in _DIAGNOSIS_PATTERNS:
        if re.search(pattern, lower):
            return "diagnosis"
    return None
