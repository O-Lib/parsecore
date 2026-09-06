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

from parsecore.Utils.Precision import DefinitelyBigger

# What one note is worth before any bonus.
BASE_STRAIN = 2.0

# What holding something else at the same time is worth.
HOLD_FACTOR = 1.25


def EvaluateDifficultyOf(current) -> float:
    """Return how hard one note is for the finger playing it.

    Args:
        current: The difficulty object to rate.
    """
    start_time = current.StartTime
    end_time = current.EndTime

    hold_factor = 1.0

    # A note played entirely inside another column's hold is worth more.
    for previous in current.PreviousHitObjects:
        if previous is None:
            continue

        if DefinitelyBigger(previous.EndTime, end_time, 1) and DefinitelyBigger(
            start_time, previous.StartTime, 1
        ):
            hold_factor = HOLD_FACTOR
            break

    return BASE_STRAIN * hold_factor
