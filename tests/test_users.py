import json
import pytest
import src.auth.users as users_module
from src.auth.users import authenticate, get_role, add_user, remove_user, list_users


@pytest.fixture(autouse=True)
def isolated_users_file(tmp_path, monkeypatch):
    """Redirect _USERS_FILE to a temp path and seed with known users."""
    tmp_file = tmp_path / "users.json"
    monkeypatch.setattr(users_module, "_USERS_FILE", tmp_file)
    # Seed two known users
    add_user("alice", "password123", "manager", "dpd_taiwan")
    add_user("student_chen", "nccu2026", "analyst", "nccu_students")
    yield tmp_file


def test_valid_dpd_user_authenticates():
    user = authenticate("alice", "password123")
    assert user is not None
    assert user["username"] == "alice"


def test_invalid_password_returns_none():
    user = authenticate("alice", "wrongpassword")
    assert user is None


def test_unknown_user_returns_none():
    user = authenticate("nobody", "password")
    assert user is None


def test_dpd_user_has_manager_role():
    assert get_role("alice") == "manager"


def test_nccu_user_has_analyst_role():
    assert get_role("student_chen") == "analyst"


def test_get_role_unknown_user_returns_none():
    assert get_role("nonexistent_user") is None


def test_add_user_persists():
    add_user("new_user", "pass456", "executive", "dpd_taiwan")
    result = authenticate("new_user", "pass456")
    assert result is not None
    assert result["role"] == "executive"


def test_remove_user():
    assert remove_user("alice") is True
    assert authenticate("alice", "password123") is None


def test_remove_nonexistent_user_returns_false():
    assert remove_user("ghost") is False


def test_list_users_returns_all():
    users = list_users()
    usernames = [u["username"] for u in users]
    assert "alice" in usernames
    assert "student_chen" in usernames


def test_passwords_survive_reload(tmp_path, monkeypatch):
    """Hash+salt stored on disk must verify correctly after re-reading the file."""
    tmp_file = tmp_path / "reload_test.json"
    monkeypatch.setattr(users_module, "_USERS_FILE", tmp_file)
    add_user("reload_user", "mypassword", "analyst", "nccu_students")
    # Simulate server restart: reload from file
    result = authenticate("reload_user", "mypassword")
    assert result is not None
    assert result["role"] == "analyst"
