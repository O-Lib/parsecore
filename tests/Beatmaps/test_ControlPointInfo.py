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

from parsecore.Beatmaps.ControlPoints.DifficultyControlPoint import (
    DifficultyControlPoint,
)
from parsecore.Beatmaps.ControlPoints.EffectControlPoint import EffectControlPoint
from parsecore.Beatmaps.ControlPoints.TimingControlPoint import TimingControlPoint
from parsecore.Beatmaps.Legacy.LegacyControlPointInfo import LegacyControlPointInfo


def test_timing_point_lookup_returns_active_point():
    """A lookup returns the last point at or before the given time."""
    info = LegacyControlPointInfo()
    info.Add(0, TimingControlPoint(BeatLength=500))
    info.Add(1000, TimingControlPoint(BeatLength=250))

    assert info.TimingPointAt(0).BPM == 120
    assert info.TimingPointAt(999).BPM == 120
    assert info.TimingPointAt(1000).BPM == 240
    assert info.TimingPointAt(5000).BPM == 240


def test_lookup_before_first_point_falls_back_to_it():
    """A time before every timing point still resolves to the first one."""
    info = LegacyControlPointInfo()
    info.Add(1000, TimingControlPoint(BeatLength=500))
    assert info.TimingPointAt(0).BPM == 120


def test_redundant_points_are_dropped():
    """A point that changes nothing is not stored."""
    info = LegacyControlPointInfo()
    assert info.Add(0, DifficultyControlPoint(SliderVelocity=2.0)) is True
    assert info.Add(100, DifficultyControlPoint(SliderVelocity=2.0)) is False
    assert len(info.DifficultyPoints) == 1


def test_timing_points_are_never_redundant():
    """Two identical timing points are both kept."""
    info = LegacyControlPointInfo()
    info.Add(0, TimingControlPoint(BeatLength=500))
    info.Add(1000, TimingControlPoint(BeatLength=500))
    assert len(info.TimingPoints) == 2


def test_effect_point_defaults_outside_range():
    """Kiai is off before any effect point is declared."""
    info = LegacyControlPointInfo()
    info.Add(500, EffectControlPoint(KiaiMode=True))
    assert info.EffectPointAt(0).KiaiMode is False
    assert info.EffectPointAt(500).KiaiMode is True


def test_beat_length_is_clamped():
    """Beat lengths outside osu!'s accepted range are clamped."""
    assert TimingControlPoint(BeatLength=1e9).BeatLength == 60000.0
    assert TimingControlPoint(BeatLength=0.0).BeatLength == 6.0
