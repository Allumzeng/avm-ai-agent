from src.auth.users import authenticate, get_role

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
