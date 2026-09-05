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

import pytest

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Beatmaps.ControlPoints.ControlPointInfo import ControlPointInfo
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    CalculateScaleFromCircleSize,
)
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle
from parsecore.Utils.Vector2 import Vector2, f32


def test_vector_components_are_single_precision():
    """Both components are narrowed when a vector is built."""
    v = Vector2(0.1, 0.2)
    assert v.X == f32(0.1)
    assert v.Y == f32(0.2)


def test_length_narrows_each_product_separately():
    """Each squared term is narrowed before they are summed, as osu! does."""
    v = Vector2(0.1, 0.2)
    expected = f32((f32(f32(v.X * v.X) + f32(v.Y * v.Y))) ** 0.5)
    assert v.length() == pytest.approx(expected, abs=0.0)


def test_dot_narrows_each_product_separately():
    """The dot product is a single-precision expression."""
    a, b = Vector2(0.1, 0.2), Vector2(0.3, 0.4)
    assert Vector2.dot(a, b) == f32(f32(a.X * b.X) + f32(a.Y * b.Y))


def test_scale_is_narrowed_at_each_step():
    """The circle-size scale rounds at every step, not just at the end."""
    for circle_size in (0.0, 3.5, 4.0, 5.0, 7.3, 10.0):
        inner = f32(1.0 - f32(0.7) * BeatmapDifficulty.DifficultyRange(circle_size))
        expected = f32(f32(inner / 2.0) * f32(1.00041))
        assert CalculateScaleFromCircleSize(circle_size, True) == expected


def test_radius_stays_single_precision():
    """An object's radius is a single-precision value."""
    circle = HitCircle()
    circle.ApplyDefaults(ControlPointInfo(), BeatmapDifficulty(CircleSize=4))
    assert circle.Radius == f32(circle.Radius)


def test_known_radius_for_circle_size_five():
    """Circle size five still gives osu!'s documented radius."""
    circle = HitCircle()
    circle.ApplyDefaults(ControlPointInfo(), BeatmapDifficulty(CircleSize=5))
    assert circle.Radius == pytest.approx(32.0, abs=0.05)
