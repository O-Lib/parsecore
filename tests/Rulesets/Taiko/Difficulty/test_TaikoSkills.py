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

from parsecore.Rulesets.Taiko.Difficulty.Evaluators import (
    ColourEvaluator,
    ReadingEvaluator,
    RhythmEvaluator,
    StaminaEvaluator,
)
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Colour import (
    TaikoColourDifficultyPreprocessor,
)
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Rhythm import (
    TaikoRhythmDifficultyPreprocessor,
)
from parsecore.Rulesets.Taiko.Difficulty.Skills.Colour import Colour
from parsecore.Rulesets.Taiko.Difficulty.Skills.Reading import Reading
from parsecore.Rulesets.Taiko.Difficulty.Skills.Rhythm import Rhythm
from parsecore.Rulesets.Taiko.Difficulty.Skills.Stamina import (
    Stamina,
    index_in_mono_streak,
)
from tests.Rulesets.Taiko.Difficulty.conftest import build_difficulty_objects


def _prepared(pattern: str, deltas: list[float] | None = None) -> list:
    """Return difficulty objects with both preprocessors already run."""
    objects = build_difficulty_objects(pattern, deltas=deltas)
    TaikoColourDifficultyPreprocessor.ProcessAndAssign(objects)
    TaikoRhythmDifficultyPreprocessor.ProcessAndAssign(objects)
    return objects


def _run(skill, objects) -> float:
    """Process every object through a skill and return its difficulty."""
    for hit_object in objects:
        skill.Process(hit_object)
    return skill.DifficultyValue()


def test_faster_drumming_costs_more_stamina():
    """The same notes packed closer together demand more of the hands."""
    slow = _prepared("dkdkdkdkdkdk", deltas=[300.0] * 12)
    fast = _prepared("dkdkdkdkdkdk", deltas=[80.0] * 12)

    assert _run(Stamina([]), fast) > _run(Stamina([]), slow)


def test_every_note_carries_a_base_stamina_cost():
    """Even the first note of a beatmap is worth something."""
    objects = _prepared("dkdk")
    assert StaminaEvaluator.EvaluateDifficultyOf(objects[0]) == pytest.approx(0.5)


def test_a_nearby_colour_change_leaves_only_two_fingers():
    """Alternating colours force two-finger play and so cost more stamina.

    A long run of one colour can be spread across eight fingers; switching
    hands every note cannot.
    """
    alternating = _prepared("dkdkdkdkdkdk", deltas=[100.0] * 12)
    single = _prepared("dddddddddddd", deltas=[100.0] * 12)

    assert StaminaEvaluator.EvaluateDifficultyOf(
        alternating[-1]
    ) > StaminaEvaluator.EvaluateDifficultyOf(single[-1])


def test_colour_difficulty_falls_on_the_note_that_opens_a_pattern():
    """Only the first note of a grouping is charged for it."""
    objects = _prepared("ddddkkkkddddkkkk")

    charged = [
        h for h in objects if ColourEvaluator.EvaluateDifficultyOf(h) > 0
    ]
    assert charged, "expected some notes to carry colour difficulty"

    for hit_object in charged:
        colour = hit_object.ColourData
        assert (
            colour.MonoStreak.FirstHitObject is hit_object
            or colour.AlternatingMonoPattern.FirstHitObject is hit_object
            or colour.RepeatingHitPattern.FirstHitObject is hit_object
        )


def test_a_pattern_that_keeps_returning_is_worth_less():
    """A colour pattern the player has just seen is easier than a fresh one."""
    repeated = _prepared("ddkkddkkddkkddkk")
    varied = _prepared("dkkkddddkkddkdkd")

    assert _run(Colour([]), repeated) < _run(Colour([]), varied)


def test_a_steady_rhythm_scores_no_rhythm_difficulty():
    """Rhythm difficulty comes from change, so an even beat is worth nothing."""
    steady = _prepared("dddddddddddd", deltas=[200.0] * 12)
    assert _run(Rhythm([]), steady) == pytest.approx(0.0)


