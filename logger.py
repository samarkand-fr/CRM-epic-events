"""
Sentry.io Remote Logging and Exception Audit Module (logger.py).

This module handles centralized error capture and security audit logging:
1. Initializing the Sentry SDK with DSN configuration loaded securely from environment variables.
2. Logging business audit events (User creation/updates, contract signatures) to Sentry.io.
3. Capturing unexpected runtime exceptions with full stack traces for debugging.
"""

import os
import sentry_sdk
from dotenv import load_dotenv

# Step 1: Load environment variables
load_dotenv()

SENTRY_DSN = os.getenv("SENTRY_DSN")


def init_sentry():
    """
    Initializes the Sentry SDK if a valid SENTRY_DSN is configured in environment.
    Fails gracefully without crashing if no DSN is provided or placeholder is used.
    """
    if SENTRY_DSN and SENTRY_DSN.strip() and not SENTRY_DSN.startswith("your_"):
        try:
            sentry_sdk.init(
                dsn=SENTRY_DSN.strip(),
                traces_sample_rate=1.0,
                environment=os.getenv("ENVIRONMENT", "development"),
            )
            print("🟢 Sentry SDK initialized successfully.")
        except Exception as e:
            print(f"⚠️ Unable to initialize Sentry SDK: {e}")
    else:
        print("ℹ️ Sentry DSN not configured. Running in local fallback mode.")


def _apply_scope_metadata(scope, extra: dict):
    """
    Helper to populate Sentry scope with indexable tags, structured contexts, and user profiles.
    """
    # 1. Indexable Tag for rapid Sentry UI searching (e.g. event_type:access_denied)
    if "event_type" in extra:
        scope.set_tag("event_type", extra["event_type"])

    # 2. Attach User Identity to Sentry's User section if available
    user_info = {}
    if "user_id" in extra:
        user_info["id"] = str(extra["user_id"])
    if "employee_number" in extra:
        user_info["username"] = extra["employee_number"]
    elif "author_emp_num" in extra:
        user_info["username"] = extra["author_emp_num"]
    if "user_email" in extra:
        user_info["email"] = extra["user_email"]
    if "user_role" in extra:
        scope.set_tag("user_role", extra["user_role"])

    if user_info:
        scope.set_user(user_info)

    # 3. Structured Context Panel in Sentry UI
    scope.set_context("Audit Details", extra)


def log_event(message: str, level: str = "info", extra: dict | None = None):
    """
    Logs an audit event / business message to Sentry.io.

    Args:
        message (str): Audit message to record.
        level (str): Log level ('info', 'warning', 'error', 'critical').
        extra (dict | None): Contextual payload key-value dictionary.
    """
    try:
        if SENTRY_DSN and SENTRY_DSN.strip() and not SENTRY_DSN.startswith("your_"):
            with sentry_sdk.push_scope() as scope:
                if extra:
                    _apply_scope_metadata(scope, extra)
                sentry_sdk.capture_message(message, level=level)
    except Exception as e:
        print(f"⚠️ Error capturing log event in Sentry: {e}")


def log_exception(error: Exception, extra: dict | None = None):
    """
    Captures an unhandled runtime exception and stacktrace to Sentry.io.

    Args:
        error (Exception): Caught python exception instance.
        extra (dict | None): Optional contextual metadata.
    """
    try:
        if SENTRY_DSN and SENTRY_DSN.strip() and not SENTRY_DSN.startswith("your_"):
            with sentry_sdk.push_scope() as scope:
                if extra:
                    _apply_scope_metadata(scope, extra)
                sentry_sdk.capture_exception(error)
    except Exception as e:
        print(f"⚠️ Error capturing exception in Sentry: {e}")
