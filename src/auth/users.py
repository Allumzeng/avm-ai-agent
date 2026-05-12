import hashlib
import json
import os
from pathlib import Path
from typing import Optional

_USERS_FILE = Path(__file__).parent.parent.parent / "users.json"


def _hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260000)
    return dk.hex()


def _load_users() -> dict:
    if not _USERS_FILE.exists():
        return {}
    with open(_USERS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_users(users: dict) -> None:
    with open(_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def authenticate(username: str, password: str) -> Optional[dict]:
    users = _load_users()
    user = users.get(username)
    if user and user["password_hash"] == _hash_password(password, user["salt_hex"]):
        return {"username": username, "role": user["role"], "group": user["group"]}
    return None


def add_user(username: str, password: str, role: str, group: str) -> None:
    users = _load_users()
    salt_hex = os.urandom(16).hex()
    users[username] = {
        "password_hash": _hash_password(password, salt_hex),
        "salt_hex": salt_hex,
        "role": role,
        "group": group,
    }
    _save_users(users)


def remove_user(username: str) -> bool:
    users = _load_users()
    if username not in users:
        return False
    del users[username]
    _save_users(users)
    return True


def get_role(username: str) -> Optional[str]:
    users = _load_users()
    user = users.get(username)
    return user["role"] if user else None


def list_users() -> list[dict]:
    users = _load_users()
    return [
        {"username": k, "role": v["role"], "group": v["group"]}
        for k, v in users.items()
    ]
