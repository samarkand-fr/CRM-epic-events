import os
import sentry_sdk
from dotenv import load_dotenv

load_dotenv()

SENTRY_DSN = os.getenv("SENTRY_DSN")


def init_sentry():
    """
    Initializes the Sentry SDK if SENTRY_DSN is provided in environment.
    Fails gracefully if no DSN is provided.
    """
    if SENTRY_DSN and SENTRY_DSN.strip() and not SENTRY_DSN.startswith("your_"):
        try:
            sentry_sdk.init(
                dsn=SENTRY_DSN.strip(),
                traces_sample_rate=1.0,
                environment=os.getenv("ENVIRONMENT", "development"),
            )
            print("🟢 Sentry SDK initialisé avec succès.")
        except Exception as e:
            print(f"⚠️ Impossible d'initialiser Sentry SDK : {e}")
    else:
        # Sentry DSN not configured; logging works in local fallback mode
        pass


def log_event(message: str, level: str = "info", extra: dict | None = None):
    """
    Logs an audit event / message to Sentry.io.
    Levels: info, warning, error, critical.
    """
    try:
        if SENTRY_DSN and SENTRY_DSN.strip() and not SENTRY_DSN.startswith("your_"):
            with sentry_sdk.push_scope() as scope:
                if extra:
                    for k, v in extra.items():
                        scope.set_extra(k, v)
                sentry_sdk.capture_message(message, level=level)
    except Exception as e:
        print(f"⚠️ Erreur lors de l'envoi du log à Sentry : {e}")


def log_exception(error: Exception, extra: dict | None = None):
    """
    Logs an unhandled exception / stacktrace to Sentry.io.
    """
    try:
        if SENTRY_DSN and SENTRY_DSN.strip() and not SENTRY_DSN.startswith("your_"):
            with sentry_sdk.push_scope() as scope:
                if extra:
                    for k, v in extra.items():
                        scope.set_extra(k, v)
                sentry_sdk.capture_exception(error)
    except Exception as e:
        print(f"⚠️ Erreur lors de la capture de l'exception dans Sentry : {e}")
