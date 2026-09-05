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

from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Colour import (
    TaikoColourDifficultyPreprocessor,
)
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Rhythm import (
    TaikoRhythmDifficultyPreprocessor,
)
from parsecore.Rulesets.Taiko.Difficulty.Utils import DeltaTimeNormaliser
from parsecore.Rulesets.Taiko.Difficulty.Utils.IntervalGroupingUtils import (
    GroupByInterval,
)
from parsecore.Rulesets.Taiko.Objects.HitType import HitType
from tests.Rulesets.Taiko.Difficulty.conftest import build_difficulty_objects


class _Spaced:
    """A stand-in carrying nothing but a spacing."""

    def __init__(self, interval: float) -> None:
        """Record the spacing.

        Args:
            interval: The gap to whatever came before.
        """
        self.Interval = interval

    def __repr__(self) -> str:
        """Return an unambiguous representation."""
        return f"_Spaced({self.Interval})"


def test_a_steady_run_forms_one_group():
    """Objects at the same spacing stay together."""
    groups = GroupByInterval([_Spaced(100) for _ in range(5)])
    assert len(groups) == 1
    assert len(groups[0]) == 5


def test_spacings_within_the_margin_still_count_as_steady():
    """A few milliseconds of snapping error do not split a rhythm."""
    groups = GroupByInterval([_Spaced(i) for i in (100, 102, 104, 101)])
    assert len(groups) == 1


def test_a_widening_gap_splits_between_the_two_spacings():
    """Slowing down ends the fast group after its last fast object."""
    groups = GroupByInterval([_Spaced(i) for i in (100, 100, 100, 400, 400, 400)])
    assert [len(g) for g in groups] == [3, 3]


def test_a_narrowing_gap_splits_one_object_earlier():
    """Speeding up hands the object carrying the last long gap to the new group.

    An object's interval is the gap before it, so the object that still shows
    the slow spacing opens the fast group rather than closing the slow one.
    """
    groups = GroupByInterval([_Spaced(i) for i in (400, 400, 400, 100, 100, 100)])
    assert [len(g) for g in groups] == [2, 4]


def test_near_identical_spacings_are_pulled_onto_one_value():
    """The normaliser reports a neighbourhood's median, not each raw spacing."""
    class _Delta:
        def __init__(self, delta):
            self.DeltaTime = delta

    objects = [_Delta(d) for d in (100.0, 102.0, 104.0, 300.0)]
    normalised = DeltaTimeNormaliser.Normalise(objects, 5.0)

    assert normalised[objects[0]] == 102.0
    assert normalised[objects[1]] == 102.0
    assert normalised[objects[2]] == 102.0
    assert normalised[objects[3]] == 300.0


def test_colour_runs_break_where_the_drum_side_changes():
    """A run of one colour ends as soon as the other colour appears."""
    objects = build_difficulty_objects("ddddkkkd")

    TaikoColourDifficultyPreprocessor.ProcessAndAssign(objects)

    run_lengths = []
    for hit_object in objects:
        streak = hit_object.ColourData.MonoStreak
        if not run_lengths or streak is not run_lengths[-1][0]:
            run_lengths.append((streak, streak.RunLength))

    assert [length for _, length in run_lengths] == [2, 3, 1]
    assert run_lengths[0][0].HitType == HitType.Centre
    assert run_lengths[1][0].HitType == HitType.Rim


def test_a_repeated_pattern_records_how_long_ago_it_appeared():
    """A pattern seen recently is marked as a repeat; a fresh one is not."""
    repeated = build_difficulty_objects("dkkdddkkkkd")
    TaikoColourDifficultyPreprocessor.ProcessAndAssign(repeated)

    intervals = {
        h.ColourData.RepeatingHitPattern.RepetitionInterval for h in repeated
    }
    assert intervals, "expected patterns to be assigned"
    assert all(1 <= i <= 17 for i in intervals)
    assert any(i <= 16 for i in intervals), "a returning pattern must be seen"


def test_a_pattern_that_never_recurs_is_left_past_the_maximum():
    """Where no earlier group plays the same way, the interval stays at 17."""
    objects = build_difficulty_objects("ddkkkddd")
    TaikoColourDifficultyPreprocessor.ProcessAndAssign(objects)

    first = objects[0].ColourData.RepeatingHitPattern
    assert first.Previous is None
    assert first.RepetitionInterval == 17


def test_spacing_ratios_snap_to_musical_values():
    """A ratio is reported as the nearest one a mapper would have meant."""
    objects = build_difficulty_objects(
        "dddddd", deltas=[200, 200, 200, 100, 100, 100]
    )
    ratios = [h.RhythmData.Ratio for h in objects]

    assert all(r in (1.0, 0.5, 2.0, 1 / 3, 3.0, 1.5, 2 / 3, 1.25, 0.8) for r in ratios)
    assert ratios == [1.0, 0.5, 1.0, 1.0]


def test_every_note_lands_in_a_rhythm_and_a_pattern_group():
    """After preprocessing no note is left without its groupings."""
    objects = build_difficulty_objects("dkdkdkdk")
    TaikoRhythmDifficultyPreprocessor.ProcessAndAssign(objects)

    for hit_object in objects:
        rhythm = hit_object.RhythmData
        assert rhythm.SameRhythmGroupedHitObjects is not None
        assert rhythm.SamePatternsGroupedHitObjects is not None

    first_group = objects[0].RhythmData.SameRhythmGroupedHitObjects
    assert first_group.Previous is None
    assert math.isinf(first_group.Interval)
    assert first_group.HitObjectIntervalRatio == pytest.approx(1.0)
