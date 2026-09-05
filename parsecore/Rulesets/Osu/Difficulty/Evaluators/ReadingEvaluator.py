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
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner
from parsecore.Utils.Interpolation import DoubleLerp

READING_WINDOW_SIZE = 3000.0

# Movements shorter than 1.5 circles barely affect how a pattern reads.
DISTANCE_INFLUENCE_THRESHOLD = NORMALISED_DIAMETER * 1.5


def EvaluateDifficultyOf(current, hidden: bool) -> float:
    """Return the reading difficulty of ``current``.

    Args:
        current: The object being evaluated.
        hidden: Whether the hidden mod is active.

    Returns:
        The reading difficulty of this object.
    """
    if isinstance(current.BaseObject, Spinner) or current.Index == 0:
        return 0.0

    curr_obj = current
    next_obj = current.Next()

    # Velocity may only add difficulty, never remove it.
    velocity = max(1.0, curr_obj.LazyJumpDistance / curr_obj.AdjustedDeltaTime)

    current_visible_object_density = _retrieve_current_visible_object_density(curr_obj)
    past_object_difficulty_influence = _get_past_object_difficulty_influence(curr_obj)
    constant_angle_nerf_factor = _get_constant_angle_nerf_factor(curr_obj)

    note_density_difficulty = _calculate_density_difficulty(
        next_obj,
        velocity,
        constant_angle_nerf_factor,
        past_object_difficulty_influence,
        current_visible_object_density,
    )

    hidden_difficulty = (
        _calculate_hidden_difficulty(
            curr_obj,
            past_object_difficulty_influence,
            current_visible_object_density,
            velocity,
            constant_angle_nerf_factor,
        )
        if hidden
        else 0.0
    )

    preempt_difficulty = _calculate_preempt_difficulty(
        velocity, constant_angle_nerf_factor, curr_obj.Preempt
    )

    reading_difficulty = DiffUtils.Norm(
        1.5, preempt_difficulty, hidden_difficulty, note_density_difficulty
    )

    # Less time to process what is on screen is harder.
    reading_difficulty *= _high_bpm_bonus(curr_obj.AdjustedDeltaTime)

    return reading_difficulty


def _calculate_density_difficulty(
    next_obj,
    velocity: float,
    constant_angle_nerf_factor: float,
    past_object_difficulty_influence: float,
    current_visible_object_density: float,
) -> float:
    """Return the difficulty of reading a dense cluster of objects.

    Args:
        next_obj: The object after the one being evaluated, or ``None``.
        velocity: The cursor velocity onto the current object.
        constant_angle_nerf_factor: The penalty for repeated angles.
        past_object_difficulty_influence: How much the visible past adds.
        current_visible_object_density: How many objects are on screen.
    """
    density_multiplier = 2.4
    density_difficulty_base = 2.5

    # Objects still to come also obscure where the cursor must go.
    future_object_difficulty_influence = math.sqrt(current_visible_object_density)

    if next_obj is not None:
        future_object_difficulty_influence *= DiffUtils.Smootherstep(
            next_obj.LazyJumpDistance, 15, DISTANCE_INFLUENCE_THRESHOLD
        )

    note_density_difficulty = (
        DiffUtils.Pow(
            past_object_difficulty_influence + future_object_difficulty_influence, 1.7
        )
        * 0.4
        * constant_angle_nerf_factor
        * velocity
    )

    # Only maps denser than average earn anything.
    note_density_difficulty = max(0.0, note_density_difficulty - density_difficulty_base)

    # A soft cap, because a player memorises part of what they read.
    return DiffUtils.Pow(note_density_difficulty, 0.45) * density_multiplier


