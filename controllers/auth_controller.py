from db import SessionLocal
from models import User
from security import verify_password, create_access_token, save_session_token, clear_session_token


def login_user(identifier: str, password: str) -> tuple[bool, str]:
    """
    Authenticates a user via email or employee number and password.
    Saves JWT session token on success.
    Returns (success: bool, message: str).
    """
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter((User.email == identifier) | (User.employee_number == identifier))
            .first()
        )
        if not user:
            return False, "Identifiant (email ou numéro d'employé) introuvable."

        if not verify_password(password, user.password_hash):
            return False, "Mot de passe incorrect."

        token = create_access_token(
            user_id=user.id,
            employee_number=user.employee_number,
            role_name=user.role.name if user.role else "UNKNOWN",
        )
        save_session_token(token)
        return True, f"Bienvenue {user.full_name} ({user.role.name}) !"
    except Exception as e:
        return False, f"Erreur lors de l'authentification : {e}"
    finally:
        db.close()


def logout_user() -> bool:
    """Logs out current user by clearing local session token."""
    clear_session_token()
    return True
