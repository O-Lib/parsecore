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
from parsecore.Rulesets.Osu.Difficulty.Preprocessing.OsuDifficultyHitObject import (
    NORMALISED_DIAMETER,
)
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner

# Distance between centres is capped at 1.2 circles.
DISTANCE_CAP = NORMALISED_DIAMETER * 1.2


def EvaluateDifficultyOf(current) -> float:
    """Return how hard the movement onto ``current`` is to perform quickly.

    Args:
        current: The object being evaluated.

    Returns:
        The agility difficulty of reaching this object.
    """
    if isinstance(current.BaseObject, Spinner):
        return 0.0

    osu_curr_obj = current
    osu_prev_obj = current.Previous() if current.Index > 0 else None

    travel_distance = osu_prev_obj.LazyTravelDistance if osu_prev_obj else 0.0
    distance = travel_distance + osu_curr_obj.LazyJumpDistance

    distance_scaled = min(distance, DISTANCE_CAP) / DISTANCE_CAP

    agility_difficulty = distance_scaled * 1000 / osu_curr_obj.AdjustedDeltaTime
    agility_difficulty *= DiffUtils.Pow(osu_curr_obj.SmallCircleBonus, 1.5)
    agility_difficulty *= _high_bpm_bonus(osu_curr_obj.AdjustedDeltaTime)

    return agility_difficulty


def _high_bpm_bonus(ms: float) -> float:
    """Return the bonus applied because fast rhythms leave no recovery time.

    Args:
        ms: The time available for the movement, in milliseconds.
    """
    return 1 / (1 - DiffUtils.Pow(0.2, ms / 1000))
