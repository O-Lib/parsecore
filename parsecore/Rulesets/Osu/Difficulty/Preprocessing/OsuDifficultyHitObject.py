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

from parsecore.Rulesets.Difficulty.Preprocessing.DifficultyHitObject import (
    DifficultyHitObject,
)
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Objects.SliderEventGenerator import TAIL_LENIENCY
from parsecore.Rulesets.Osu.Mods.OsuModHidden import FADE_OUT_DURATION_MULTIPLIER
from parsecore.Rulesets.Osu.Objects.OsuHitObject import PREEMPT_MIN
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.SliderRepeat import SliderRepeat
from parsecore.Rulesets.Osu.Objects.SliderTick import SliderTick
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner
from parsecore.Utils.Vector2 import Vector2, f32

# Distances are scaled so every circle has this radius; 100 is then the
# diameter, which keeps the skill thresholds readable.
NORMALISED_RADIUS = 50
NORMALISED_DIAMETER = NORMALISED_RADIUS * 2

# Simultaneous objects would otherwise divide by zero.
MIN_DELTA_TIME = 25.0

# Declared as ``float`` in osu!, so they carry single-precision rounding.
MAXIMUM_SLIDER_RADIUS = f32(NORMALISED_RADIUS * f32(2.4))
ASSUMED_SLIDER_RADIUS = f32(NORMALISED_RADIUS * f32(1.8))


