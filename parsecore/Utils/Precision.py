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

# The tolerance osu! allows two doubles by default.
DOUBLE_EPSILON = 1e-14

# The tolerance osu! allows two single-precision values by default.
FLOAT_EPSILON = 1e-3


def AlmostBigger(
    value1: float, value2: float, acceptable_difference: float = DOUBLE_EPSILON
) -> bool:
    """Return whether one value is bigger than another, or close enough to it.

    Args:
        value1: The value that might be bigger.
        value2: The value to compare against.
        acceptable_difference: How far apart the two may be.
    """
    return value1 > value2 - acceptable_difference


def DefinitelyBigger(
    value1: float, value2: float, acceptable_difference: float = DOUBLE_EPSILON
) -> bool:
    """Return whether one value is bigger than another by a clear margin.

    Args:
        value1: The value that might be bigger.
        value2: The value to compare against.
        acceptable_difference: How far apart the two must be.
    """
    return value1 - acceptable_difference > value2


def AlmostEquals(
    value1: float, value2: float, acceptable_difference: float = DOUBLE_EPSILON
) -> bool:
    """Return whether two values are close enough to be treated as equal.

    Args:
        value1: The first value.
        value2: The second value.
        acceptable_difference: How far apart the two may be.
    """
    return abs(value1 - value2) <= acceptable_difference