def test_a_changing_rhythm_scores_more_than_a_steady_one():
    """Switching spacing partway through is what rhythm rates."""
    steady = _prepared("dddddddddddd", deltas=[200.0] * 12)
    changing = _prepared(
        "dddddddddddd", deltas=[200.0] * 6 + [125.0] * 3 + [200.0] * 3
    )

    assert _run(Rhythm([]), changing) > _run(Rhythm([]), steady)


def test_reading_rates_scroll_speed_rather_than_layout():
    """A faster-scrolling beatmap is harder to read at the same note spacing."""
    slow = _prepared("dkdkdkdkdkdk", deltas=[200.0] * 12)
    for hit_object in slow:
        hit_object.EffectiveBPM = 120.0
    fast = _prepared("dkdkdkdkdkdk", deltas=[200.0] * 12)
    for hit_object in fast:
        hit_object.EffectiveBPM = 600.0

    assert ReadingEvaluator.EvaluateDifficultyOf(
        fast[0]
    ) > ReadingEvaluator.EvaluateDifficultyOf(slow[0])
    assert _run(Reading([]), fast) > _run(Reading([]), slow)


def test_rhythm_is_gated_by_what_the_hands_can_manage():
    """A rhythm the hands are not straining for keeps little of its difficulty.

    The stamina demand multiplies the rhythm difficulty, so the same rhythm
    change survives almost intact at speed and is cut away when the player has
    time to spare. This is about the gate alone; the group's own length pulls
    the other way, so the finished skill values do not line up this simply.
    """
    change = ([200.0] * 8 + [125.0] * 4) * 4

    def surviving_fraction(scale: float) -> float:
        """Return how much of the raw rhythm difficulty the gate lets through."""
        objects = _prepared("d" * len(change), deltas=[d * scale for d in change])
        skill = Rhythm([])
        raw = sum(RhythmEvaluator.EvaluateDifficultyOf(h) for h in objects)
        gated = sum(skill.StrainValueOf(h) for h in objects)
        assert raw > 0, "expected the rhythm change to be rated at all"
        return gated / raw

    fast = surviving_fraction(0.15)
    ordinary = surviving_fraction(1.0)
    slow = surviving_fraction(5.0)

    assert fast > ordinary > slow
    assert fast > 0.5, "a passage at the limit keeps most of its rhythm"
    assert slow < 0.1, "a passage with time to spare keeps almost none"


def test_a_note_outside_a_colour_run_reports_no_position():
    """Where a note is not in the run it points at, osu! reports minus one."""
    objects = _prepared("dkdkdk")

    hit_object = objects[0]
    assert index_in_mono_streak(hit_object) == 0

    hit_object.ColourData.MonoStreak = objects[-1].ColourData.MonoStreak
    assert index_in_mono_streak(hit_object) == -1


def test_a_spinner_costs_nothing_on_any_skill():
    """Only notes are rated; a swell or roll carries no strain of its own."""
    objects = _prepared("dkdk")

    class _NotAHit:
        pass

    hit_object = objects[-1]
    hit_object.BaseObject = _NotAHit()

    assert StaminaEvaluator.EvaluateDifficultyOf(hit_object) == 0.0
    assert RhythmEvaluator.EvaluateDifficultyOf(hit_object) == 0.0


def test_single_colour_stamina_ignores_the_relief_of_switching_hands():
    """Measuring one colour drops the bonus a long run would otherwise earn."""
    objects = _prepared("dddddddddddddddd", deltas=[100.0] * 16)

    both = _run(Stamina([], single_colour_stamina=False), objects)
    single = _run(Stamina([], single_colour_stamina=True), _prepared(
        "dddddddddddddddd", deltas=[100.0] * 16
    ))

    assert single < both
    assert not math.isnan(single)