class OsuDifficultyHitObject(DifficultyHitObject):
    """One osu! object, with the geometry the difficulty skills need."""

    def __init__(
        self,
        hit_object,
        last_object,
        clock_rate: float,
        objects: list[DifficultyHitObject],
        index: int,
    ) -> None:
        """Wrap an osu! object for difficulty calculation.

        Args:
            hit_object: The object being wrapped.
            last_object: The object immediately before it.
            clock_rate: The rate the beatmap is played at.
            objects: The list this object is part of.
            index: This object's position in that list.
        """
        super().__init__(hit_object, last_object, clock_rate, objects, index)

        self.AdjustedDeltaTime = max(self.DeltaTime, MIN_DELTA_TIME)

        previous = self.Previous()
        self.LastObjectEndDeltaTime = (
            max(self.StartTime - previous.EndTime, MIN_DELTA_TIME)
            if previous is not None
            else self.AdjustedDeltaTime
        )

        self.JumpDistance = 0.0
        self.LazyJumpDistance = 0.0
        self.MinimumJumpDistance = 0.0
        self.MinimumJumpTime = 0.0
        self.TravelDistance = 0.0
        self.TravelTime = 0.0
        self.LazyEndPosition: Vector2 | None = None
        self.LazyTravelDistance = 0.0
        self.LazyTravelTime = 0.0
        self.Angle: float | None = None
        self.NormalisedVectorAngle: float | None = None

        self._compute_slider_cursor_position()
        self._set_distances(clock_rate)

    @property
    def Preempt(self) -> float:
        """Return how long the object is visible before it must be hit."""
        return self.BaseObject.TimePreempt / self.ClockRate

    @property
    def SmallCircleBonus(self) -> float:
        """Return the bonus applied because small circles are harder to hit."""
        return max(1.0, 1.0 + (30 - self.BaseObject.Radius) / 70)

    @property
    def OverallDifficulty(self) -> float:
        """Return the overall difficulty implied by this object's hit window."""
        return (79.5 - self.HitWindowGreat / 2) / 6

    def OpacityAt(self, time: float, hidden: bool) -> float:
        """Return how visible this object is at a point in time.

        Args:
            time: The time to sample, in milliseconds.
            hidden: Whether the hidden mod is active.

        Returns:
            The object's opacity, from ``0`` to ``1``.
        """
        base_object = self.BaseObject

        if time > base_object.StartTime:
            # Treated as invisible once its start time has passed; the object
            # lingers a little longer in reality, but not where this is used.
            return 0.0

        fade_in_start_time = base_object.StartTime - base_object.TimePreempt
        fade_in_duration = 400 * min(1.0, base_object.TimePreempt / PREEMPT_MIN)

        if hidden:
            fade_out_start_time = (
                base_object.StartTime
                - base_object.TimePreempt
                + base_object.TimeFadeIn
            )
            fade_out_duration = base_object.TimePreempt * FADE_OUT_DURATION_MULTIPLIER

            return min(
                min(max((time - fade_in_start_time) / fade_in_duration, 0.0), 1.0),
                1.0
                - min(
                    max((time - fade_out_start_time) / fade_out_duration, 0.0), 1.0
                ),
            )

        return min(max((time - fade_in_start_time) / fade_in_duration, 0.0), 1.0)

    def CalculateDoubleTapFeasibility(self, next_obj) -> float:
        """Return how easily this object can be double-tapped with the next.

        Two objects close in time and space can be hit with a single roll of
        two fingers, which makes them easier than their spacing suggests.

        Args:
            next_obj: The object after this one, or ``None``.

        Returns:
            A value from ``0`` (not feasible) to ``1`` (trivially feasible).
        """
        if next_obj is None:
            return 0.0

        curr_delta_time = max(1.0, self.DeltaTime)
        next_delta_time = max(1.0, next_obj.DeltaTime)
        delta_difference = abs(next_delta_time - curr_delta_time)

        speed_ratio = curr_delta_time / max(curr_delta_time, delta_difference)
        window_ratio = DiffUtils.Pow(
            min(1.0, curr_delta_time / self.HitWindowGreat), 5
        ) if self.HitWindowGreat else 0.0

        # Circles that do not overlap cannot be double-tapped.
        distance_factor = DiffUtils.Pow(
            DiffUtils.ReverseLerp(
                self.LazyJumpDistance, NORMALISED_DIAMETER, NORMALISED_RADIUS
            ),
            2,
        )

        return 1.0 - DiffUtils.Pow(speed_ratio, distance_factor * (1 - window_ratio))

    def _set_distances(self, clock_rate: float) -> None:
        """Compute jump distances and the angle at this object.

        Args:
            clock_rate: The rate the beatmap is played at.
        """
        base_object = self.BaseObject
        last_object = self.LastObject

        if isinstance(base_object, Slider):
            self.TravelDistance = self.LazyTravelDistance * max(
                1.0, DiffUtils.Pow(base_object.RepeatCount, 0.3)
            )
            self.TravelTime = max(self.LazyTravelTime / clock_rate, MIN_DELTA_TIME)

        self.MinimumJumpTime = self.AdjustedDeltaTime

        if isinstance(base_object, Spinner) or isinstance(last_object, Spinner):
            return

        # osu! holds this in a ``float``, so the division rounds before use.
        scaling_factor = f32(NORMALISED_RADIUS / f32(base_object.Radius))

        last_difficulty_object = self.Previous()
        last_last_difficulty_object = self.Previous(1)

        last_cursor_position = (
            self._get_end_cursor_position(last_difficulty_object)
            if last_difficulty_object is not None
            else last_object.StackedPosition
        )

        self.JumpDistance = f32(
            (last_object.StackedPosition - base_object.StackedPosition).length()
            * scaling_factor
        )
        self.LazyJumpDistance = f32(
            (base_object.StackedPosition - last_cursor_position).length()
            * scaling_factor
        )
        self.MinimumJumpDistance = self.LazyJumpDistance

        if isinstance(last_object, Slider) and last_difficulty_object is not None:
            last_travel_time = max(
                last_difficulty_object.LazyTravelTime / clock_rate, MIN_DELTA_TIME
            )
            self.MinimumJumpTime = max(
                self.AdjustedDeltaTime - last_travel_time, MIN_DELTA_TIME
            )

            tail_jump_distance = f32(
                (
                    last_object.TailCircle.StackedPosition
                    - base_object.StackedPosition
                ).length()
                * scaling_factor
            )

            self.MinimumJumpDistance = max(
                0.0,
                min(
                    self.LazyJumpDistance
                    - f32(MAXIMUM_SLIDER_RADIUS - ASSUMED_SLIDER_RADIUS),
                    f32(tail_jump_distance - MAXIMUM_SLIDER_RADIUS),
                ),
            )

        if last_last_difficulty_object is not None and not isinstance(
            last_last_difficulty_object.BaseObject, Spinner
        ):
            if (
                isinstance(last_difficulty_object.BaseObject, Slider)
                and last_difficulty_object.TravelDistance > 0
            ):
                last_cursor_position = (
                    last_difficulty_object.BaseObject.HeadCircle.StackedPosition
                )

            last_last_cursor_position = self._get_end_cursor_position(
                last_last_difficulty_object
            )

            angle = _calculate_angle(
                base_object.StackedPosition,
                last_cursor_position,
                last_last_cursor_position,
            )
            slider_angle = self._calculate_slider_angle(
                last_difficulty_object, last_last_cursor_position
            )

            v = base_object.StackedPosition - last_cursor_position
            self.NormalisedVectorAngle = math.atan2(abs(v.Y), abs(v.X))
            self.Angle = min(angle, slider_angle)

    def _calculate_slider_angle(
        self, last_difficulty_object, last_last_cursor_position: Vector2
    ) -> float:
        """Return the angle measured from a slider's own exit direction.

        Args:
            last_difficulty_object: The preceding object.
            last_last_cursor_position: The cursor position before that.
        """
        last_cursor_position = self._get_end_cursor_position(last_difficulty_object)

        previous_base = last_difficulty_object.BaseObject
        if isinstance(previous_base, Slider) and last_difficulty_object.TravelDistance > 0:
            second_last_nested = previous_base.NestedHitObjects[-2]
            last_last_cursor_position = second_last_nested.StackedPosition

        return _calculate_angle(
            self.BaseObject.StackedPosition,
            last_cursor_position,
            last_last_cursor_position,
        )

    @staticmethod
    def _get_end_cursor_position(difficulty_hit_object) -> Vector2:
        """Return where the cursor is assumed to rest after an object.

        Args:
            difficulty_hit_object: The object to inspect.
        """
        if difficulty_hit_object.LazyEndPosition is not None:
            return difficulty_hit_object.LazyEndPosition
        return difficulty_hit_object.BaseObject.StackedPosition

    def _compute_slider_cursor_position(self) -> None:
        """Walk a slider's nested objects to find how far the cursor moves."""
        slider = self.BaseObject
        if not isinstance(slider, Slider):
            return
        if self.LazyEndPosition is not None:
            return

        tracking_end_time = max(
            slider.StartTime + slider.Duration + TAIL_LENIENCY,
            slider.StartTime + slider.Duration / 2,
        )

        nested_objects = list(slider.NestedHitObjects)

        last_real_tick = None
        for hit_object in slider.NestedHitObjects:
            if isinstance(hit_object, SliderTick):
                last_real_tick = hit_object

        if last_real_tick is not None and last_real_tick.StartTime > tracking_end_time:
            # A tick inside the tail leniency must still be tracked, so it
            # becomes the last object the cursor is required to reach.
            tracking_end_time = last_real_tick.StartTime
            nested_objects.remove(last_real_tick)
            nested_objects.append(last_real_tick)

        self.LazyTravelTime = tracking_end_time - slider.StartTime

        end_time_min = self.LazyTravelTime / slider.SpanDuration
        if end_time_min % 2 >= 1:
            end_time_min = 1 - end_time_min % 1
        else:
            end_time_min %= 1

        # A provisional end position, refined by the walk below.
        self.LazyEndPosition = slider.StackedPosition + slider.Path.PositionAt(
            end_time_min
        )

        curr_cursor_position = slider.StackedPosition
        scaling_factor = NORMALISED_RADIUS / slider.Radius

        for i in range(1, len(nested_objects)):
            curr_movement_obj = nested_objects[i]

            curr_movement = (
                curr_movement_obj.StackedPosition - curr_cursor_position
            )
            curr_movement_length = scaling_factor * curr_movement.length()

            # The cursor only has to move far enough to stay inside the ball.
            required_movement = ASSUMED_SLIDER_RADIUS

            if i == len(nested_objects) - 1:
                lazy_movement = self.LazyEndPosition - curr_cursor_position
                if lazy_movement.length() < curr_movement.length():
                    curr_movement = lazy_movement
                curr_movement_length = scaling_factor * curr_movement.length()
            elif isinstance(curr_movement_obj, SliderRepeat):
                # Repeats demand a tighter movement than the rest of the path.
                required_movement = NORMALISED_RADIUS

            if curr_movement_length > required_movement:
                curr_cursor_position = curr_cursor_position + curr_movement * f32(
                    (curr_movement_length - required_movement) / curr_movement_length
                )
                curr_movement_length *= (
                    curr_movement_length - required_movement
                ) / curr_movement_length
                self.LazyTravelDistance += curr_movement_length

            if i == len(nested_objects) - 1:
                self.LazyEndPosition = curr_cursor_position


def _calculate_angle(
    current_position: Vector2, last_position: Vector2, last_last_position: Vector2
) -> float:
    """Return the angle at ``last_position`` between three points.

    Args:
        current_position: The current object's position.
        last_position: The previous object's position.
        last_last_position: The position before that.

    Returns:
        The angle in radians, between ``0`` and ``pi``.
    """
    v1 = last_last_position - last_position
    v2 = current_position - last_position

    dot = Vector2.dot(v1, v2)
    # The cross product is a single-precision expression in osu!.
    det = f32(f32(v1.X * v2.Y) - f32(v1.Y * v2.X))

    return abs(math.atan2(det, dot))
