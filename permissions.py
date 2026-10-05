"""
Role-Based Access Control and Permission Module (permissions.py).

This module provides Role-Based Access Control (RBAC) security mechanisms:
1. Extracting and validating the logged-in User from persistent JWT session tokens.
2. Checking role authorizations (GESTION, COMMERCIAL, SUPPORT).
3. Enforcing CLI access controls via @require_login and @require_role(*roles) decorators.
"""

from functools import wraps
import click
from db import SessionLocal
from models import User
from security import get_session_token, decode_access_token


from logger import log_event


def get_current_user(db_session=None) -> tuple[User | None, str | None]:
    """
    Retrieves the currently authenticated user from local persistent JWT session token.

    Args:
        db_session: Optional SQLAlchemy database session.

    Returns:
        tuple[User | None, str | None]: (User object, ErrorCode string).
        - (User, None) if session token is valid.
        - (None, "TOKEN_EXPIRED") if JWT has expired.
        - (None, "NO_TOKEN") if no session token file is present.
    """
    token = get_session_token()
    if not token:
        return None, "NO_TOKEN"

    payload, err_code = decode_access_token(token)
    if err_code == "TOKEN_EXPIRED":
        return None, "TOKEN_EXPIRED"
    if not payload:
        return None, "TOKEN_INVALID"

    user_id = payload.get("user_id")
    if not user_id:
        return None, "TOKEN_INVALID"

    close_session = False
    if db_session is None:
        db_session = SessionLocal()
        close_session = True

    try:
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return None, "USER_NOT_FOUND"
        return user, None
    finally:
        if close_session:
            db_session.close()


def has_role(user: User, *role_names: str) -> bool:
    """
    Checks if user belongs to any of the specified department role names.

    Args:
        user (User): Authenticated user instance.
        *role_names (str): Allowed role names (e.g. 'COMMERCIAL', 'SUPPORT', 'GESTION').

    Returns:
        bool: True if user holds one of the specified roles, False otherwise.
    """
    if not user or not user.role:
        return False
    return user.role.name.upper() in [r.upper() for r in role_names]


def check_permission(user: User, allowed_roles: list[str]) -> tuple[bool, str]:
    """
    Validates user permissions before executing controller domain logic.

    Args:
        user (User): User attempting action.
        allowed_roles (list[str]): Authorized department role names.

    Returns:
        tuple[bool, str]: (is_allowed: bool, error_message: str).
    """
    if not user:
        return False, "No authenticated user session found."
    if not has_role(user, *allowed_roles):
        allowed_str = ", ".join(allowed_roles)
        user_role_str = user.role.name if user.role else "NO_ROLE"
        msg = f"Permission denied. Required role: [{allowed_str}]. Your role: [{user_role_str}]."
        log_event(
            message=f"Security Alert: {msg}",
            level="warning",
            extra={
                "user_id": user.id,
                "user_email": user.email,
                "employee_number": user.employee_number,
                "user_role": user_role_str,
                "required_roles": allowed_roles,
                "event_type": "access_denied",
            },
        )
        return False, msg
    return True, ""


def require_login(f):
    """
    CLI decorator enforcing an active user login session before executing a Click command.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user, err_code = get_current_user()
        if err_code == "TOKEN_EXPIRED":
            click.echo(click.style("⏰ Your session has expired. Please log in again using 'python epicevents.py login'.", fg="yellow"))
            raise click.Abort()
        if not user:
            click.echo(click.style("❌ Authentication required to execute this command. Use 'python epicevents.py login'.", fg="red"))
            raise click.Abort()
        return f(*args, **kwargs)
    return decorated_function


def require_role(*role_names: str):
    """
    CLI decorator restricting Click command execution to specific department roles.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user, err_code = get_current_user()
            if err_code == "TOKEN_EXPIRED":
                click.echo(click.style("⏰ Your session has expired. Please log in again using 'python epicevents.py login'.", fg="yellow"))
                raise click.Abort()
            if not user:
                click.echo(click.style("❌ Authentication required to execute this command.", fg="red"))
                raise click.Abort()
            
            allowed, msg = check_permission(user, list(role_names))
            if not allowed:
                click.echo(click.style(f"⛔ {msg}", fg="red"))
                raise click.Abort()
            return f(*args, **kwargs)
        return decorated_function
    return decorator

