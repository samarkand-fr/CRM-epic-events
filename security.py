import os
import json
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "EPIC_EVENTS_CRM_SUPER_SECRET_KEY_2026")
ALGORITHM = "HS256"
SESSION_FILE_PATH = os.path.expanduser("~/.epic_events_session")

# Passlib CryptContext using Argon2 as primary scheme, with bcrypt as fallback
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hashes and salts password securely using Argon2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, employee_number: str, role_name: str, expires_delta: timedelta = timedelta(hours=8)) -> str:
    """Generates a JWT token for the authenticated user."""
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "user_id": user_id,
        "employee_number": employee_number,
        "role_name": role_name,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def save_session_token(token: str) -> None:
    """Saves JWT token to local session file with restrictive permissions (0600)."""
    with open(SESSION_FILE_PATH, "w") as f:
        f.write(token)
    os.chmod(SESSION_FILE_PATH, 0o600)


def get_session_token() -> str | None:
    """Reads session token from local session file if exists."""
    if os.path.exists(SESSION_FILE_PATH):
        try:
            with open(SESSION_FILE_PATH, "r") as f:
                token = f.read().strip()
                return token if token else None
        except Exception:
            return None
    return None


def clear_session_token() -> None:
    """Deletes local session token file on logout."""
    if os.path.exists(SESSION_FILE_PATH):
        try:
            os.remove(SESSION_FILE_PATH)
        except Exception:
            pass
