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
from parsecore.Rulesets.Taiko.Objects.Hit import Hit

# How close two spacings must be before a repeat is penalised.
REPEATED_INTERVAL_THRESHOLD = 0.1

# What a repeated spacing is worth compared to a fresh one.
REPEATED_INTERVAL_PENALTY = 0.80

# How many notes at one spacing stop the short-interval penalty applying.
SHORT_INTERVAL_NOTE_LIMIT = 6


def EvaluateDifficultyOf(hit_object) -> float:
    """Return how hard a note's rhythm is.

    Args:
        hit_object: The difficulty object to rate.
    """
    if not isinstance(hit_object.BaseObject, Hit):
        return 0.0

    rhythm_data = hit_object.RhythmData
    hit_window = hit_object.HitWindowGreat

    same_rhythm = 0.0
    same_pattern = 0.0
    interval_penalty = 0.0
    gap_penalty = 0.0

    rhythm_group = rhythm_data.SameRhythmGroupedHitObjects
    if rhythm_group is not None and rhythm_group.FirstHitObject is hit_object:
        same_rhythm += 10.0 * _evaluate_rhythm_group(rhythm_group, hit_window)
        interval_penalty = _repeated_interval_penalty(rhythm_group, hit_window)
        gap_penalty = _long_gap_penalty(rhythm_group.Previous)

    pattern_group = rhythm_data.SamePatternsGroupedHitObjects
    if pattern_group is not None and pattern_group.FirstHitObject is hit_object:
        same_pattern += 1.15 * _ratio_difficulty(pattern_group.IntervalRatio)

    return max(same_rhythm, same_pattern) * interval_penalty * gap_penalty


def _evaluate_rhythm_group(rhythm_group, hit_window: float) -> float:
    """Return how hard one steady run of notes is.

    Args:
        rhythm_group: The run of evenly spaced notes.
        hit_window: How much timing slack the beatmap allows.
    """
    interval_difficulty = _ratio_difficulty(rhythm_group.HitObjectIntervalRatio)
    previous_interval = (
        rhythm_group.Previous.HitObjectInterval if rhythm_group.Previous else None
    )

    interval_difficulty *= _repeated_interval_penalty(rhythm_group, hit_window)

    if previous_interval is not None and len(rhythm_group.HitObjects) > 1:
        # A run that lasts longer than the previous spacing would suggest has
        # already been read by the time it ends.
        expected_duration = previous_interval * len(rhythm_group.HitObjects)
        duration_difference = rhythm_group.Duration - expected_duration

        if duration_difference > 0:
            interval_difficulty *= DiffUtils.Logistic(
                duration_difference / hit_window,
                midpoint_offset=0.35,
                multiplier=2,
                max_value=1,
            )

    interval_difficulty *= DiffUtils.Logistic(
        rhythm_group.Duration / hit_window,
        midpoint_offset=0.3,
        multiplier=2,
        max_value=1,
    )

    return DiffUtils.Pow(interval_difficulty, 0.75)


def _repeated_interval_penalty(
    rhythm_group, hit_window: float, threshold: float = REPEATED_INTERVAL_THRESHOLD
) -> float:
    """Return how much a spacing the player has already met is discounted.

    Args:
        rhythm_group: The run of evenly spaced notes.
        hit_window: How much timing slack the beatmap allows.
        threshold: How close two spacings must be to count as repeated.
    """
    long_interval_penalty = _same_interval(rhythm_group, 3, threshold)

    # Six notes at one spacing is long enough that repeating it is no relief.
    short_interval_penalty = (
        _same_interval(rhythm_group, 4, threshold)
        if len(rhythm_group.HitObjects) < SHORT_INTERVAL_NOTE_LIMIT
        else 1.0
    )

    duration_penalty = max(1 - rhythm_group.Duration * 2 / hit_window, 0.5)
    return min(long_interval_penalty, short_interval_penalty) * duration_penalty


def _same_interval(start_group, interval_count: int, threshold: float) -> float:
    """Return whether any two of the last few spacings match.

    Args:
        start_group: The run to look back from.
        interval_count: How many runs back to gather.
        threshold: How close two spacings must be to count as repeated.

    Returns:
        The penalty, or one where nothing repeated.
    """
    intervals: list[float] = []
    current = start_group

    for _ in range(interval_count):
        if current is None:
            break
        if current.HitObjectInterval is not None:
            intervals.append(current.HitObjectInterval)
        current = current.Previous

    if len(intervals) < interval_count:
        return 1.0

    for i in range(len(intervals)):
        for j in range(i + 1, len(intervals)):
            if abs(1 - intervals[i] / intervals[j]) <= threshold:
                return REPEATED_INTERVAL_PENALTY

    return 1.0


def _long_gap_penalty(previous) -> float:
    """Return how much a pause before a short run eases it.

    Args:
        previous: The run before the one being rated, if any.
    """
    if previous is None:
        return 1.0

    gap_interval = previous.FirstHitObject.DeltaTime
    rhythm_interval = (
        previous.HitObjectInterval
        if previous.HitObjectInterval is not None
        else gap_interval
    )
    rhythm_length = len(previous.HitObjects)

    gap_ratio = gap_interval / max(rhythm_interval, 1)
    gap_factor = DiffUtils.Logistic(gap_ratio, 1.75, 20)

    length_factor = DiffUtils.ReverseLerp(rhythm_length, 8, 2)

    return 1.0 - 0.75 * gap_factor * length_factor


def _ratio_difficulty(ratio: float, terms: int = 8) -> float:
    """Return how hard a spacing ratio is to land.

    A ratio near a simple fraction is easy to feel; the sum of cosine terms
    below dips at each of those, so awkward ratios in between score highest.

    Args:
        ratio: How this spacing compares to the one before it.
        terms: How many fractions to test against.
    """
    difficulty = 0.0

    # Anything infinite, zero or not a number is treated as no ratio at all.
    ratio = ratio if _is_normal(ratio) else 0.0

    for i in range(1, terms + 1):
        difficulty += _term_penalty(ratio, i, 4.0, 1.0)

    difficulty += terms / (1 + ratio)
    difficulty += DiffUtils.BellCurve(ratio, 1, 0.5)
    difficulty -= DiffUtils.BellCurve(ratio, 1, 0.3)

    difficulty = max(difficulty, 0.0)
    return difficulty / math.sqrt(8)


def _term_penalty(
    ratio: float, denominator: int, power: float, multiplier: float
) -> float:
    """Return how far a ratio sits from one simple fraction.

    Args:
        ratio: The spacing ratio.
        denominator: Which fraction to test against.
        power: How sharply the dip narrows.
        multiplier: How deep the dip goes.
    """
    return -multiplier * DiffUtils.Pow(math.cos(denominator * math.pi * ratio), power)


def _is_normal(value: float) -> bool:
    """Return whether a value is finite, non-zero and not subnormal.

    Args:
        value: The value to test.
    """
    return math.isfinite(value) and abs(value) >= 2.2250738585072014e-308
