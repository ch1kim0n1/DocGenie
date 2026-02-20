"""Command-line interface for the demo_library."""

from __future__ import annotations

import sys

from mathlib.arithmetic import add, divide, multiply, subtract
from mathlib.geometry import Circle, Rectangle, Triangle


def main() -> int:
    """Entry point for the demo_library CLI.

    Prints a brief demo of each module's capabilities and exits.

    Returns:
        0 on success.
    """
    print("=== demo_library CLI ===\n")

    # Arithmetic
    print("Arithmetic:")
    print(f"  3 + 4 = {add(3, 4)}")
    print(f"  10 - 3 = {subtract(10, 3)}")
    print(f"  6 * 7 = {multiply(6, 7)}")
    print(f"  22 / 7 = {divide(22, 7):.6f}")

    # Geometry
    print("\nGeometry:")
    c = Circle(5.0)
    r = Rectangle(4.0, 6.0)
    t = Triangle(3.0, 4.0, 5.0)
    print(f"  {c.describe()}")
    print(f"  {r.describe()}")
    print(f"  {t.describe()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
