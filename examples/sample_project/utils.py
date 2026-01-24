"""
Utility functions for the sample project.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    """
    Generate a secure random token.

    Returns:
        Random token string
    """
    return secrets.token_urlsafe(32)


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid format
    """
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


class DateHelper:
    """Helper class for date operations."""

    @staticmethod
    def format_date(date: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Format a datetime object.

        Args:
            date: Datetime object
            format_str: Format string

        Returns:
            Formatted date string
        """
        return date.strftime(format_str)

    @staticmethod
    def add_days(date: datetime, days: int) -> datetime:
        """
        Add days to a date.

        Args:
            date: Base date
            days: Number of days to add

        Returns:
            New datetime object
        """
        return date + timedelta(days=days)

    @staticmethod
    def is_weekend(date: datetime) -> bool:
        """
        Check if date falls on weekend.

        Args:
            date: Date to check

        Returns:
            True if weekend
        """
        return date.weekday() >= 5


def calculate_age(birth_date: datetime) -> int:
    """
    Calculate age from birth date.

    Args:
        birth_date: Date of birth

    Returns:
        Age in years
    """
    today = datetime.now()
    age = today.year - birth_date.year

    # Adjust if birthday hasn't occurred this year
    if today.month < birth_date.month or (
        today.month == birth_date.month and today.day < birth_date.day
    ):
        age -= 1

    return age


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix
