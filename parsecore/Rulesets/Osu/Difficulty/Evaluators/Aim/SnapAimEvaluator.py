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
    NORMALISED_DIAMETER,
    NORMALISED_RADIUS,
)
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner

WIDE_ANGLE_MULTIPLIER = 9.67
ACUTE_ANGLE_MULTIPLIER = 2.41
SLIDER_MULTIPLIER = 1.5
VELOCITY_CHANGE_MULTIPLIER = 0.9

# Raising this beyond 1.02 makes difficulty *fall* as distance grows.
WIGGLE_MULTIPLIER = 1.02

# How the wide-angle bonus rescales time.
WIDE_ANGLE_TIME_SCALE = 1.45


def EvaluateDifficultyOf(current, with_slider_travel_distance: bool) -> float:
    """Return the snap-aim difficulty of moving onto ``current``.

    Args:
        current: The object being evaluated.
        with_slider_travel_distance: Whether slider travel counts towards aim.

    Returns:
        The snap difficulty of this object.
    """
    osu_curr_obj = current
    osu_last_obj = current.Previous()

    if (
        isinstance(current.BaseObject, Spinner)
        or current.Index <= 1
        or isinstance(osu_last_obj.BaseObject, Spinner)
    ):
        return 0.0

    osu_last2_obj = current.Previous(2)

    radius = NORMALISED_RADIUS
    diameter = NORMALISED_DIAMETER

    # Velocity onto this object, assuming the last one was a circle.
    curr_distance = (
        osu_curr_obj.LazyJumpDistance
        if with_slider_travel_distance
        else osu_curr_obj.JumpDistance
    )
    curr_velocity = curr_distance / osu_curr_obj.AdjustedDeltaTime

    # After a slider, the travel velocity carries into the next object.
    if isinstance(osu_last_obj.BaseObject, Slider) and with_slider_travel_distance:
        slider_distance = (
            osu_last_obj.LazyTravelDistance + osu_curr_obj.LazyJumpDistance
        )
        curr_velocity = max(
            curr_velocity, slider_distance / osu_curr_obj.AdjustedDeltaTime
        )

    prev_distance = (
        osu_last_obj.LazyJumpDistance
        if with_slider_travel_distance
        else osu_last_obj.JumpDistance
    )
    prev_velocity = prev_distance / osu_last_obj.AdjustedDeltaTime

    snap_difficulty = curr_velocity

    snap_difficulty *= _vector_angle_repetition(osu_curr_obj, osu_last_obj)

    if osu_curr_obj.Angle is not None and osu_last_obj.Angle is not None:
        curr_angle = osu_curr_obj.Angle
        last_angle = osu_last_obj.Angle

        velocity_influence = min(curr_velocity, prev_velocity)

        acute_angle_bonus = 0.0
        if max(
            osu_curr_obj.AdjustedDeltaTime, osu_last_obj.AdjustedDeltaTime
        ) < 1.25 * min(osu_curr_obj.AdjustedDeltaTime, osu_last_obj.AdjustedDeltaTime):
            # Only when the rhythm is unchanged.
            acute_angle_bonus = CalcAngleAcuteness(curr_angle)

            # Repeated angles are compared raw, before any scaling.
            acute_angle_bonus *= 0.08 + 0.92 * (
                1
                - min(
                    acute_angle_bonus,
                    DiffUtils.Pow(CalcAngleAcuteness(last_angle), 3),
                )
            )

            # Only above 300 BPM (1/2) and beyond one diameter of spacing.
            acute_angle_bonus *= (
                velocity_influence
                * DiffUtils.Smootherstep(
                    DiffUtils.MillisecondsToBPM(osu_curr_obj.AdjustedDeltaTime, 2),
                    300,
                    400,
                )
                * DiffUtils.Smootherstep(curr_distance, 0, diameter * 2)
            )

        wide_angle_bonus = _calc_angle_wideness(curr_angle)
        wide_angle_bonus *= 0.25 + 0.75 * (
            1
            - min(wide_angle_bonus, DiffUtils.Pow(_calc_angle_wideness(last_angle), 3))
        )

        wide_angle_curr_velocity = curr_distance / DiffUtils.Pow(
            osu_curr_obj.AdjustedDeltaTime, WIDE_ANGLE_TIME_SCALE
        )
        wide_angle_prev_velocity = prev_distance / DiffUtils.Pow(
            osu_last_obj.AdjustedDeltaTime, WIDE_ANGLE_TIME_SCALE
        )

        if isinstance(osu_last_obj.BaseObject, Slider) and with_slider_travel_distance:
            slider_distance = (
                osu_last_obj.LazyTravelDistance + osu_curr_obj.LazyJumpDistance
            )
            wide_angle_curr_velocity = max(
                wide_angle_curr_velocity,
                slider_distance
                / DiffUtils.Pow(osu_curr_obj.AdjustedDeltaTime, WIDE_ANGLE_TIME_SCALE),
            )

        wide_angle_bonus *= min(wide_angle_curr_velocity, wide_angle_prev_velocity)

        if osu_last2_obj is not None:
            # Patterns that just bounce through one point earn less wide bonus.
            # An angle is centred on the previous object, hence Previous(2).
            last_base = osu_last_obj.BaseObject
            last2_base = osu_last2_obj.BaseObject
            distance = (last2_base.StackedPosition - last_base.StackedPosition).length()
            if distance < 1:
                wide_angle_bonus *= 1 - 0.55 * (1 - distance)

        snap_difficulty += max(
            acute_angle_bonus * ACUTE_ANGLE_MULTIPLIER,
            wide_angle_bonus * WIDE_ANGLE_MULTIPLIER,
        )

        # Wiggle patterns: jumps of [radius, 3 diameters] under a 110 degree angle.
        wiggle_bonus = (
            velocity_influence
            * DiffUtils.Smootherstep(curr_distance, radius, diameter)
            * DiffUtils.Pow(
                DiffUtils.ReverseLerp(curr_distance, diameter * 3, diameter), 1.8
            )
            * DiffUtils.Smootherstep(
                curr_angle, math.radians(110), math.radians(60)
            )
            * DiffUtils.Smootherstep(prev_distance, radius, diameter)
            * DiffUtils.Pow(
                DiffUtils.ReverseLerp(prev_distance, diameter * 3, diameter), 1.8
            )
            * DiffUtils.Smootherstep(
                last_angle, math.radians(110), math.radians(60)
            )
        )
        snap_difficulty += wiggle_bonus * WIGGLE_MULTIPLIER

    if max(prev_velocity, curr_velocity) != 0:
        if with_slider_travel_distance:
            # Velocity changes are judged on the jump alone, without sliders.
            curr_velocity = curr_distance / osu_curr_obj.AdjustedDeltaTime

        dist_ratio = DiffUtils.Smoothstep(
            abs(prev_velocity - curr_velocity) / max(prev_velocity, curr_velocity),
            0,
            1,
        )

        overlap_velocity_buff = min(
            diameter
            * 1.25
            / min(osu_curr_obj.AdjustedDeltaTime, osu_last_obj.AdjustedDeltaTime),
            abs(prev_velocity - curr_velocity),
        )

        velocity_change_bonus = overlap_velocity_buff * dist_ratio
        velocity_change_bonus *= DiffUtils.Pow(
            min(osu_curr_obj.AdjustedDeltaTime, osu_last_obj.AdjustedDeltaTime)
            / max(osu_curr_obj.AdjustedDeltaTime, osu_last_obj.AdjustedDeltaTime),
            2,
        )

        snap_difficulty += velocity_change_bonus * VELOCITY_CHANGE_MULTIPLIER

    if isinstance(osu_curr_obj.BaseObject, Slider) and with_slider_travel_distance:
        slider_bonus = osu_curr_obj.TravelDistance / osu_curr_obj.TravelTime
        snap_difficulty += (
            slider_bonus if slider_bonus < 1 else DiffUtils.Pow(slider_bonus, 0.75)
        ) * SLIDER_MULTIPLIER

    snap_difficulty *= osu_curr_obj.SmallCircleBonus
    snap_difficulty *= _high_bpm_bonus(osu_curr_obj.AdjustedDeltaTime)

    return snap_difficulty


