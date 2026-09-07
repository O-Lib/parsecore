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

from parsecore.Utils.PathApproximator import (
    CIRCULAR_ARC_TOLERANCE,
    circular_arc_properties,
    circular_arc_to_piecewise_linear,
)
from parsecore.Utils.Vector2 import Vector2, f32

WIDE_ARC = [Vector2(0, 0), Vector2(92, -16), Vector2(192, -20)]


def test_tolerance_is_single_precision():
    """The tolerance is a single-precision value, not the double 0.1."""
    assert CIRCULAR_ARC_TOLERANCE == f32(0.1)
    assert CIRCULAR_ARC_TOLERANCE != 0.1


def test_wide_arc_properties():
    """A near-straight arc still describes a circle, and a large one."""
    properties = circular_arc_properties(WIDE_ARC)
    assert properties.IsValid
    assert properties.Radius == 732.165771484375
    assert properties.ThetaRange == 0.26442425920129065


def test_wide_arc_point_count():
    """The point count is decided at single precision.

    The number of points follows from how far the arc may bend between two of
    them. Both the tolerance and the radius are single precision, so the whole
    fraction is worked out there. Here the result lands either side of eight
    depending on that rounding, and the game gets nine points.
    """
    points = circular_arc_to_piecewise_linear(WIDE_ARC)
    assert len(points) == 9


def test_wide_arc_points():
    """Every point along that arc matches the game, to the last bit."""
    points = circular_arc_to_piecewise_linear(WIDE_ARC)
    expected = [
        (0.0, 0.0),
        (23.618682861328125, -5.2686767578125),
        (47.398590087890625, -9.75390625),
        (71.31372833251953, -13.4508056640625),
        (95.33797454833984, -16.35546875),
        (119.44508361816406, -18.4644775390625),
        (143.60873413085938, -19.7757568359375),
        (167.80252075195312, -20.28778076171875),
        (192.0, -20.0),
    ]
    assert [(float(p.X), float(p.Y)) for p in points] == expected


def test_collinear_points_fall_back_to_bezier():
    """Three points in a line describe no circle, so a bezier is used."""
    points = circular_arc_to_piecewise_linear(
        [Vector2(0, 0), Vector2(50, 0), Vector2(100, 0)]
    )
    assert points
    assert points[-1].X == pytest.approx(100.0)
