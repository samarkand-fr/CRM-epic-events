from db import SessionLocal
from models import User, Role
from security import hash_password
from permissions import check_permission
from logger import log_event


def get_all_users() -> list[User]:
    """Retrieves all users with their associated role."""
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id.asc()).all()
        return users
    finally:
        db.close()


def create_user(
    employee_number: str,
    full_name: str,
    email: str,
    password: str,
    role_name: str,
    current_user: User,
) -> tuple[bool, str]:
    """
    Creates a new user account.
    Restricted to GESTION department.
    Logs audit event to Sentry.io.
    """
    allowed, msg = check_permission(current_user, ["GESTION"])
    if not allowed:
        return False, msg

    if not employee_number or not full_name or not email or not password or not role_name:
        return False, "Tous les champs (numéro d'employé, nom, email, mot de passe, rôle) sont obligatoires."

    db = SessionLocal()
    try:
        existing_emp = db.query(User).filter(User.employee_number == employee_number).first()
        if existing_emp:
            return False, f"Le numéro d'employé '{employee_number}' existe déjà."

        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            return False, f"L'email '{email}' est déjà utilisé par un autre collaborateur."

        role = db.query(Role).filter(Role.name == role_name.upper()).first()
        if not role:
            return False, f"Rôle invalide. Rôles disponibles : COMMERCIAL, SUPPORT, GESTION."

        new_user = User(
            employee_number=employee_number,
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role_id=role.id,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Audit Event Logging to Sentry
        log_event(
            message=f"Collaborateur créé : {new_user.full_name} ({new_user.employee_number}) - Rôle : {role.name}",
            level="info",
            extra={
                "created_user_id": new_user.id,
                "created_user_emp_num": new_user.employee_number,
                "role": role.name,
                "author_emp_num": current_user.employee_number,
            },
        )

        return True, f"Collaborateur {new_user.full_name} ({new_user.employee_number}) créé avec succès avec le rôle {role.name}."
    except Exception as e:
        db.rollback()
        return False, f"Erreur lors de la création du collaborateur : {e}"
    finally:
        db.close()


def update_user(
    user_id: int,
    full_name: str | None = None,
    email: str | None = None,
    password: str | None = None,
    role_name: str | None = None,
    current_user: User = None,
) -> tuple[bool, str]:
    """
    Updates an existing user account.
    Restricted to GESTION department.
    Logs audit event to Sentry.io.
    """
    allowed, msg = check_permission(current_user, ["GESTION"])
    if not allowed:
        return False, msg

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, f"Collaborateur ID #{user_id} introuvable."

        changes = []
        if full_name:
            user.full_name = full_name
            changes.append("nom")
        if email and email != user.email:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                return False, f"L'email '{email}' est déjà utilisé."
            user.email = email
            changes.append("email")
        if password:
            user.password_hash = hash_password(password)
            changes.append("mot de passe")
        if role_name:
            role = db.query(Role).filter(Role.name == role_name.upper()).first()
            if not role:
                return False, f"Rôle invalide. Rôles disponibles : COMMERCIAL, SUPPORT, GESTION."
            user.role_id = role.id
            changes.append("rôle")

        db.commit()
        db.refresh(user)

        # Audit Event Logging to Sentry
        log_event(
            message=f"Collaborateur modifié : {user.full_name} ({user.employee_number}) - Modifs : {', '.join(changes)}",
            level="info",
            extra={
                "updated_user_id": user.id,
                "updated_user_emp_num": user.employee_number,
                "modifications": changes,
                "author_emp_num": current_user.employee_number,
            },
        )

        return True, f"Collaborateur ID #{user.id} ({user.full_name}) mis à jour avec succès."
    except Exception as e:
        db.rollback()
        return False, f"Erreur lors de la mise à jour : {e}"
    finally:
        db.close()
