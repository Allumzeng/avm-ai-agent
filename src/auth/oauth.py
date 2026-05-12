"""Domain-based whitelist for Google OAuth login."""
from typing import Optional

_DOMAIN_RULES: dict[str, dict[str, str]] = {
    "linexsolutions.com": {"role": "manager", "group": "dpd_taiwan"},
    "g.nccu.edu.tw":      {"role": "analyst", "group": "nccu_students"},
}


def resolve_oauth_user(email: str) -> Optional[dict]:
    if not email or "@" not in email:
        return None
    domain = email.rsplit("@", 1)[1].lower()
    return _DOMAIN_RULES.get(domain)
