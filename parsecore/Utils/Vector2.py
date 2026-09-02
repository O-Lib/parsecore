"""
MIT License

Copyright (c) 2026-Present O!Lib

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass

_PACK_F32 = struct.Struct("<f").pack
_UNPACK_F32 = struct.Struct("<f").unpack


def f32(value: float) -> float:
    """Return ``value`` rounded to single precision.

    Args:
        value: The double-precision value.

    Returns:
        The nearest ``float32`` value, as a Python float.
    """
    return _UNPACK_F32(_PACK_F32(value))[0]


F32_EPSILON = 1e-3


@dataclass(frozen=True, slots=True)
class Vector2:
    """A point or offset on the playfield, held at single precision."""

    X: float = 0.0
    Y: float = 0.0

    def __post_init__(self) -> None:
        """Narrow both components to single precision."""
        object.__setattr__(self, "X", f32(self.X))
        object.__setattr__(self, "Y", f32(self.Y))

    def __add__(self, other: Vector2) -> Vector2:
        """Return the component-wise sum."""
        return Vector2(self.X + other.X, self.Y + other.Y)

    def __sub__(self, other: Vector2) -> Vector2:
        """Return the component-wise difference."""
        return Vector2(self.X - other.X, self.Y - other.Y)

    def __mul__(self, scalar: float) -> Vector2:
        """Return this vector scaled by ``scalar``."""
        return Vector2(self.X * scalar, self.Y * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> Vector2:
        """Return this vector divided by ``scalar``."""
        return Vector2(self.X / scalar, self.Y / scalar)

    def __neg__(self) -> Vector2:
        """Return the negated vector."""
        return Vector2(-self.X, -self.Y)

    def length(self) -> float:
        """Return the vector's length.

        Each product is narrowed on its own, because osu! computes this in
        single precision and the intermediate rounding is observable.
        """
        return f32(math.sqrt(f32(f32(self.X * self.X) + f32(self.Y * self.Y))))

    def length_squared(self) -> float:
        """Return the vector's squared length."""
        return f32(f32(self.X * self.X) + f32(self.Y * self.Y))

    def normalised(self) -> Vector2:
        """Return a unit vector in the same direction (zero stays zero).

        osuTK scales by the reciprocal of the length rather than dividing by
        it, and the two round differently in single precision, so the
        reciprocal is taken here as well. The zero case would give osuTK a NaN;
        no real path reaches it, and returning zero keeps that from spreading.
        """
        length = self.length()
        if length == 0.0:
            return Vector2()
        scale = f32(1.0 / length)
        return Vector2(self.X * scale, self.Y * scale)

    @staticmethod
    def distance(a: Vector2, b: Vector2) -> float:
        """Return the distance between two points.

        Args:
            a: The first point.
            b: The second point.
        """
        return (a - b).length()

    @staticmethod
    def dot(a: Vector2, b: Vector2) -> float:
        """Return the dot product of two vectors.

        Args:
            a: The first vector.
            b: The second vector.
        """
        return f32(f32(a.X * b.X) + f32(a.Y * b.Y))
