"""
User and Collaborator Management Controller (controllers/user_controller.py).

This module handles CRUD domain operations for employee accounts:
1. Listing all collaborators (authenticated users).
2. Creating new collaborator accounts (Restricted to GESTION department, logs Sentry event).
3. Updating existing collaborator details and roles (Restricted to GESTION department, logs Sentry event).
"""

from db import SessionLocal
from models import User, Role
from security import hash_password
from permissions import check_permission
from logger import log_event


def get_all_users() -> list[User]:
    """
    Retrieves all employee users ordered by ID ascending.

    Returns:
        list[User]: List of User ORM entities with pre-joined Role objects.
    """
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
    Creates a new collaborator account.

    Step 1: Check permissions (Restricted to GESTION team).
    Step 2: Validate required fields and uniqueness of employee_number and email.
    Step 3: Hash password securely using Argon2.
    Step 4: Commit new User record to database.
    Step 5: Emit audit event logging payload to Sentry.io.

    Args:
        employee_number (str): Unique business employee code (e.g. EMP004).
        full_name (str): Employee full name.
        email (str): Employee professional email.
        password (str): Initial cleartext password.
        role_name (str): Target department role (COMMERCIAL, SUPPORT, GESTION).
        current_user (User): Authenticated active user session.

    Returns:
        tuple[bool, str]: (success: bool, message: str).
    """
    # Step 1: RBAC Permission Verification
    allowed, msg = check_permission(current_user, ["GESTION"])
    if not allowed:
        return False, msg

    # Step 2: Validate Input Fields
    if not employee_number or not full_name or not email or not password or not role_name:
        return False, "All fields (employee number, full name, email, password, role) are required."

    db = SessionLocal()
    try:
        # Validate unique employee number
        existing_emp = db.query(User).filter(User.employee_number == employee_number).first()
        if existing_emp:
            return False, f"Employee number '{employee_number}' already exists."

        # Validate unique email
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            return False, f"Email '{email}' is already registered to another employee."

        # Validate role exists
        role = db.query(Role).filter(Role.name == role_name.upper()).first()
        if not role:
            return False, f"Invalid role '{role_name}'. Available roles: COMMERCIAL, SUPPORT, GESTION."

        # Step 3 & 4: Hash password with Argon2 and add user
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

        # Step 5: Audit Event Logging to Sentry.io
        log_event(
            message=f"Collaborator created: {new_user.full_name} ({new_user.employee_number}) - Role: {role.name}",
            level="info",
            extra={
                "created_user_id": new_user.id,
                "created_user_emp_num": new_user.employee_number,
                "role": role.name,
                "author_emp_num": current_user.employee_number,
            },
        )

        return True, f"Collaborator {new_user.full_name} ({new_user.employee_number}) created successfully with role {role.name}."
    except Exception as e:
        db.rollback()
        return False, f"Error creating collaborator: {e}"
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
    Updates an existing collaborator account.

    Step 1: Check permissions (Restricted to GESTION team).
    Step 2: Fetch existing user by ID from database.
    Step 3: Update specified attributes (full name, email, password, department role).
    Step 4: Commit changes and log audit event to Sentry.io.

    Args:
        user_id (int): Target user database ID.
        full_name (str | None): Optional updated full name.
        email (str | None): Optional updated email address.
        password (str | None): Optional updated password.
        role_name (str | None): Optional updated department role.
        current_user (User): Authenticated active user session.

    Returns:
        tuple[bool, str]: (success: bool, message: str).
    """
    # Step 1: RBAC Permission Verification
    allowed, msg = check_permission(current_user, ["GESTION"])
    if not allowed:
        return False, msg

    db = SessionLocal()
    try:
        # Step 2: Fetch target user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, f"Collaborator ID #{user_id} not found."

        # Step 3: Apply modifications
        changes = []
        if full_name:
            user.full_name = full_name
            changes.append("full_name")
        if email and email != user.email:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                return False, f"Email '{email}' is already in use by another collaborator."
            user.email = email
            changes.append("email")
        if password:
            user.password_hash = hash_password(password)
            changes.append("password")
        if role_name:
            role = db.query(Role).filter(Role.name == role_name.upper()).first()
            if not role:
                return False, f"Invalid role '{role_name}'. Available roles: COMMERCIAL, SUPPORT, GESTION."
            user.role_id = role.id
            changes.append("role")

        db.commit()
        db.refresh(user)

        # Step 4: Audit Event Logging to Sentry.io
        log_event(
            message=f"Collaborator updated: {user.full_name} ({user.employee_number}) - Modifs: {', '.join(changes)}",
            level="info",
            extra={
                "updated_user_id": user.id,
                "updated_user_emp_num": user.employee_number,
                "modifications": changes,
                "author_emp_num": current_user.employee_number,
            },
        )

        return True, f"Collaborator ID #{user.id} ({user.full_name}) updated successfully."
    except Exception as e:
        db.rollback()
        return False, f"Error updating collaborator: {e}"
    finally:
        db.close()

