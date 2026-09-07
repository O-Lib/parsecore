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

from parsecore.Rulesets.Catch.Difficulty.Preprocessing.CatchDifficultyHitObject import (
    NORMALIZED_HALF_CATCHER_WIDTH,
)
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Utils.Vector2 import f32

# What turning around is worth on top of the distance itself.
DIRECTION_CHANGE_BONUS = 21.0

# How far from a hyper-dash a movement still counts as an edge dash.
EDGE_DASH_THRESHOLD = 20.0

# How many earlier movements a steady run is looked for over.
MAX_LINEAR_SPACING_LOOKBACK = 10

# How closely two spacings must match to continue a steady run.
LINEAR_SPACING_TOLERANCE = 0.05


def EvaluateDifficultyOf(current) -> float:
    """Return how hard the movement onto an object is.

    Args:
        current: The difficulty object to rate.
    """
    last = current.Previous(0)
    last_last = current.Previous(1)

    catcher_speed_multiplier = current.ClockRate

    weighted_strain_time = current.StrainTime + 13 + (3 / catcher_speed_multiplier)
    distance_addition = DiffUtils.Pow(abs(current.DistanceMoved), 1.3) / 510
    sqrt_strain = math.sqrt(weighted_strain_time)

    edge_dash_bonus = 0.0

    if abs(current.DistanceMoved) > 0.1:
        if (
            current.Index >= 1
            and abs(last.DistanceMoved) > 0.1
            and _sign(current.DistanceMoved) != _sign(last.DistanceMoved)
        ):
            bonus_factor = f32(min(50.0, abs(current.DistanceMoved)) / 50)
            antiflow_factor = max(f32(min(70.0, abs(last.DistanceMoved)) / 70), 0.38)

            distance_addition += (
                DIRECTION_CHANGE_BONUS
                / math.sqrt(last.StrainTime + 16)
                * bonus_factor
                * antiflow_factor
                * max(1 - DiffUtils.Pow(weighted_strain_time / 1000, 3), 0.0)
            )

        distance_addition += (
            12.5
            * min(abs(current.DistanceMoved), NORMALIZED_HALF_CATCHER_WIDTH * 2)
            / (NORMALIZED_HALF_CATCHER_WIDTH * 6)
            / sqrt_strain
        )

    # A run of movements at one steady spacing settles into a rhythm, so each
    # further one in the run is worth less.
    linear_spacing_count = 0

    for i in range(min(current.Index, MAX_LINEAR_SPACING_LOOKBACK)):
        previous = current.Previous(i)

        if (
            _sign(current.DistanceMoved) != _sign(previous.DistanceMoved)
            or current.DistanceMoved == 0
            or previous.DistanceMoved == 0
        ):
            break

        current_spacing = abs(current.DistanceMoved / current.StrainTime)
        previous_spacing = abs(previous.DistanceMoved / previous.StrainTime)

        if abs(current_spacing / previous_spacing - 1) > LINEAR_SPACING_TOLERANCE:
            break

        linear_spacing_count += 1

    distance_addition *= DiffUtils.Pow(0.7, linear_spacing_count)

    # A dash that only just falls short of needing a hyper-dash is the hardest
    # thing in catch, and harder still the less time there is to judge it.
    if current.LastObject.DistanceToHyperDash <= EDGE_DASH_THRESHOLD:
        if not current.LastObject.HyperDash:
            edge_dash_bonus += 5.7

        room_to_spare = f32(
            f32(EDGE_DASH_THRESHOLD - current.LastObject.DistanceToHyperDash)
            / EDGE_DASH_THRESHOLD
        )

        distance_addition *= 1.0 + edge_dash_bonus * room_to_spare * DiffUtils.Pow(
            min(current.StrainTime * catcher_speed_multiplier, 265) / 265, 1.5
        )

    if (
        current.Index >= 2
        and abs(current.ExactDistanceMoved) <= NORMALIZED_HALF_CATCHER_WIDTH * 2
        and current.ExactDistanceMoved == -last.ExactDistanceMoved
        and last.ExactDistanceMoved == -last_last.ExactDistanceMoved
        and current.StrainTime == last.StrainTime
        and last.StrainTime == last_last.StrainTime
    ):
        distance_addition = 0.0

    return distance_addition / weighted_strain_time


def _sign(value: float) -> int:
    """Return the sign of a value, the way osu! reads it.

    Args:
        value: The value to test.
    """
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0
