"""
Unit tests for permissions and RBAC module (permissions.py).
"""

from models import User, Role
from permissions import has_role, check_permission


def test_has_role():
    role_gestion = Role(id=1, name="GESTION")
    user = User(id=1, full_name="Admin", role=role_gestion)

    assert has_role(user, "GESTION") is True
    assert has_role(user, "COMMERCIAL", "GESTION") is True
    assert has_role(user, "SUPPORT") is False


def test_check_permission_allowed():
    role_commercial = Role(id=1, name="COMMERCIAL")
    user = User(id=1, full_name="Bill", employee_number="EMP001", role=role_commercial)

    allowed, msg = check_permission(user, ["COMMERCIAL"])
    assert allowed is True
    assert msg == ""


def test_check_permission_denied():
    role_commercial = Role(id=1, name="COMMERCIAL")
    user = User(id=1, full_name="Bill", employee_number="EMP001", role=role_commercial)

    allowed, msg = check_permission(user, ["GESTION"])
    assert allowed is False
    assert "Permission denied" in msg
