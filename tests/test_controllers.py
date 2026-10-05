"""
Unit tests for domain controllers and authentication logic.
"""

from controllers.auth_controller import login_user
from controllers.user_controller import get_all_users
from controllers.client_controller import get_all_clients
from controllers.contract_controller import get_all_contracts
from controllers.event_controller import get_all_events


def test_login_user_invalid_identifier():
    success, msg = login_user("nonexistent_user@domain.com", "Password123!")
    assert success is False
    assert "not found" in msg


def test_login_user_invalid_password():
    success, msg = login_user("EMP001", "InvalidPassword!")
    assert success is False
    assert "Incorrect password" in msg


def test_get_all_users():
    users = get_all_users()
    assert isinstance(users, list)
    assert len(users) > 0


def test_get_all_clients():
    clients = get_all_clients()
    assert isinstance(clients, list)


def test_get_all_contracts():
    contracts = get_all_contracts()
    assert isinstance(contracts, list)


def test_get_all_events():
    events = get_all_events()
    assert isinstance(events, list)
