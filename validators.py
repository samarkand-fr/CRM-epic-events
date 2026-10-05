"""
Data Input Validation Module (validators.py).

This module contains input validation routines to verify user inputs
prior to sending data to database controllers or storing in PostgreSQL:
1. Email format verification via regular expressions.
2. Employee number format check (minimum length, non-empty).
3. Date format validation (YYYY-MM-DD HH:MM).
4. Non-negative numeric amount checks (contracts, pricing).
"""

import re
from datetime import datetime


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validates email format using regular expressions.

    Args:
        email (str): Email string to validate.

    Returns:
        tuple[bool, str]: (is_valid, error_message).
    """
    if not email or not isinstance(email, str):
        return False, "Email address cannot be empty."
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email.strip()):
        return False, f"Invalid email format: '{email}'."
    return True, ""


def validate_employee_number(emp_num: str) -> tuple[bool, str]:
    """
    Validates employee identification number format.

    Args:
        emp_num (str): Employee number string (e.g. EMP001).

    Returns:
        tuple[bool, str]: (is_valid, error_message).
    """
    if not emp_num or not isinstance(emp_num, str):
        return False, "Employee number cannot be empty."
    emp_num = emp_num.strip()
    if len(emp_num) < 3:
        return False, "Employee number must contain at least 3 characters (e.g. EMP001)."
    return True, ""


def validate_date_format(date_str: str) -> tuple[bool, datetime | None, str]:
    """
    Validates date string format 'YYYY-MM-DD HH:MM'.

    Args:
        date_str (str): Input date string.

    Returns:
        tuple[bool, datetime | None, str]: (is_valid, datetime_object, error_message).
    """
    if not date_str or not isinstance(date_str, str):
        return False, None, "Date string cannot be empty."
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M")
        return True, dt, ""
    except ValueError:
        return False, None, f"Invalid date format '{date_str}'. Please use format 'YYYY-MM-DD HH:MM' (e.g. 2026-10-15 14:30)."


def validate_positive_amount(amount: float, field_name: str = "Amount") -> tuple[bool, str]:
    """
    Validates that a numeric financial amount is non-negative (>= 0).

    Args:
        amount (float): Value to validate.
        field_name (str): Label used in error messages.

    Returns:
        tuple[bool, str]: (is_valid, error_message).
    """
    try:
        val = float(amount)
        if val < 0:
            return False, f"{field_name} must be a positive number or zero."
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number."

