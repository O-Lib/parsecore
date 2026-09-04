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

SQRT2 = 1.4142135623730950


def Pow(base_value: float, exponent: float) -> float:
    """Return ``base_value`` raised to ``exponent``.

    osu! declares this twice: once taking a ``double`` exponent, which defers
    to ``Math.Pow``, and once taking an ``int``, which multiplies the base out
    by hand for exponents up to five. Which one runs is decided by the type of
    the exponent written at the call site, and the two do not agree to the last
    bit -- ``x * x * x`` is not ``Math.Pow(x, 3)``. Python draws the same line
    between ``3`` and ``3.0``, so the exponent's type is honoured here too, and
    call sites must pass whichever type osu! writes.

    The ``Math.Pow`` path returns NaN where Python would raise: a negative base
    with a fractional exponent, or a result too large to hold.

    Args:
        base_value: The base.
        exponent: The exponent.
    """
    if isinstance(exponent, int) and not isinstance(exponent, bool):
        match exponent:
            case 0:
                return 1.0
            case 1:
                return base_value
            case 2:
                return base_value * base_value
            case 3:
                return base_value * base_value * base_value
            case 4:
                return base_value * base_value * base_value * base_value
            case 5:
                # The largest exponent osu!'s difficulty calculation uses.
                return (
                    base_value * base_value * base_value * base_value * base_value
                )

    try:
        return math.pow(base_value, exponent)
    except (ValueError, OverflowError):
        return math.nan


def Logistic(
    x: float, midpoint_offset: float = 0.0, multiplier: float = 1.0,
    max_value: float = 1.0,
) -> float:
    """Return a logistic curve evaluated at ``x``.

    Args:
        x: The input value.
        midpoint_offset: Where the curve reaches half its maximum.
        multiplier: How steeply the curve rises.
        max_value: The curve's upper bound.

    Returns:
        The curve's value at ``x``.
    """
    return max_value / (1 + math.exp(multiplier * (midpoint_offset - x)))


def LogisticExp(exponent: float, max_value: float = 1.0) -> float:
    """Return a logistic curve from a precomputed exponent.

    Args:
        exponent: The exponent to feed the curve.
        max_value: The curve's upper bound.
    """
    return max_value / (1 + math.exp(exponent))


def Erf(x: float) -> float:
    """Return the error function of ``x``.

    This is Abramowitz and Stegun's formula 7.1.26, the approximation osu!
    uses. Python's ``math.erf`` is far more accurate, and that is exactly why
    it cannot be used here: the pp value follows from these digits, so it has
    to be wrong in the same way osu!'s is.

    Args:
        x: The input value.
    """
    if x == 0:
        return 0.0
    if x == math.inf:
        return 1.0
    if x == -math.inf:
        return -1.0
    if math.isnan(x):
        return math.nan

    t = 1.0 / (1.0 + 0.3275911 * abs(x))
    tau = t * (
        0.254829592
        + t
        * (
            -0.284496736
            + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))
        )
    )

    erf = 1.0 - tau * math.exp(-x * x)

    return erf if x >= 0 else -erf


def ErfInv(x: float) -> float:
    """Return the inverse error function of ``x``.

    Winitzki's approximation with the correction term osu! applies above
    ``0.85``, which brings its worst error from -0.005 down to -0.00045. As
    with :func:`Erf`, the approximation is the point: a more accurate inverse
    would move every pp value away from osu!'s.

    Args:
        x: A value in the interval ``[-1, 1]``.

    Returns:
        The value whose error function is ``x``.
    """
    if x <= -1:
        return -math.inf
    if x >= 1:
        return math.inf
    if x == 0:
        return 0.0

    a = 0.147
    sgn = math.copysign(1.0, x)
    x = abs(x)

    ln = math.log(1 - x * x)
    t1 = 2 / (math.pi * a) + ln / 2
    t2 = ln / a
    base_approx = math.sqrt(t1 * t1 - t2) - t1

    correction = Pow((x - 0.85) / 0.293, 8) if x >= 0.85 else 0
    return sgn * (math.sqrt(base_approx) + correction)


