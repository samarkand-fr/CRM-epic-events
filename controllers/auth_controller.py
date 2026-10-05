"""
Authentication Controller Module (controllers/auth_controller.py).

This module manages user login authentication and logout logic:
1. Validating user identity (email or employee number) against PostgreSQL DB.
2. Verifying password hashes using Argon2 algorithm.
3. Generating and persisting JWT session tokens locally at ~/.epic_events_token.
4. Handling session logout by invalidating local token files.
"""

from db import SessionLocal
from models import User
from security import verify_password, create_access_token, save_session_token, clear_session_token
from logger import log_event, log_exception


def login_user(identifier: str, password: str) -> tuple[bool, str]:
    """
    Authenticates an employee user via email or employee number and password.

    Step 1: Look up user in database by email or employee number.
    Step 2: Verify Argon2 password hash.
    Step 3: Generate signed JWT session access token containing user payload.
    Step 4: Save persistent session token to local file ~/.epic_events_token (chmod 0600).

    Args:
        identifier (str): Email address or employee number (e.g. EMP001).
        password (str): Input password string.

    Returns:
        tuple[bool, str]: (success: bool, message: str).
    """
    db = SessionLocal()
    try:
        # Step 1: Query User entity matching identifier
        user = (
            db.query(User)
            .filter((User.email == identifier) | (User.employee_number == identifier))
            .first()
        )
        if not user:
            log_event(
                message=f"Security Alert: Failed login attempt (User identifier '{identifier}' not found)",
                level="warning",
                extra={"identifier": identifier, "event_type": "login_failed_user_not_found"},
            )
            return False, "User identifier (email or employee number) not found."

        # Step 2: Verify cleartext password against Argon2 stored hash
        if not verify_password(password, user.password_hash):
            log_event(
                message=f"Security Alert: Failed login attempt for {user.full_name} ({user.employee_number}) - Incorrect password",
                level="warning",
                extra={
                    "user_id": user.id,
                    "employee_number": user.employee_number,
                    "event_type": "login_failed_incorrect_password",
                },
            )
            return False, "Incorrect password."

        # Step 3: Create JWT access token
        role_name = user.role.name if user.role else "UNKNOWN"
        token = create_access_token(
            user_id=user.id,
            employee_number=user.employee_number,
            role_name=role_name,
        )

        # Step 4: Persist JWT token to secure local session file
        save_session_token(token)

        # Audit Event Logging to Sentry.io for Successful Login
        log_event(
            message=f"User login successful: {user.full_name} ({user.employee_number}) - Role: {role_name}",
            level="info",
            extra={
                "user_id": user.id,
                "employee_number": user.employee_number,
                "role": role_name,
                "event_type": "login_success",
            },
        )
        return True, f"Login successful! Welcome {user.full_name} (Role: {role_name}). JWT session token saved."
    except Exception as e:
        log_exception(e, extra={"identifier": identifier, "event_type": "login_exception"})
        return False, f"Error during user authentication: {e}"
    finally:
        db.close()


def logout_user() -> bool:
    """
    Logs out the active user by deleting the local persistent JWT session token file.

    Returns:
        bool: True upon completion.
    """
    clear_session_token()
    return True

