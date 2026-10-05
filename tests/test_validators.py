"""
Unit tests for validators module (validators.py).
"""

from validators import (
    validate_email,
    validate_employee_number,
    validate_positive_amount,
    validate_date_format,
)


def test_validate_email_valid():
    is_valid, err = validate_email("bill.boquet@epicevents.io")
    assert is_valid is True
    assert err == ""

    is_valid, err = validate_email("alex.dev@domain.com")
    assert is_valid is True
    assert err == ""


def test_validate_email_invalid():
    is_valid, err = validate_email("invalid-email")
    assert is_valid is False
    assert "Invalid email format" in err

    is_valid, err = validate_email("")
    assert is_valid is False
    assert "cannot be empty" in err


def test_validate_employee_number_valid():
    is_valid, err = validate_employee_number("EMP001")
    assert is_valid is True
    assert err == ""


def test_validate_employee_number_invalid():
    is_valid, err = validate_employee_number("E1")
    assert is_valid is False
    assert "at least 3 characters" in err

    is_valid, err = validate_employee_number("")
    assert is_valid is False
    assert "cannot be empty" in err


def test_validate_positive_amount():
    is_valid, err = validate_positive_amount(100.0)
    assert is_valid is True
    assert err == ""

    is_valid, err = validate_positive_amount(0.0)
    assert is_valid is True
    assert err == ""

    is_valid, err = validate_positive_amount(-50.0)
    assert is_valid is False
    assert "must be a positive number" in err


def test_validate_date_format():
    is_valid, dt, err = validate_date_format("2026-10-15 10:00")
    assert is_valid is True
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.day == 15
    assert err == ""

    is_valid, dt, err = validate_date_format("invalid-date")
    assert is_valid is False
    assert dt is None
    assert "Invalid date format" in err
