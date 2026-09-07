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

from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    CalculateDifficultyPeppyStars,
)
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.SliderTick import SliderTick
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner

# What a slider head, tail or repeat was worth in osu!stable.
BIG_TICK_SCORE = 30.0

# What a slider tick was worth.
SMALL_TICK_SCORE = 10.0

# What one spin and one bonus spin were worth.
SPIN_SCORE = 100
BONUS_SPIN_SCORE = 1000

# The fastest and slowest a spinner can be turned, in rotations per second.
MAXIMUM_ROTATIONS_PER_SECOND = 477.0 / 60
MINIMUM_ROTATIONS_PER_SECOND = 3


def CalculateNestedScorePerObject(beatmap, object_count: int) -> float:
    """Return the average score an object carries through its ticks.

    Args:
        beatmap: The beatmap as osu! plays it.
        object_count: How many objects were judged.
    """
    amount_of_big_ticks = 0
    amount_of_small_ticks = 0
    spinner_score = 0.0

    for hit_object in beatmap.HitObjects:
        if isinstance(hit_object, Slider):
            # One for the head, one for the tail, and one per repeat.
            amount_of_big_ticks += 2 + hit_object.RepeatCount
            amount_of_small_ticks += sum(
                1 for n in hit_object.NestedHitObjects if isinstance(n, SliderTick)
            )
        elif isinstance(hit_object, Spinner):
            spinner_score += _calculate_spinner_score(hit_object)

    slider_score = (
        amount_of_big_ticks * BIG_TICK_SCORE + amount_of_small_ticks * SMALL_TICK_SCORE
    )

    return (slider_score + spinner_score) / object_count


def _calculate_spinner_score(spinner) -> float:
    """Return what a spinner is worth on an average play, not a perfect one.

    Args:
        spinner: The spinner to score.
    """
    seconds_duration = spinner.Duration / 1000

    total_half_spins_possible = int(
        seconds_duration * MAXIMUM_ROTATIONS_PER_SECOND * 2
    )
    half_spins_required_for_completion = int(
        seconds_duration * MINIMUM_ROTATIONS_PER_SECOND
    )
    half_spins_required_before_bonus = half_spins_required_for_completion + 3

    full_spins = total_half_spins_possible // 2

    score = SPIN_SCORE * full_spins

    bonus_spins = (total_half_spins_possible - half_spins_required_before_bonus) // 2

    # Fewer bonus spins are counted than are possible, so that this stands for
    # a typical play rather than the best one anybody could manage.
    bonus_spins = max(0, bonus_spins - full_spins // 2)

    score += BONUS_SPIN_SCORE * bonus_spins

    return float(score)


def CalculateDifficultyPeppyStarsFor(beatmap) -> int:
    """Return the multiplier osu!stable scaled a beatmap's score by.

    Args:
        beatmap: The beatmap as it was decoded.
    """
    object_count = len(beatmap.HitObjects)
    drain_length = 0

    if object_count > 0:
        break_length = sum(
            int(round(b.EndTime)) - int(round(b.StartTime)) for b in beatmap.Breaks
        )
        # osu! divides two whole numbers here, truncating towards zero.
        drain_length = int(
            (
                int(round(beatmap.HitObjects[-1].StartTime))
                - int(round(beatmap.HitObjects[0].StartTime))
                - break_length
            )
            / 1000
        )

    return CalculateDifficultyPeppyStars(
        beatmap.Difficulty, object_count, drain_length
    )
