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
from parsecore.Rulesets.Osu.Difficulty.Preprocessing.OsuDifficultyHitObject import (
    MIN_DELTA_TIME,
)
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner

HISTORY_TIME_MAX = 5 * 1000
HISTORY_OBJECTS_MAX = 32
RHYTHM_OVERALL_MULTIPLIER = 0.95
RHYTHM_RATIO_DIFFICULTY_MULTIPLIER = 26.0

# Stands in for C#'s int.MaxValue, used as "no delta yet".
_INT_MAX = 2147483647

# A delta time is never taken as exactly zero.
DELTA_MIN_VALUE = 1e-7


class Island:
    """A run of consecutive objects sharing the same spacing."""

    def __init__(self, delta: int) -> None:
        """Create an island at a given spacing.

        Args:
            delta: The spacing of every object in the island.
        """
        self.Delta = (
            delta if delta == _INT_MAX else max(delta, int(MIN_DELTA_TIME))
        )
        self.DeltaCount = 1
        self.Occurrences = 1

    def AddDelta(self, delta: int) -> None:
        """Extend the island by one object.

        Args:
            delta: The spacing of the object being added.
        """
        if self.Delta == _INT_MAX:
            self.Delta = max(delta, int(MIN_DELTA_TIME))
        self.DeltaCount += 1

    def IsSimilarPolarity(self, other: Island, epsilon: float) -> bool:
        """Return whether two islands share spacing and odd/even length.

        Args:
            other: The island to compare against.
            epsilon: How far two spacings may differ and still match.
        """
        # Islands of a single object carry no polarity.
        if self.DeltaCount <= 1 or other.DeltaCount <= 1:
            return False
        return (
            abs(self.Delta - other.Delta) < epsilon
            and self.DeltaCount % 2 == other.DeltaCount % 2
        )

    def AlmostEquals(self, other: Island, epsilon: float) -> bool:
        """Return whether two islands are the same shape.

        Args:
            other: The island to compare against.
            epsilon: How far two spacings may differ and still match.
        """
        return (
            abs(self.Delta - other.Delta) < epsilon
            and self.DeltaCount == other.DeltaCount
        )

    def __repr__(self) -> str:
        """Return the island as ``delta x count``."""
        return f"{self.Delta}x{self.DeltaCount}"


def _get_effective_difficulty(delta_difference_ratio: float) -> float:
    """Return how much a spacing ratio is worth.

    Ratios that are whole multiples of each other (100 ms against 200 ms) are
    easy to read, so only the fractional part earns difficulty.

    Args:
        delta_difference_ratio: The ratio between two spacings.
    """
    delta_difference_fraction = delta_difference_ratio - math.trunc(
        delta_difference_ratio
    )
    return 1.0 + RHYTHM_RATIO_DIFFICULTY_MULTIPLIER * min(
        0.5, DiffUtils.SmoothstepBellCurve(delta_difference_fraction)
    )


