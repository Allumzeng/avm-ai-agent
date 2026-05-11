import hashlib
from typing import Optional

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

USERS: dict[str, dict] = {
    "alice": {
        "password_hash": _hash("password123"),
        "role": "manager",
        "group": "dpd_taiwan",
    },
    "student_chen": {
        "password_hash": _hash("nccu2026"),
        "role": "analyst",
        "group": "nccu_students",
    },
}

def authenticate(username: str, password: str) -> Optional[dict]:
    user = USERS.get(username)
    if user and user["password_hash"] == _hash(password):
        return {"username": username, "role": user["role"], "group": user["group"]}
    return None

def get_role(username: str) -> Optional[str]:
    user = USERS.get(username)
    return user["role"] if user else None