def _high_bpm_bonus(ms: float) -> float:
    """Return the bonus applied because fast rhythms leave no recovery time.

    Args:
        ms: The time available for the movement, in milliseconds.
    """
    return 1 / (1 - DiffUtils.Pow(0.03, DiffUtils.Pow(ms / 1000, 0.65)))


def _vector_angle_repetition(current, previous) -> float:
    """Return a penalty for repeating the same movement direction.

    Args:
        current: The object being evaluated.
        previous: The object before it.

    Returns:
        A multiplier at or below one.
    """
    if current.Angle is None or previous.Angle is None:
        return 1.0

    note_limit = 6
    maximum_repetition_nerf = 0.15
    maximum_vector_influence = 0.5

    constant_angle_count = 0.0

    for index in range(note_limit):
        prev_obj = current.Previous(index)
        if prev_obj is None:
            break

        # Only vectors within one rhythm section count; a rhythm change breaks
        # the momentum that makes repetition easy.
        if max(current.AdjustedDeltaTime, prev_obj.AdjustedDeltaTime) > 1.1 * min(
            current.AdjustedDeltaTime, prev_obj.AdjustedDeltaTime
        ):
            break

        if (
            prev_obj.NormalisedVectorAngle is not None
            and current.NormalisedVectorAngle is not None
        ):
            angle_difference = abs(
                current.NormalisedVectorAngle - prev_obj.NormalisedVectorAngle
            )
            constant_angle_count += math.cos(
                8 * min(math.radians(11.25), angle_difference)
            )

    # An empty count means no repetition was found at all.
    vector_repetition = (
        DiffUtils.Pow(min(0.5 / constant_angle_count, 1), 2)
        if constant_angle_count > 0
        else 1.0
    )

    stack_factor = DiffUtils.Smootherstep(
        current.LazyJumpDistance, 0, NORMALISED_DIAMETER
    )

    curr_angle = current.Angle
    last_angle = previous.Angle

    angle_difference_adjusted = math.cos(
        2 * min(math.radians(45), abs(curr_angle - last_angle) * stack_factor)
    )

    base_nerf = 1 - maximum_repetition_nerf * CalcAngleAcuteness(
        last_angle
    ) * angle_difference_adjusted

    return DiffUtils.Pow(
        base_nerf
        + (1 - base_nerf) * vector_repetition * maximum_vector_influence * stack_factor,
        2,
    )


def _calc_angle_wideness(angle: float) -> float:
    """Return how wide an angle is, from ``0`` to ``1``.

    Args:
        angle: The angle in radians.
    """
    return DiffUtils.Smoothstep(angle, math.radians(40), math.radians(140))


def CalcAngleAcuteness(angle: float) -> float:
    """Return how acute an angle is, from ``0`` to ``1``.

    Args:
        angle: The angle in radians.
    """
    return DiffUtils.Smoothstep(angle, math.radians(140), math.radians(40))