def Smoothstep(x: float, start: float, end: float) -> float:
    """Return a smooth ramp from ``0`` to ``1`` between two bounds.

    Args:
        x: The input value.
        start: The value mapping to ``0``.
        end: The value mapping to ``1``.
    """
    x = ReverseLerp(x, start, end)
    return x * x * (3.0 - 2.0 * x)


def Smootherstep(x: float, start: float, end: float) -> float:
    """Return a smoother ramp from ``0`` to ``1`` between two bounds.

    Args:
        x: The input value.
        start: The value mapping to ``0``.
        end: The value mapping to ``1``.
    """
    x = ReverseLerp(x, start, end)
    return x * x * x * (x * (6.0 * x - 15.0) + 10.0)


def ReverseLerp(x: float, start: float, end: float) -> float:
    """Return where ``x`` falls between two bounds, clamped to ``0``-``1``.

    Args:
        x: The input value.
        start: The value mapping to ``0``.
        end: The value mapping to ``1``.
    """
    if start == end:
        return 0.0
    return min(max((x - start) / (end - start), 0.0), 1.0)


def Norm(p: float, *values: float) -> float:
    """Return the p-norm of a set of values.

    A negative value raised to a fractional power has no real answer, and osu!
    lets the resulting NaN travel: the caller then sees a norm that fails every
    comparison, which is how a negative strain drops out of a sum entirely.
    Taking the magnitude instead would quietly keep it.

    Args:
        p: The norm's exponent, always a real number to osu!.
        *values: The values to combine.
    """
    p = float(p)

    total = 0.0
    for x in values:
        total += Pow(x, p)

    return Pow(total, 1.0 / p)


def BellCurve(
    x: float, mean: float, width: float, multiplier: float = 1.0
) -> float:
    """Return a bell curve evaluated at ``x``.

    Args:
        x: The input value.
        mean: Where the curve peaks.
        width: How wide the curve is.
        multiplier: The curve's peak value.
    """
    return multiplier * math.exp(math.e * -(math.pow(x - mean, 2) / math.pow(width, 2)))


def SmoothstepBellCurve(
    x: float, mean: float | None = None, width: float | None = None
) -> float:
    """Return a smoothstep bell curve peaking at ``1``.

    With no bounds given, peaks at ``x = 0.5`` and falls to zero at ``0`` and
    ``1``. With ``mean`` and ``width``, peaks at ``mean`` and falls to zero
    ``width`` either side of it.

    Args:
        x: The input value.
        mean: Where the curve peaks, if given.
        width: How far either side of the peak the curve reaches zero.

    Returns:
        The curve's value at ``x``.
    """
    if mean is None or width is None:
        x = 0.5 - abs(x - 0.5)
        x = min(max(x * 2.0, 0.0), 1.0)
        return x * x * (3.0 - 2.0 * x)

    x -= mean
    x = (width - x) if x > 0 else (width + x)
    return Smoothstep(x, 0.0, width)


def Erfc(x: float) -> float:
    """Return the complementary error function of ``x``.

    Taken from :func:`Erf` by subtraction, the way osu! defines it, rather than
    from ``math.erfc``.

    Args:
        x: The input value.
    """
    return 1 - Erf(x)


def ErfcInv(z: float) -> float:
    """Return the inverse complementary error function of ``z``.

    Args:
        z: A value in the open interval ``(0, 2)``.
    """
    return ErfInv(1.0 - z)


def MillisecondsToBPM(milliseconds: float, delimiter: int = 4) -> float:
    """Return the tempo a note length corresponds to.

    Args:
        milliseconds: The note length.
        delimiter: Which rhythm delimiter to use; the default is 1/4.
    """
    return 60000.0 / (milliseconds * delimiter)


def BPMToMilliseconds(bpm: float, delimiter: int = 4) -> float:
    """Return the note length a tempo corresponds to.

    Args:
        bpm: The tempo in beats per minute.
        delimiter: Which rhythm delimiter to use; the default is 1/4.
    """
    return 60000.0 / delimiter / bpm