def EvaluateDifficultyOf(current) -> float:
    """Return a rhythm multiplier for the tap difficulty of ``current``.

    Args:
        current: The object being evaluated.

    Returns:
        A multiplier at or above one, applied to the object's strain.
    """
    if isinstance(current.BaseObject, Spinner):
        return 0.0

    rhythm_complexity_sum = 0.0
    delta_difference_epsilon = current.HitWindowGreat * 0.3

    island = Island(_INT_MAX)
    previous_island = Island(_INT_MAX)
    islands: list[Island] = []

    # The difficulty an island started at, used to reward tighter rhythms.
    start_difficulty = 0.0
    first_delta_switch = False

    historical_note_count = min(current.Index, HISTORY_OBJECTS_MAX)

    rhythm_start = 0
    while (
        rhythm_start < historical_note_count - 2
        and current.StartTime - current.Previous(rhythm_start).StartTime
        < HISTORY_TIME_MAX
    ):
        rhythm_start += 1

    prev_obj = current.Previous(rhythm_start)
    prev_prev_obj = current.Previous(rhythm_start + 1)

    # Walk forward from the furthest object back to the current one.
    for i in range(rhythm_start, 0, -1):
        curr_obj = current.Previous(i - 1)
        if isinstance(curr_obj.BaseObject, Spinner):
            continue

        # Objects fade from the history by both time and count; whichever
        # limit bites first wins.
        time_decay = (
            HISTORY_TIME_MAX - (current.StartTime - curr_obj.StartTime)
        ) / HISTORY_TIME_MAX
        note_decay = (historical_note_count - i) / historical_note_count
        curr_historical_decay = min(note_decay, time_decay)

        curr_delta = max(curr_obj.DeltaTime, DELTA_MIN_VALUE)
        prev_delta = max(prev_obj.DeltaTime, DELTA_MIN_VALUE)
        delta_difference = abs(prev_delta - curr_delta)

        if island.Delta == _INT_MAX:
            island = Island(int(curr_delta))

        delta_difference_ratio = max(prev_delta, curr_delta) / min(
            prev_delta, curr_delta
        )

        # A very large ratio is easy to read, so the bonus is reduced.
        difference_multiplier = min(max(2.0 - delta_difference_ratio / 8.0, 0.0), 1.0)
        window_penalty = min(
            max(
                (delta_difference - delta_difference_epsilon)
                / delta_difference_epsilon,
                0.0,
            ),
            1.0,
        )

        effective_difficulty = (
            _get_effective_difficulty(delta_difference_ratio)
            * window_penalty
            * difference_multiplier
        )

        if isinstance(prev_obj.BaseObject, Slider):
            # Releasing a slider and tapping is simpler than two taps, so a
            # slider-circle-circle pattern reads as a triple, not a single
            # followed by a double.
            slider_lazy_end_delta = curr_obj.MinimumJumpTime
            slider_lazy_ratio = max(slider_lazy_end_delta, curr_delta) / min(
                slider_lazy_end_delta, curr_delta
            )
            slider_real_end_delta = curr_obj.LastObjectEndDeltaTime
            slider_real_ratio = max(slider_real_end_delta, curr_delta) / min(
                slider_real_end_delta, curr_delta
            )
            slider_effective_difficulty = min(
                _get_effective_difficulty(slider_lazy_ratio),
                _get_effective_difficulty(slider_real_ratio),
            )
            effective_difficulty = min(
                slider_effective_difficulty, effective_difficulty
            )

        if delta_difference < delta_difference_epsilon:
            island.AddDelta(int(curr_delta))

        if first_delta_switch:
            if delta_difference > delta_difference_epsilon:
                # Changing tempo into a slider gives a forgiving hit window.
                if isinstance(curr_obj.BaseObject, Slider):
                    effective_difficulty *= 0.5

                # Islands of the same parity alternate the same hand.
                if island.IsSimilarPolarity(previous_island, delta_difference_epsilon):
                    effective_difficulty *= 0.5

                # A speed-up one note after another (1/1 to 1/2 to 1/4) is not
                # worth rewarding twice.
                if (
                    max(prev_prev_obj.DeltaTime, DELTA_MIN_VALUE)
                    > prev_delta + delta_difference_epsilon
                    and prev_delta > curr_delta + delta_difference_epsilon
                ):
                    effective_difficulty *= 0.125

                # Repeating the same island length (triplet after triplet).
                if previous_island.DeltaCount == island.DeltaCount:
                    effective_difficulty *= 0.5

                is_speeding_up = prev_delta > curr_delta + delta_difference_epsilon
                if is_speeding_up:
                    effective_difficulty *= 0.65

                found = False
                for existing_island in islands:
                    if existing_island.AlmostEquals(island, delta_difference_epsilon):
                        # Only consecutive repeats add to the occurrence count.
                        if previous_island.AlmostEquals(
                            island, delta_difference_epsilon
                        ):
                            existing_island.Occurrences += 1

                        power = DiffUtils.Logistic(
                            island.Delta,
                            midpoint_offset=58.33,
                            multiplier=0.24,
                            max_value=2.75,
                        )
                        effective_difficulty *= min(
                            3.0 / existing_island.Occurrences,
                            DiffUtils.Pow(1.0 / existing_island.Occurrences, power),
                        )
                        found = True
                        break

                if not found and island.DeltaCount > 0:
                    islands.append(island)

                # Double-tappable patterns are easier than they look.
                effective_difficulty *= (
                    1 - prev_obj.CalculateDoubleTapFeasibility(curr_obj) * 0.75
                )

                if island.DeltaCount > 1:
                    rhythm_complexity_sum += (
                        math.sqrt(effective_difficulty * start_difficulty)
                        * curr_historical_decay
                    )
                else:
                    # Single-note islands are worth a flat amount.
                    rhythm_complexity_sum += 0.7 * curr_historical_decay

                start_difficulty = effective_difficulty

                if prev_delta + delta_difference_epsilon < curr_delta:
                    # Slowing down ends the run; speeding up keeps counting.
                    first_delta_switch = False

                previous_island = island
                island = Island(int(curr_delta))

        elif prev_delta > curr_delta + delta_difference_epsilon:
            # A speed-up begins a new island run.
            first_delta_switch = True

            if isinstance(curr_obj.BaseObject, Slider):
                effective_difficulty *= 0.6
            if isinstance(prev_obj.BaseObject, Slider):
                effective_difficulty *= 0.6

            start_difficulty = effective_difficulty
            island = Island(int(curr_delta))

        prev_prev_obj = prev_obj
        prev_obj = curr_obj

    # A long trailing island dilutes the sum.
    rhythm_complexity_sum *= DiffUtils.ReverseLerp(island.DeltaCount, 22, 3)

    return math.sqrt(4 + rhythm_complexity_sum * RHYTHM_OVERALL_MULTIPLIER) / 2.0
