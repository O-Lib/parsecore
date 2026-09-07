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

from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Utils.Precision import DefinitelyBigger

# How far apart two releases must be before the later one is awkward.
RELEASE_THRESHOLD = 30.0

# What holding something else at the same time is worth.
HOLD_FACTOR = 1.25


def EvaluateDifficultyOf(current) -> float:
    """Return how hard the stage is at the moment of one note.

    Args:
        current: The difficulty object to rate.
    """
    start_time = current.StartTime
    end_time = current.EndTime
    is_overlapping = False

    # The lowest value the current note alone justifies.
    closest_end_time = abs(end_time - start_time)
    hold_factor = 1.0
    hold_addition = 0.0

    for previous in current.PreviousHitObjects:
        if previous is None:
            continue

        # The note is overlapped where an earlier one runs into its body and
        # finishes inside it.
        is_overlapping = is_overlapping or (
            DefinitelyBigger(previous.EndTime, start_time, 1)
            and DefinitelyBigger(end_time, previous.EndTime, 1)
            and DefinitelyBigger(start_time, previous.StartTime, 1)
        )

        # Anything held at the same time is worth a little more.
        if DefinitelyBigger(previous.EndTime, end_time, 1) and DefinitelyBigger(
            start_time, previous.StartTime, 1
        ):
            hold_factor = HOLD_FACTOR

        closest_end_time = min(closest_end_time, abs(end_time - previous.EndTime))

    # The bonus for an awkward release only stands where nothing else ends near
    # by; it is halved once the closest release is a release threshold away.
    if is_overlapping:
        hold_addition = DiffUtils.Logistic(
            closest_end_time, multiplier=0.27, midpoint_offset=RELEASE_THRESHOLD
        )

    return (1 + hold_addition) * hold_factor
