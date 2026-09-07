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
from parsecore.Rulesets.Osu.Difficulty.Evaluators.Aim import SnapAimEvaluator
from parsecore.Rulesets.Osu.Difficulty.Preprocessing.OsuDifficultyHitObject import (
    NORMALISED_DIAMETER,
    NORMALISED_RADIUS,
)
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner

VELOCITY_CHANGE_MULTIPLIER = 0.52

# Flow difficulty scales harder than linearly with both distance and time.
FLOW_DIFFICULTY_EXPONENT = 1.45


def EvaluateDifficultyOf(current, with_slider_travel_distance: bool) -> float:
    """Return the flow-aim difficulty of moving onto ``current``.

    Args:
        current: The object being evaluated.
        with_slider_travel_distance: Whether slider travel counts towards aim.

    Returns:
        The flow difficulty of this object.
    """
    osu_curr_obj = current
    osu_last_obj = current.Previous()

    if (
        isinstance(current.BaseObject, Spinner)
        or current.Index <= 1
        or isinstance(osu_last_obj.BaseObject, Spinner)
    ):
        return 0.0

    osu_last_last_obj = current.Previous(1)

    curr_distance = (
        osu_curr_obj.LazyJumpDistance
        if with_slider_travel_distance
        else osu_curr_obj.JumpDistance
    )
    prev_distance = (
        osu_last_obj.LazyJumpDistance
        if with_slider_travel_distance
        else osu_last_obj.JumpDistance
    )

    curr_velocity = curr_distance / osu_curr_obj.AdjustedDeltaTime

    if isinstance(osu_last_obj.BaseObject, Slider) and with_slider_travel_distance:
        # After a slider, the travel velocity carries into the next object.
        slider_distance = (
            osu_last_obj.LazyTravelDistance + osu_curr_obj.LazyJumpDistance
        )
        curr_velocity = max(
            curr_velocity, slider_distance / osu_curr_obj.AdjustedDeltaTime
        )

    prev_velocity = prev_distance / osu_last_obj.AdjustedDeltaTime

    flow_difficulty = curr_velocity

    # A reduced circle-size bonus, because this evaluator scales distance over
    # time differently to the one the bonus was tuned for.
    flow_difficulty *= math.sqrt(osu_curr_obj.SmallCircleBonus)

    # Changing rhythm mid-flow is harder than holding one.
    flow_difficulty *= 1 + min(
        0.25,
        DiffUtils.Pow(
            (
                max(osu_curr_obj.AdjustedDeltaTime, osu_last_obj.AdjustedDeltaTime)
                - min(osu_curr_obj.AdjustedDeltaTime, osu_last_obj.AdjustedDeltaTime)
            )
            / 50,
            4,
        ),
    )

    if osu_curr_obj.Angle is not None and osu_last_obj.Angle is not None:
        angle_difference = abs(osu_curr_obj.Angle - osu_last_obj.Angle)
        angle_difference_adjusted = math.sin(angle_difference / 2) * 180.0
        angular_velocity = angle_difference_adjusted / (
            osu_curr_obj.AdjustedDeltaTime * 0.1
        )
        # Consistent angles flow more easily than erratic ones.
        flow_difficulty *= 0.8 + math.sqrt(angular_velocity / 270.0)

    # Three objects stacked on top of each other need no real movement.
    overlapped_notes_weight = 1.0
    if current.Index > 2:
        o1 = _calculate_overlap_factor(osu_curr_obj, osu_last_obj)
        o2 = _calculate_overlap_factor(osu_curr_obj, osu_last_last_obj)
        o3 = _calculate_overlap_factor(osu_last_obj, osu_last_last_obj)
        overlapped_notes_weight = 1 - o1 * o2 * o3

    if osu_curr_obj.Angle is not None:
        # Acute angles are hard to flow through.
        flow_difficulty += (
            curr_velocity
            * SnapAimEvaluator.CalcAngleAcuteness(osu_curr_obj.Angle)
            * overlapped_notes_weight
        )

    if max(prev_velocity, curr_velocity) != 0:
        if with_slider_travel_distance:
            curr_velocity = curr_distance / osu_curr_obj.AdjustedDeltaTime

        dist_ratio = DiffUtils.Smoothstep(
            abs(prev_velocity - curr_velocity) / max(prev_velocity, curr_velocity),
            0,
            1,
        )

        overlap_velocity_buff = min(
            NORMALISED_DIAMETER
            * 1.25
            / min(osu_curr_obj.AdjustedDeltaTime, osu_last_obj.AdjustedDeltaTime),
            abs(prev_velocity - curr_velocity),
        )

        flow_difficulty += (
            overlap_velocity_buff
            * dist_ratio
            * overlapped_notes_weight
            * VELOCITY_CHANGE_MULTIPLIER
        )

    if isinstance(osu_curr_obj.BaseObject, Slider) and with_slider_travel_distance:
        # Include slider velocity so flow stays comparable with snap.
        flow_difficulty += osu_curr_obj.TravelDistance / osu_curr_obj.TravelTime

    flow_difficulty = DiffUtils.Pow(flow_difficulty, FLOW_DIFFICULTY_EXPONENT)

    # Spacing below one radius is always flowed, so it earns less.
    return flow_difficulty * DiffUtils.Smootherstep(
        curr_distance, 0, NORMALISED_RADIUS
    )


def _calculate_overlap_factor(first, second) -> float:
    """Return how much two objects overlap, from ``0`` to ``1``.

    Args:
        first: The first object.
        second: The second object.
    """
    first_base = first.BaseObject
    second_base = second.BaseObject

    object_radius = first_base.Radius
    distance = (first_base.StackedPosition - second_base.StackedPosition).length()

    return min(
        max(
            1 - DiffUtils.Pow(max(distance - object_radius, 0) / object_radius, 2),
            0.0,
        ),
        1.0,
    )