def _calculate_preempt_difficulty(
    velocity: float, constant_angle_nerf_factor: float, preempt: float
) -> float:
    """Return the difficulty of a short approach time.

    Args:
        velocity: The cursor velocity onto the current object.
        constant_angle_nerf_factor: The penalty for repeated angles.
        preempt: How long the object is visible before it must be hit.
    """
    preempt_balancing_factor = 140000.0
    # 500 ms is approximately approach rate 9.66.
    preempt_starting_point = 500.0

    preempt_difficulty = (
        DiffUtils.Pow(
            (
                preempt_starting_point
                - preempt
                + abs(preempt - preempt_starting_point)
            )
            / 2,
            2.5,
        )
        / preempt_balancing_factor
    )

    # osu! forms the two factors into one product before applying it, and the
    # grouping is worth a bit of the result.
    return preempt_difficulty * (constant_angle_nerf_factor * velocity)


def _calculate_hidden_difficulty(
    curr_obj,
    past_object_difficulty_influence: float,
    current_visible_object_density: float,
    velocity: float,
    constant_angle_nerf_factor: float,
) -> float:
    """Return the extra difficulty hidden adds to reading.

    Args:
        curr_obj: The object being evaluated.
        past_object_difficulty_influence: How much the visible past adds.
        current_visible_object_density: How many objects are on screen.
        velocity: The cursor velocity onto the current object.
        constant_angle_nerf_factor: The penalty for repeated angles.
    """
    hidden_multiplier = 0.28

    # A longer preempt means longer spent invisible, which is rewarded.
    preempt_factor = DiffUtils.Pow(curr_obj.Preempt, 2.2) * 0.01
    density_factor = (
        DiffUtils.Pow(
            current_visible_object_density + past_object_difficulty_influence, 3.3
        )
        * 3
    )

    hidden_difficulty = (
        (preempt_factor + density_factor)
        * constant_angle_nerf_factor
        * velocity
        * 0.01
    )

    # A soft cap, because a player memorises part of what they read.
    hidden_difficulty = DiffUtils.Pow(hidden_difficulty, 0.4) * hidden_multiplier

    previous_obj = curr_obj.Previous()

    # A perfect stack only counts when the next note is fully invisible at the
    # moment the previous one is clicked.
    if (
        previous_obj is not None
        and curr_obj.LazyJumpDistance == 0
        and curr_obj.OpacityAt(previous_obj.BaseObject.StartTime, True) == 0
        and previous_obj.StartTime > curr_obj.StartTime - curr_obj.Preempt
    ):
        hidden_difficulty += hidden_multiplier * 2500 / DiffUtils.Pow(
            curr_obj.AdjustedDeltaTime, 1.5
        )

    return hidden_difficulty


def _get_past_object_difficulty_influence(curr_obj) -> float:
    """Return how much the objects still on screen add to reading.

    Args:
        curr_obj: The object being evaluated.
    """
    past_object_difficulty_influence = 0.0

    for loop_obj in _retrieve_past_visible_objects(curr_obj):
        loop_difficulty = curr_obj.OpacityAt(loop_obj.BaseObject.StartTime, False)

        # Objects a short distance apart can be cheesed, so how they were
        # arranged matters less.
        loop_difficulty *= DiffUtils.Smootherstep(
            loop_obj.LazyJumpDistance, 15, DISTANCE_INFLUENCE_THRESHOLD
        )

        time_between = curr_obj.StartTime - loop_obj.StartTime
        loop_difficulty *= _get_time_nerf_factor(time_between)

        past_object_difficulty_influence += loop_difficulty

    return past_object_difficulty_influence


def _retrieve_past_visible_objects(current) -> list:
    """Return the objects already on screen when ``current`` appears.

    Args:
        current: The object being evaluated.
    """
    result = []

    for i in range(current.Index):
        hit_object = current.Previous(i)
        if (
            hit_object is None
            or current.StartTime - hit_object.StartTime > READING_WINDOW_SIZE
            # The current object was not yet visible when that one was clicked.
            or hit_object.StartTime < current.StartTime - current.Preempt
        ):
            break
        result.append(hit_object)

    return result


