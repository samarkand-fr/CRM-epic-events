"""
Security and Cryptographic Authentication Module (security.py).

This module handles cryptographic security operations:
1. Password hashing and salting using Argon2 algorithm.
2. JSON Web Token (JWT) session generation and decoding.
3. Secure local token session storage at ~/.epic_events_token (POSIX permission 0600).
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from dotenv import load_dotenv

# Step 1: Load environment variables
load_dotenv()

# Step 2: Load JWT secret key from environment
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is missing from .env configuration file.")

ALGORITHM = "HS256"
SESSION_FILE_PATH = os.path.expanduser("~/.epic_events_token")

# Step 3: Configure CryptContext with Argon2 primary hashing algorithm and bcrypt fallback
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hashes and salts a cleartext password securely using Argon2.

    Args:
        password (str): Cleartext password.

    Returns:
        str: Argon2 hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a cleartext password against a stored Argon2 hash.

    Args:
        plain_password (str): Input cleartext password.
        hashed_password (str): Stored Argon2 hash from DB.

    Returns:
        bool: True if password matches hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, employee_number: str, role_name: str, expires_delta: timedelta = timedelta(hours=8)) -> str:
    """
    Generates a signed JWT access token for an authenticated user.

    Args:
        user_id (int): Unique database ID of the user.
        employee_number (str): Business employee code (e.g. EMP001).
        role_name (str): Department role (COMMERCIAL, SUPPORT, GESTION).
        expires_delta (timedelta): Token lifetime (default 8 hours).

    Returns:
        str: Encoded and signed JWT token string.
    """
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "user_id": user_id,
        "employee_number": employee_number,
        "role_name": role_name,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> tuple[dict | None, str | None]:
    """
    Decodes and validates a JWT access token.

    Args:
        token (str): The JWT string to verify.

    Returns:
        tuple[dict | None, str | None]: (payload dict, error_code str).
        Returns (None, "TOKEN_EXPIRED") if expired, or (None, "TOKEN_INVALID") if invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload, None
    except jwt.ExpiredSignatureError:
        clear_session_token()
        return None, "TOKEN_EXPIRED"
    except jwt.InvalidTokenError:
        clear_session_token()
        return None, "TOKEN_INVALID"


def save_session_token(token: str) -> None:
    """
    Saves the JWT session token to local file ~/.epic_events_token
    with restricted read/write permissions (chmod 0600 - Owner read/write only).

    Args:
        token (str): Active session JWT string.
    """
    with open(SESSION_FILE_PATH, "w") as f:
        f.write(token)
    os.chmod(SESSION_FILE_PATH, 0o600)


def get_session_token() -> str | None:
    """
    Reads persistent session token from local file if present.

    Returns:
        str | None: JWT string if file exists, None otherwise.
    """
    if os.path.exists(SESSION_FILE_PATH):
        try:
            with open(SESSION_FILE_PATH, "r") as f:
                token = f.read().strip()
                return token if token else None
        except Exception:
            return None
    return None


def clear_session_token() -> None:
    """
    Deletes local session token file on logout or token expiration.
    """
    if os.path.exists(SESSION_FILE_PATH):
        try:
            os.remove(SESSION_FILE_PATH)
        except Exception:
            pass

