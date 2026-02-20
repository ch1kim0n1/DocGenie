"""Basic arithmetic operations module."""

from __future__ import annotations


def add(a: float, b: float) -> float:
    """Add two numbers together and return their sum.

    Args:
        a: The first operand.
        b: The second operand.

    Returns:
        The sum of a and b.
    """
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract b from a and return the result.

    Args:
        a: The minuend.
        b: The subtrahend.

    Returns:
        The difference a - b.
    """
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return their product.

    Args:
        a: The first factor.
        b: The second factor.

    Returns:
        The product of a and b.
    """
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b and return the quotient.

    Args:
        a: The dividend.
        b: The divisor.

    Returns:
        The quotient a / b.

    Raises:
        ZeroDivisionError: If b is zero.
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def power(base: float, exponent: int) -> float:
    """Raise base to an integer exponent.

    Args:
        base: The base value.
        exponent: The integer exponent (may be negative).

    Returns:
        base raised to the power of exponent.
    """
    return base**exponent


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp value to the inclusive range [minimum, maximum].

    Args:
        value: The value to clamp.
        minimum: The lower bound.
        maximum: The upper bound.

    Returns:
        value if within range, else the nearest bound.
    """
    return max(minimum, min(value, maximum))
