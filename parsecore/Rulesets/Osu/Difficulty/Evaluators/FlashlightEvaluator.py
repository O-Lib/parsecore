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
from parsecore.Rulesets.Osu.Mods.OsuModHidden import OsuModHidden
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner

MAX_OPACITY_BONUS = 0.4
HIDDEN_BONUS = 0.2
MIN_VELOCITY = 0.5
SLIDER_MULTIPLIER = 1.3
MIN_ANGLE_MULTIPLIER = 0.2

# How many objects back the flashlight memory reaches.
HISTORY_LENGTH = 10


def EvaluateDifficultyOf(current, mods: list) -> float:
    """Return the flashlight difficulty of reading up to ``current``.

    Args:
        current: The object being evaluated.
        mods: The mods the score was set with.

    Returns:
        The flashlight difficulty of this object.
    """
    if isinstance(current.BaseObject, Spinner):
        return 0.0

    osu_current = current
    osu_hit_object = osu_current.BaseObject

    scaling_factor = 52.0 / osu_hit_object.Radius

    small_dist_nerf = 1.0
    cumulative_strain_time = 0.0
    flashlight_difficulty = 0.0

    last_obj = osu_current
    angle_repeat_count = 0.0

    hidden_mods = [m for m in mods if isinstance(m, OsuModHidden)]
    hidden_fades_objects = any(
        not getattr(m, "OnlyFadeApproachCircles", False) for m in hidden_mods
    )

    # Walk backwards in time from the current object.
    for i in range(min(current.Index, HISTORY_LENGTH)):
        current_obj = current.Previous(i)
        current_hit_object = current_obj.BaseObject

        cumulative_strain_time += last_obj.AdjustedDeltaTime

        if not isinstance(current_obj.BaseObject, Spinner):
            jump_distance = (
                osu_hit_object.StackedPosition - current_hit_object.StackedEndPosition
            ).length()

            # Objects already inside the flashlight circle are easy to see.
            if i == 0:
                small_dist_nerf = min(1.0, jump_distance / 75.0)

            # Only the first object of a stack should count.
            stack_nerf = min(
                1.0, (current_obj.LazyJumpDistance / scaling_factor) / 25.0
            )

            opacity_bonus = 1.0 + MAX_OPACITY_BONUS * (
                1.0
                - osu_current.OpacityAt(
                    current_hit_object.StartTime, hidden_fades_objects
                )
            )

            flashlight_difficulty += (
                stack_nerf
                * opacity_bonus
                * scaling_factor
                * jump_distance
                / cumulative_strain_time
            )

            if current_obj.Angle is not None and osu_current.Angle is not None:
                # Objects further back count less towards the repetition nerf.
                if abs(current_obj.Angle - osu_current.Angle) < 0.02:
                    angle_repeat_count += max(1.0 - 0.1 * i, 0.0)

        last_obj = current_obj

    flashlight_difficulty = DiffUtils.Pow(small_dist_nerf * flashlight_difficulty, 2)

    # Hidden removes the approach circles, so there is more to remember.
    if hidden_mods:
        flashlight_difficulty *= 1.0 + HIDDEN_BONUS

    flashlight_difficulty *= MIN_ANGLE_MULTIPLIER + (1.0 - MIN_ANGLE_MULTIPLIER) / (
        angle_repeat_count + 1.0
    )

    slider_bonus = 0.0
    if isinstance(osu_current.BaseObject, Slider):
        osu_slider = osu_current.BaseObject

        # Undo the scaling to recover the true travel distance in pixels.
        pixel_travel_distance = osu_current.LazyTravelDistance / scaling_factor

        slider_bonus = DiffUtils.Pow(
            max(0.0, pixel_travel_distance / osu_current.TravelTime - MIN_VELOCITY),
            0.5,
        )

        # Longer sliders take more memorising.
        slider_bonus *= pixel_travel_distance

        # Repeats retrace known ground, so they need less memorising.
        if osu_slider.RepeatCount > 0:
            slider_bonus /= osu_slider.RepeatCount + 1

    flashlight_difficulty += slider_bonus * SLIDER_MULTIPLIER

    return flashlight_difficulty
