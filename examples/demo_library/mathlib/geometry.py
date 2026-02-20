"""Geometric shapes and area/perimeter computations."""

from __future__ import annotations

import math


class Shape:
    """Abstract base class for geometric shapes.

    All concrete shapes should implement :meth:`area` and :meth:`perimeter`.
    """

    def area(self) -> float:
        """Return the area of the shape."""
        raise NotImplementedError

    def perimeter(self) -> float:
        """Return the perimeter (circumference) of the shape."""
        raise NotImplementedError

    def describe(self) -> str:
        """Return a human-readable description with area and perimeter."""
        return (
            f"{type(self).__name__}: area={self.area():.4f}, "
            f"perimeter={self.perimeter():.4f}"
        )


class Circle(Shape):
    """A circle defined by its radius.

    Args:
        radius: The radius of the circle (must be positive).
    """

    def __init__(self, radius: float) -> None:
        if radius <= 0:
            raise ValueError(f"radius must be positive, got {radius}")
        self.radius = radius

    def area(self) -> float:
        """Return the area of the circle (π × r²)."""
        return math.pi * self.radius**2

    def perimeter(self) -> float:
        """Return the circumference of the circle (2 × π × r)."""
        return 2 * math.pi * self.radius

    @classmethod
    def from_diameter(cls, diameter: float) -> "Circle":
        """Create a Circle from its diameter.

        Args:
            diameter: The diameter of the circle.

        Returns:
            A new Circle instance.
        """
        return cls(diameter / 2)


class Rectangle(Shape):
    """A rectangle defined by width and height.

    Args:
        width: The horizontal dimension.
        height: The vertical dimension.
    """

    def __init__(self, width: float, height: float) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        self.width = width
        self.height = height

    def area(self) -> float:
        """Return the area of the rectangle (width × height)."""
        return self.width * self.height

    def perimeter(self) -> float:
        """Return the perimeter of the rectangle (2 × (width + height))."""
        return 2 * (self.width + self.height)

    @property
    def is_square(self) -> bool:
        """True if width equals height."""
        return self.width == self.height

    @classmethod
    def square(cls, side: float) -> "Rectangle":
        """Create a square (width == height).

        Args:
            side: The side length.

        Returns:
            A Rectangle where width == height == side.
        """
        return cls(side, side)


class Triangle(Shape):
    """A triangle defined by three side lengths.

    Uses Heron's formula for area computation.

    Args:
        a: Length of the first side.
        b: Length of the second side.
        c: Length of the third side.
    """

    def __init__(self, a: float, b: float, c: float) -> None:
        if a + b <= c or b + c <= a or a + c <= b:
            raise ValueError("Invalid triangle: sides do not satisfy triangle inequality")
        self.a = a
        self.b = b
        self.c = c

    def area(self) -> float:
        """Return the area using Heron's formula."""
        s = self.perimeter() / 2
        return math.sqrt(s * (s - self.a) * (s - self.b) * (s - self.c))

    def perimeter(self) -> float:
        """Return the perimeter (sum of all three sides)."""
        return self.a + self.b + self.c
