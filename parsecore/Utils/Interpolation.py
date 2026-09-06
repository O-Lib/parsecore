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


def Lerp(start: float, final: float, amount: float) -> float:
    """Return a linear interpolation between two values.

    Mirrors ``osu.Framework.Utils.Interpolation.Lerp``.

    Args:
        start: The value at ``amount`` zero.
        final: The value at ``amount`` one.
        amount: How far between them to sample.
    """
    return start + (final - start) * amount


def DoubleLerp(value1: float, value2: float, amount: float) -> float:
    """Return a linear interpolation the way .NET's ``double.Lerp`` does.

    The weights are applied to both ends rather than to their difference, which
    makes ``amount`` of one land exactly on ``value2``. The last bit of the
    result differs from :func:`Lerp`, so the two are not interchangeable.

    Args:
        value1: The value at ``amount`` zero.
        value2: The value at ``amount`` one.
        amount: How far between them to sample.
    """
    return (value1 * (1.0 - amount)) + (value2 * amount)
