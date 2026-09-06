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

from parsecore.Rulesets.Objects.PathControlPoint import PathControlPoint
from parsecore.Rulesets.Objects.SliderPath import SliderPath
from parsecore.Rulesets.Objects.Types.PathType import BEZIER, LINEAR, PERFECT_CURVE
from parsecore.Utils.Vector2 import Vector2


def test_linear_path_length():
    """A straight path is exactly as long as the distance between its ends."""
    path = SliderPath([PathControlPoint(Vector2(0, 0), LINEAR),
                       PathControlPoint(Vector2(100, 0))])
    assert path.Distance == pytest.approx(100.0)


def test_position_at_midpoint():
    """Half way along a straight path is the midpoint."""
    path = SliderPath([PathControlPoint(Vector2(0, 0), LINEAR),
                       PathControlPoint(Vector2(100, 0))])
    assert path.PositionAt(0.5).X == pytest.approx(50.0)
    assert path.PositionAt(0.5).Y == pytest.approx(0.0)


def test_perfect_curve_approximates_semicircle():
    """Three points forming a semicircle give a length close to pi * r."""
    path = SliderPath([PathControlPoint(Vector2(0, 0), PERFECT_CURVE),
                       PathControlPoint(Vector2(50, 50)),
                       PathControlPoint(Vector2(100, 0))])
    assert path.Distance == pytest.approx(math.pi * 50, rel=1e-3)


def test_expected_distance_shortens_path():
    """A declared distance shorter than the curve trims the path."""
    path = SliderPath([PathControlPoint(Vector2(0, 0), LINEAR),
                       PathControlPoint(Vector2(100, 0))],
                      expected_distance=50.0)
    assert path.Distance == pytest.approx(50.0)
    assert path.PositionAt(1.0).X == pytest.approx(50.0)


def test_bezier_is_shorter_than_control_polygon():
    """A bezier curve is shorter than the polygon through its control points."""
    path = SliderPath([PathControlPoint(Vector2(0, 0), BEZIER),
                       PathControlPoint(Vector2(50, 100)),
                       PathControlPoint(Vector2(100, 0))])
    polygon = math.hypot(50, 100) * 2
    assert 0 < path.Distance < polygon


def test_empty_path_has_no_length():
    """A path without control points has zero length."""
    assert SliderPath().Distance == 0.0


def test_path_ending_on_a_repeat_is_never_extended():
    """A path that ends on a repeated control point is not stretched out.

    Only the seam between two segments is closed up, so such a path ends on two
    coincident points, and that is what tells the length calculation to leave
    the stated distance alone. Shortening still works; only lengthening is
    refused.
    """
    def path(expected):
        return SliderPath(
            [
                PathControlPoint(Vector2(0, 0), LINEAR),
                PathControlPoint(Vector2(100, 0), LINEAR),
                PathControlPoint(Vector2(100, 0)),
            ],
            expected_distance=expected,
        )

    assert path(180.0).Distance == pytest.approx(100.0)
    assert path(40.0).Distance == pytest.approx(40.0)
