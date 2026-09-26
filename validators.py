import re
from datetime import datetime


def validate_email(email: str) -> tuple[bool, str]:
    """Validates email format using regex."""
    if not email or not isinstance(email, str):
        return False, "L'adresse email ne peut pas être vide."
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email.strip()):
        return False, f"Format d'email invalide : '{email}'."
    return True, ""


def validate_employee_number(emp_num: str) -> tuple[bool, str]:
    """Validates employee number format."""
    if not emp_num or not isinstance(emp_num, str):
        return False, "Le numéro d'employé ne peut pas être vide."
    emp_num = emp_num.strip()
    if len(emp_num) < 3:
        return False, "Le numéro d'employé doit contenir au moins 3 caractères (ex: EMP001)."
    return True, ""


def validate_date_format(date_str: str) -> tuple[bool, datetime | None, str]:
    """
    Validates date string format YYYY-MM-DD HH:MM.
    Returns (is_valid: bool, datetime_obj, error_message).
    """
    if not date_str or not isinstance(date_str, str):
        return False, None, "La date ne peut pas être vide."
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M")
        return True, dt, ""
    except ValueError:
        return False, None, f"Format de date invalide '{date_str}'. Utiliser le format 'YYYY-MM-DD HH:MM' (ex: 2026-10-15 14:30)."


def validate_positive_amount(amount: float, field_name: str = "Montant") -> tuple[bool, str]:
    """Validates that a numeric amount is >= 0."""
    try:
        val = float(amount)
        if val < 0:
            return False, f"{field_name} doit être une valeur positive ou nulle."
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name} doit être un nombre valide."
