from functools import wraps
import click
from db import SessionLocal
from models import User
from security import get_session_token, decode_access_token


def get_current_user(db_session=None) -> tuple[User | None, str | None]:
    """
    Retrieves the currently authenticated user from persistent JWT token session.
    Returns (User, None) on success.
    Returns (None, "TOKEN_EXPIRED") if token has expired.
    Returns (None, "NO_TOKEN") if no token is present.
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
    """Checks if the user has one of the specified role names."""
    if not user or not user.role:
        return False
    return user.role.name.upper() in [r.upper() for r in role_names]


def check_permission(user: User, allowed_roles: list[str]) -> tuple[bool, str]:
    """
    Authorization check function.
    Returns (has_permission: bool, error_message: str).
    """
    if not user:
        return False, "Aucun utilisateur connecté."
    if not has_role(user, *allowed_roles):
        allowed_str = ", ".join(allowed_roles)
        return False, f"Permission refusée. Rôle requis : [{allowed_str}]. Rôle actuel : [{user.role.name}]."
    return True, ""


def require_login(f):
    """Decorator requiring an authenticated user for CLI commands."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user, err_code = get_current_user()
        if err_code == "TOKEN_EXPIRED":
            click.echo(click.style("⏰ Votre session a expiré. Veuillez vous réauthentifier avec 'python epicevents.py login'.", fg="yellow"))
            raise click.Abort()
        if not user:
            click.echo(click.style("❌ Vous devez être connecté pour exécuter cette commande. Utiliser 'python epicevents.py login'.", fg="red"))
            raise click.Abort()
        return f(*args, **kwargs)
    return decorated_function


def require_role(*role_names: str):
    """Decorator requiring a user to have one of the given roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user, err_code = get_current_user()
            if err_code == "TOKEN_EXPIRED":
                click.echo(click.style("⏰ Votre session a expiré. Veuillez vous réauthentifier avec 'python epicevents.py login'.", fg="yellow"))
                raise click.Abort()
            if not user:
                click.echo(click.style("❌ Vous devez être connecté pour exécuter cette commande.", fg="red"))
                raise click.Abort()
            
            allowed, msg = check_permission(user, list(role_names))
            if not allowed:
                click.echo(click.style(f"⛔ {msg}", fg="red"))
                raise click.Abort()
            return f(*args, **kwargs)
        return decorated_function
    return decorator
