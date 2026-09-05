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

import math

import pytest

from parsecore.Rulesets.Difficulty.Utils import DiffUtils


def test_erf_inv_round_trips():
    """The inverse error function undoes the error function.

    Both sides are approximations, so the round trip only holds to their
    combined error rather than to machine precision.
    """
    for value in (-0.9, -0.5, -0.1, 0.0, 0.1, 0.5, 0.9, 0.999):
        assert DiffUtils.Erf(DiffUtils.ErfInv(value)) == pytest.approx(value, abs=2e-3)


def test_erf_reproduces_osus_approximation():
    """The error function is osu!'s approximation, not an exact one.

    osu! uses Abramowitz and Stegun 7.1.26, which is off the true value by
    around 1e-7. pp is read off these digits, so the approximation has to be
    reproduced rather than improved on.
    """
    assert DiffUtils.Erf(0) == 0.0
    assert DiffUtils.Erf(1) == 0.8427006897475899

    exact_at_one = 0.8427007929497149
    assert DiffUtils.Erf(1) != exact_at_one
    assert abs(DiffUtils.Erf(1) - exact_at_one) < 1.5e-7


def test_erf_inv_reproduces_osus_approximation():
    """The inverse error function is osu!'s approximation too.

    Winitzki's formula with the correction osu! adds above 0.85; its error is
    a few parts in ten thousand, far coarser than machine precision.
    """
    assert DiffUtils.ErfInv(0) == 0.0
    assert DiffUtils.ErfInv(-1) == float("-inf")
    assert DiffUtils.ErfInv(1) == float("inf")

    assert DiffUtils.ErfInv(-0.9) == -DiffUtils.ErfInv(0.9)

    exact_at_half = 0.4769362762044699
    assert abs(DiffUtils.ErfInv(0.5) - exact_at_half) < 5e-4


def test_erfc_is_derived_from_erf():
    """The complementary error function is one minus the error function."""
    for value in (-1.5, -0.25, 0.0, 0.25, 1.5):
        assert DiffUtils.Erfc(value) == 1 - DiffUtils.Erf(value)


def test_logistic_is_bounded_and_centred():
    """A logistic curve is half its maximum at the midpoint."""
    assert DiffUtils.Logistic(0, 0, 1, 2) == pytest.approx(1.0)
    assert 0 < DiffUtils.Logistic(-10) < 0.001
    assert 0.999 < DiffUtils.Logistic(10) < 1


def test_smoothstep_clamps_outside_range():
    """A smoothstep is flat outside its bounds and half way at the centre."""
    assert DiffUtils.Smoothstep(-1, 0, 10) == 0.0
    assert DiffUtils.Smoothstep(11, 0, 10) == 1.0
    assert DiffUtils.Smoothstep(5, 0, 10) == pytest.approx(0.5)


def test_reverse_lerp_clamps():
    """Reverse interpolation stays inside zero and one."""
    assert DiffUtils.ReverseLerp(5, 0, 10) == pytest.approx(0.5)
    assert DiffUtils.ReverseLerp(-5, 0, 10) == 0.0
    assert DiffUtils.ReverseLerp(15, 0, 10) == 1.0


def test_norm_matches_pythagoras():
    """The two-norm of a 3-4 pair is five."""
    assert DiffUtils.Norm(2, 3, 4) == pytest.approx(5.0)


def test_bpm_conversions_round_trip():
    """Converting a tempo to a beat length and back is lossless."""
    assert DiffUtils.MillisecondsToBPM(DiffUtils.BPMToMilliseconds(180)) == pytest.approx(180)


def test_whole_number_powers_are_multiplied_out():
    """A whole exponent up to five multiplies the base out by hand.

    osu! declares two ``Pow`` overloads and the exponent's type picks between
    them. ``x * x * x`` and ``Math.Pow(x, 3)`` disagree in the last bit, and
    that bit reaches the star rating, so ``3`` and ``3.0`` must stay distinct.
    """
    base = 2.037467453190547

    assert DiffUtils.Pow(base, 0) == 1.0
    assert DiffUtils.Pow(base, 1) == base
    assert DiffUtils.Pow(base, 2) == base * base
    assert DiffUtils.Pow(base, 3) == base * base * base
    assert DiffUtils.Pow(base, 4) == base * base * base * base
    assert DiffUtils.Pow(base, 5) == base * base * base * base * base

    assert DiffUtils.Pow(base, 3.0) != DiffUtils.Pow(base, 3)
    assert DiffUtils.Pow(base, 3.0) == math.pow(base, 3.0)


def test_powers_above_five_fall_back_to_pow():
    """Beyond five, osu! has no unrolled case and defers to ``Math.Pow``."""
    base = 1.37
    assert DiffUtils.Pow(base, 6) == math.pow(base, 6)
    assert DiffUtils.Pow(base, 16) == math.pow(base, 16)
