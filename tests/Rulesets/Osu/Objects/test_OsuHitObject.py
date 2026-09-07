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
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle


def _applied(circle_size: float = 5.0, approach_rate: float = 5.0):
    """Return a hit circle with defaults applied at a given difficulty."""
    circle = HitCircle()
    circle.ApplyDefaults(
        ControlPointInfo(),
        BeatmapDifficulty(CircleSize=circle_size, ApproachRate=approach_rate),
    )
    return circle


def test_circle_size_five_gives_the_known_radius():
    """Circle size five gives osu!'s documented radius of about 32."""
    assert _applied(circle_size=5).Radius == pytest.approx(32.0, abs=0.05)


def test_larger_circle_size_means_smaller_circles():
    """A higher circle size shrinks the objects."""
    assert _applied(circle_size=7).Radius < _applied(circle_size=3).Radius


def test_approach_rate_preempt_values():
    """Preempt time matches osu!'s approach rate mapping."""
    assert _applied(approach_rate=5).TimePreempt == pytest.approx(1200.0)
    assert _applied(approach_rate=7).TimePreempt == pytest.approx(900.0)
    assert _applied(approach_rate=10).TimePreempt == pytest.approx(450.0)
    assert _applied(approach_rate=0).TimePreempt == pytest.approx(1800.0)


def test_fade_in_shrinks_with_preempt():
    """Fade-in never outlasts the preempt window at high approach rates."""
    assert _applied(approach_rate=5).TimeFadeIn == pytest.approx(400.0)
    assert _applied(approach_rate=10).TimeFadeIn == pytest.approx(400.0)


def test_stack_offset_shifts_the_position():
    """Stacking moves an object up and to the left."""
    circle = _applied()
    circle.StackHeight = 2
    assert circle.StackedPosition.X < circle.Position.X
    assert circle.StackedPosition.Y < circle.Position.Y