def _retrieve_current_visible_object_density(current) -> float:
    """Return how many objects are on screen when ``current`` must be clicked.

    Args:
        current: The object being evaluated.
    """
    visible_object_count = 0.0

    hit_object = current.Next()
    while hit_object is not None:
        if (
            hit_object.StartTime - current.StartTime > READING_WINDOW_SIZE
            # That object is not visible yet when the current one is clicked.
            or current.StartTime < hit_object.StartTime - hit_object.Preempt
        ):
            break

        time_between = hit_object.StartTime - current.StartTime
        visible_object_count += (
            hit_object.OpacityAt(current.BaseObject.StartTime, False)
            * _get_time_nerf_factor(time_between)
        )

        hit_object = hit_object.Next()

    return visible_object_count


def _get_constant_angle_nerf_factor(current) -> float:
    """Return a penalty for how often the current angle has already appeared.

    Args:
        current: The object being evaluated.

    Returns:
        A multiplier between ``0.2`` and ``1``.
    """
    minimum_angle_relevancy_time = 2000.0
    maximum_angle_relevancy_time = 200.0

    constant_angle_count = 0.0
    index = 0
    current_time_gap = 0.0

    loop_obj_prev0 = current
    loop_obj_prev1 = None
    loop_obj_prev2 = None

    while current_time_gap < minimum_angle_relevancy_time:
        loop_obj = current.Previous(index)
        if loop_obj is None:
            break

        # Objects near the time limit count for less.
        long_interval_factor = 1 - DiffUtils.ReverseLerp(
            loop_obj.AdjustedDeltaTime,
            maximum_angle_relevancy_time,
            minimum_angle_relevancy_time,
        )

        if loop_obj.Angle is not None and current.Angle is not None:
            angle_difference = abs(current.Angle - loop_obj.Angle)
            angle_difference_alternating = math.pi

            if (
                loop_obj_prev0.Angle is not None
                and loop_obj_prev1 is not None
                and loop_obj_prev1.Angle is not None
                and loop_obj_prev2 is not None
                and loop_obj_prev2.Angle is not None
            ):
                angle_difference_alternating = abs(
                    loop_obj_prev1.Angle - loop_obj.Angle
                )
                angle_difference_alternating += abs(
                    loop_obj_prev2.Angle - loop_obj_prev0.Angle
                )

                # Only count alternation where one angle is sharp and the
                # other is wide.
                weight = 1.0
                weight *= DiffUtils.ReverseLerp(
                    min(loop_obj.Angle, loop_obj_prev0.Angle) * 180 / math.pi, 20, 5
                )
                weight *= DiffUtils.ReverseLerp(
                    max(loop_obj.Angle, loop_obj_prev0.Angle) * 180 / math.pi, 60, 120
                )

                # osu! reaches for .NET's own lerp here, not the framework's.
                angle_difference_alternating = DoubleLerp(
                    math.pi, 0.1 * angle_difference_alternating, weight
                )

            stack_factor = DiffUtils.Smootherstep(
                loop_obj.LazyJumpDistance, 0, NORMALISED_RADIUS
            )

            constant_angle_count += (
                math.cos(
                    3
                    * min(
                        math.radians(30),
                        min(angle_difference, angle_difference_alternating)
                        * stack_factor,
                    )
                )
                * long_interval_factor
            )

        current_time_gap = current.StartTime - loop_obj.StartTime
        index += 1
        loop_obj_prev2 = loop_obj_prev1
        loop_obj_prev1 = loop_obj_prev0
        loop_obj_prev0 = loop_obj

    if constant_angle_count <= 0:
        # No comparable angles found, so nothing is repeated.
        return 1.0

    return min(max(2 / constant_angle_count, 0.2), 1.0)


def _get_time_nerf_factor(delta_time: float) -> float:
    """Return how much an object still counts, given how distant it is in time.

    Args:
        delta_time: The time between the two objects.
    """
    return min(max(2 - delta_time / (READING_WINDOW_SIZE / 2), 0.0), 1.0)


def _high_bpm_bonus(ms: float) -> float:
    """Return the bonus applied because fast rhythms leave less reading time.

    Args:
        ms: The time available, in milliseconds.
    """
    return 1 / (1 - DiffUtils.Pow(0.8, ms / 1000))
