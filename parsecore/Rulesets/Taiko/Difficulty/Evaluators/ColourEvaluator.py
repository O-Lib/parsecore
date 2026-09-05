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

import math

from parsecore.Rulesets.Difficulty.Utils import DiffUtils

# How close two spacing ratios must be to count as the same rhythm.
CONSISTENT_RATIO_THRESHOLD = 0.01

# How far back to look for a steady rhythm.
MAX_OBJECTS_TO_CHECK = 64


def EvaluateDifficultyOf(hit_object) -> float:
    """Return how hard a note's colour pattern is.

    Args:
        hit_object: The difficulty object to rate.
    """
    colour_data = hit_object.ColourData
    difficulty = 0.0

    if (
        colour_data.MonoStreak is not None
        and colour_data.MonoStreak.FirstHitObject is hit_object
    ):
        difficulty += _evaluate_mono_streak_difficulty(colour_data.MonoStreak)

    if (
        colour_data.AlternatingMonoPattern is not None
        and colour_data.AlternatingMonoPattern.FirstHitObject is hit_object
    ):
        difficulty += _evaluate_alternating_mono_pattern_difficulty(
            colour_data.AlternatingMonoPattern
        )

    if (
        colour_data.RepeatingHitPattern is not None
        and colour_data.RepeatingHitPattern.FirstHitObject is hit_object
    ):
        difficulty += _evaluate_repeating_hit_patterns_difficulty(
            colour_data.RepeatingHitPattern
        )

    return difficulty * _consistent_ratio_penalty(hit_object)


def _consistent_ratio_penalty(
    hit_object,
    threshold: float = CONSISTENT_RATIO_THRESHOLD,
    max_objects_to_check: int = MAX_OBJECTS_TO_CHECK,
) -> float:
    """Return how much a steady underlying rhythm eases a colour pattern.

    The walk back stops at the first pair of notes sharing a spacing ratio; a
    pattern laid over an even rhythm is far easier than the same pattern laid
    over a changing one.

    Args:
        hit_object: The difficulty object to look back from.
        threshold: How close two ratios must be to count as the same.
        max_objects_to_check: How far back to walk.

    Returns:
        A multiplier at or below one.
    """
    consistent_ratio_count = 0
    total_ratio_count = 0.0

    recent_ratios: list[float] = []
    current = hit_object
    previous_hit_object = current.Previous(1)

    for _ in range(max_objects_to_check):
        if current.Index <= 1:
            break

        current_ratio = current.RhythmData.Ratio
        previous_ratio = previous_hit_object.RhythmData.Ratio

        recent_ratios.append(current_ratio)

        if abs(1 - current_ratio / previous_ratio) <= threshold:
            consistent_ratio_count += 1
            total_ratio_count += current_ratio
            break

        current = previous_hit_object

    if consistent_ratio_count > 0:
        return 1 - total_ratio_count / (consistent_ratio_count + 1) * 0.80

    if len(recent_ratios) <= 1:
        return 1.0

    average = sum(recent_ratios) / len(recent_ratios)
    max_ratio_deviation = max(abs(r - average) for r in recent_ratios)

    return 0.7 + 0.3 * DiffUtils.Smootherstep(max_ratio_deviation, 0.0, 1.0)


def _evaluate_mono_streak_difficulty(mono_streak) -> float:
    """Return how hard one colour run is, given the pattern it sits in.

    Args:
        mono_streak: The colour run to rate.
    """
    return (
        DiffUtils.LogisticExp(math.e * mono_streak.Index - 2 * math.e)
        * _evaluate_alternating_mono_pattern_difficulty(mono_streak.Parent)
        * 0.5
    )


def _evaluate_alternating_mono_pattern_difficulty(alternating_mono_pattern) -> float:
    """Return how hard one alternating pattern is, given its group.

    Args:
        alternating_mono_pattern: The pattern to rate.
    """
    return DiffUtils.LogisticExp(
        math.e * alternating_mono_pattern.Index - 2 * math.e
    ) * _evaluate_repeating_hit_patterns_difficulty(alternating_mono_pattern.Parent)


def _evaluate_repeating_hit_patterns_difficulty(repeating_hit_pattern) -> float:
    """Return how hard a pattern group is, given how recently it recurred.

    Args:
        repeating_hit_pattern: The group to rate.
    """
    return 2 * (
        1
        - DiffUtils.LogisticExp(
            math.e * repeating_hit_pattern.RepetitionInterval - 2 * math.e
        )
    )
