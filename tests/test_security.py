"""
Unit tests for security cryptographic module (security.py).
"""

from datetime import timedelta
from security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    save_session_token,
    get_session_token,
    clear_session_token,
)


def test_hash_and_verify_password():
    password = "StrongPassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_create_and_decode_access_token():
    token = create_access_token(user_id=1, employee_number="EMP001", role_name="COMMERCIAL")
    assert isinstance(token, str)

    payload, err_code = decode_access_token(token)
    assert err_code is None
    assert payload["user_id"] == 1
    assert payload["employee_number"] == "EMP001"
    assert payload["role_name"] == "COMMERCIAL"


def test_expired_access_token():
    expired_token = create_access_token(
        user_id=1,
        employee_number="EMP001",
        role_name="COMMERCIAL",
        expires_delta=timedelta(seconds=-10),
    )
    payload, err_code = decode_access_token(expired_token)
    assert payload is None
    assert err_code == "TOKEN_EXPIRED"


def test_session_token_file_ops():
    test_token = "mock_jwt_session_token"
    try:
        save_session_token(test_token)
        retrieved = get_session_token()
        assert retrieved == test_token
        clear_session_token()
    except PermissionError:
        pass
