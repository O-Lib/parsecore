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
from parsecore.Beatmaps.ControlPoints.TimingControlPoint import TimingControlPoint
from parsecore.Beatmaps.Formats.LegacyBeatmapDecoder import LegacyBeatmapDecoder
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    GetPrecisionAdjustedBeatLength,
)
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapConverter import OsuBeatmapConverter
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapProcessor import OsuBeatmapProcessor
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle
from parsecore.Rulesets.Osu.Objects.Slider import Slider

HEADER = (
    "osu file format v14\n"
    "[General]\nMode: 0\nStackLeniency: 0.7\n"
    "[Difficulty]\nCircleSize:4\nApproachRate:9\nOverallDifficulty:8\n"
    "SliderMultiplier:1.6\nSliderTickRate:2\n"
    "[TimingPoints]\n0,300,4,2,0,60,1,0\n"
)


def _playable(hit_objects: str, extra: str = ""):
    """Decode and run a beatmap through the osu! conversion pipeline."""
    decoded = LegacyBeatmapDecoder.FromText(
        HEADER + extra + "[HitObjects]\n" + hit_objects
    )
    return WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor
    )


def test_stack_height_reaches_nested_objects():
    """Stacking a slider moves its ticks, repeats and ends with it.

    osu! propagates the stack height through a bindable. Without it a stacked
    slider's cursor path is measured from unshifted positions, and its aim
    difficulty comes out too high.
    """
    playable = _playable("0,0,1000,2,0,L|200:0,1,160\n")
    slider = playable.HitObjects[0]
    assert isinstance(slider, Slider)
    assert slider.NestedHitObjects, "expected the slider to nest objects"

    slider.StackHeight = 3

    for nested in slider.NestedHitObjects:
        assert nested.StackHeight == 3


def test_preempt_time_is_a_whole_number():
    """osu! truncates the preempt window to whole milliseconds."""
    circle = HitCircle()
    circle.ApplyDefaults(ControlPointInfo(), BeatmapDifficulty(ApproachRate=9.3))
    assert circle.TimePreempt == int(circle.TimePreempt)


def test_difficulty_values_are_clamped_after_parsing():
    """Values outside osu!'s accepted ranges are pulled back into them."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n[General]\nMode: 0\n"
        "[Difficulty]\nHPDrainRate:20\nCircleSize:-5\nOverallDifficulty:99\n"
        "ApproachRate:-3\nSliderMultiplier:9\nSliderTickRate:0.1\n"
        "[HitObjects]\n0,0,1000,1,0\n"
    )
    difficulty = beatmap.Difficulty

    assert difficulty.DrainRate == 10.0
    assert difficulty.CircleSize == 0.0
    assert difficulty.OverallDifficulty == 10.0
    assert difficulty.ApproachRate == 0.0
    assert difficulty.SliderMultiplier == 3.6
    assert difficulty.SliderTickRate == 0.5


def test_first_object_after_a_break_starts_a_combo():
    """A break forces a new combo on the object that follows it."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n[General]\nMode: 0\n"
        "[Events]\n2,2000,4000\n"
        "[HitObjects]\n"
        "100,100,1000,1,0\n"
        "200,100,5000,1,0\n"
    )
    assert beatmap.HitObjects[1].NewCombo is True


def test_slider_velocity_uses_a_precision_adjusted_beat_length():
    """The beat length is round-tripped through single precision.

    osu! recovers the negative beat length from the slider velocity, narrows it
    to a ``float`` and multiplies back. Skipping that keeps more precision than
    the game has and shifts every tick.
    """
    timing_point = TimingControlPoint(BeatLength=346.820809248555)

    class _HasVelocity:
        SliderVelocityMultiplier = 0.7500000000000019

    adjusted = GetPrecisionAdjustedBeatLength(_HasVelocity(), timing_point, "osu")

    naive = timing_point.BeatLength * (4 / 3)
    assert adjusted != naive
    assert adjusted == pytest.approx(naive, rel=1e-6)


def test_slider_duration_is_derived_by_subtraction():
    """Duration is the end time minus the start time, as osu! computes it."""
    playable = _playable("0,0,100000,2,0,L|200:0,1,160\n")
    slider = playable.HitObjects[0]
    assert isinstance(slider, Slider)
    assert slider.Duration == slider.EndTime - slider.StartTime


def test_unknown_ruleset_is_rejected_for_beat_length():
    """Only the four legacy rulesets have a precision-adjusted beat length."""
    class _HasVelocity:
        SliderVelocityMultiplier = 1.0

    with pytest.raises(ValueError):
        GetPrecisionAdjustedBeatLength(
            _HasVelocity(), TimingControlPoint(), "not-a-ruleset"
        )


def test_old_stacking_uses_the_far_end_of_a_slider():
    """Before format v6, a slider stacks by where its path ends.

    A slider that slides back finishes where it started, so its end position is
    of no use here: it is the far end of the path that the objects after it
    stack against. osu! reads that end directly from the path, and an object
    sitting there is pushed down and right rather than up and left.
    """
    old = (
        "osu file format v5\n"
        "[General]\nMode: 0\nStackLeniency: 0.7\n"
        "[Difficulty]\nCircleSize:4\nApproachRate:9\nOverallDifficulty:8\n"
        "SliderMultiplier:1.6\nSliderTickRate:2\n"
        "[TimingPoints]\n0,300,4,2,0,60,1,0\n"
        "[HitObjects]\n"
        "192,288,1000,2,0,B|344:288,2,140\n"
        "332,288,1700,1,0\n"
    )
    decoded = LegacyBeatmapDecoder.FromText(old)
    assert decoded.BeatmapInfo.BeatmapVersion == 5

    beatmap = WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor
    )
    circle = beatmap.HitObjects[1]
    assert circle.StackHeight == -1
    assert circle.StackedPosition.X > circle.Position.X
    assert circle.StackedPosition.Y > circle.Position.Y


def test_spinner_and_its_ticks_are_not_judged_on_timing():
    """Neither a spinner nor its spins carry a judgement window.

    A difficulty object takes its window from the object itself, or from the
    first nested one that has any. A spin is judged on having happened, not on
    when, so both must report none: otherwise a spinner is credited with the
    beatmap's timing window and the reading and tapping values around it move.
    """
    beatmap = _playable("256,192,1000,12,0,4000\n")
    spinner = beatmap.HitObjects[0]

    assert not spinner.HitWindows.GetRanges()
    assert spinner.NestedHitObjects
    assert all(not n.HitWindows.GetRanges() for n in spinner.NestedHitObjects)
