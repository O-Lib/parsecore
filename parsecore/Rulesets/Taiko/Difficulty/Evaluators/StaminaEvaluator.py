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

from parsecore.Rulesets.Taiko.Objects.Hit import Hit

# How long a colour change may be away before it stops constraining the hands.
COLOUR_CHANGE_WINDOW = 300.0

# Fingers available with and without a nearby colour change.
CONSTRAINED_FINGERS = 2
FREE_FINGERS = 8

# What every note costs before any speed is taken into account.
BASE_STRAIN = 0.5


def EvaluateDifficultyOf(current) -> float:
    """Return how much stamina a note demands.

    Args:
        current: The difficulty object to rate.
    """
    if not isinstance(current.BaseObject, Hit):
        return 0.0

    previous = current.Previous(1)
    previous_mono = current.PreviousMono(_available_fingers_for(current) - 1)

    object_strain = BASE_STRAIN
    if previous is None:
        return object_strain

    if previous_mono is not None:
        object_strain += _speed_bonus(
            current.StartTime - previous_mono.StartTime
        ) + 0.5 * _speed_bonus(current.StartTime - previous.StartTime)

    return object_strain


def _speed_bonus(interval: float) -> float:
    """Return how much a gap between notes is worth.

    Args:
        interval: The gap in milliseconds.
    """
    return 20 / max(interval, 1)


def _available_fingers_for(hit_object) -> int:
    """Return how many fingers the passage around a note leaves free.

    Args:
        hit_object: The difficulty object to look around.
    """
    previous_colour_change = hit_object.ColourData.PreviousColourChange
    next_colour_change = hit_object.ColourData.NextColourChange

    if (
        previous_colour_change is not None
        and hit_object.StartTime - previous_colour_change.StartTime
        < COLOUR_CHANGE_WINDOW
    ):
        return CONSTRAINED_FINGERS

    if (
        next_colour_change is not None
        and next_colour_change.StartTime - hit_object.StartTime
        < COLOUR_CHANGE_WINDOW
    ):
        return CONSTRAINED_FINGERS

    return FREE_FINGERS
