import hashlib
import os
from typing import Optional

def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260000)
    return dk.hex()

def _make_user(password: str, role: str, group: str) -> dict:
    salt = os.urandom(16)
    return {
        "password_hash": _hash_password(password, salt),
        "salt": salt,
        "role": role,
        "group": group,
    }

USERS: dict[str, dict] = {
    "alice": _make_user("password123", role="manager", group="dpd_taiwan"),
    "student_chen": _make_user("nccu2026", role="analyst", group="nccu_students"),
}

def authenticate(username: str, password: str) -> Optional[dict]:
    user = USERS.get(username)
    if user and user["password_hash"] == _hash_password(password, user["salt"]):
        return {"username": username, "role": user["role"], "group": user["group"]}
    return None

def get_role(username: str) -> Optional[str]:
    user = USERS.get(username)
    return user["role"] if user else None
