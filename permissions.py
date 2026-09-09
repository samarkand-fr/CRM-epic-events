from functools import wraps
import click
from db import SessionLocal
from models import User
from security import get_session_token, decode_access_token


def get_current_user(db_session=None) -> User | None:
    """Retrieves the currently authenticated user from local token session."""
    token = get_session_token()
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    close_session = False
    if db_session is None:
        db_session = SessionLocal()
        close_session = True

    try:
        user = db_session.query(User).filter(User.id == user_id).first()
        return user
    finally:
        if close_session:
            db_session.close()


def has_role(user: User, *role_names: str) -> bool:
    """Checks if the user has one of the specified role names."""
    if not user or not user.role:
        return False
    return user.role.name.upper() in [r.upper() for r in role_names]


def require_login(f):
    """Decorator requiring an authenticated user for CLI commands."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            click.echo(click.style("❌ Erreur : Vous devez être connecté pour exécuter cette commande. Utiliser 'python cli.py login'.", fg="red"))
            raise click.Abort()
        return f(*args, **kwargs)
    return decorated_function


def require_role(*role_names: str):
    """Decorator requiring a user to have one of the given roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                click.echo(click.style("❌ Erreur : Vous devez être connecté pour exécuter cette commande.", fg="red"))
                raise click.Abort()
            if not has_role(user, *role_names):
                allowed = ", ".join(role_names)
                click.echo(click.style(f"⛔ Accès refusé : Rôle insuffisant. Rôles autorisés : {allowed}. Votre rôle : {user.role.name}", fg="red"))
                raise click.Abort()
            return f(*args, **kwargs)
        return decorated_function
    return decorator
