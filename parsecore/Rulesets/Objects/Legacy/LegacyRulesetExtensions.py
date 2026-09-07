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
from decimal import ROUND_HALF_EVEN, Decimal

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Utils.Vector2 import f32

# Builds of osu! up to 2013-05-04 rounded the playfield down, which scaled
# every radius by this much. Removing it would change every object's size.
BROKEN_GAMEFIELD_ROUNDING_ALLOWANCE = 1.00041

DECIMAL_ZERO = Decimal(0)
DECIMAL_SIXTEEN = Decimal(16)


def GetPrecisionAdjustedBeatLength(
    has_slider_velocity, timing_control_point, ruleset_short_name: str
) -> float:
    """Return the beat length a slider's velocity is measured against.

    The slider velocity is turned back into the negative beat length the file
    declared, narrowed to single precision, and multiplied back in. osu! does
    this to reproduce the rounding osu!stable had.

    Args:
        has_slider_velocity: The object carrying a slider velocity multiplier.
        timing_control_point: The timing point in effect.
        ruleset_short_name: One of ``osu``, ``taiko``, ``fruits`` or ``mania``.

    Returns:
        The adjusted beat length.

    Raises:
        ValueError: If the ruleset is not a legacy one.
    """
    slider_velocity_as_beat_length = -100 / has_slider_velocity.SliderVelocityMultiplier

    if ruleset_short_name in ("taiko", "mania"):
        upper = 10000
    elif ruleset_short_name in ("osu", "fruits"):
        upper = 1000
    else:
        raise ValueError("must be a legacy ruleset")

    if slider_velocity_as_beat_length < 0:
        # The cast to single precision is what osu!stable effectively did.
        bpm_multiplier = (
            min(max(f32(-slider_velocity_as_beat_length), 10), upper) / 100.0
        )
    else:
        bpm_multiplier = 1.0

    return timing_control_point.BeatLength * bpm_multiplier


def CalculateScaleFromCircleSize(
    circle_size: float, apply_fudge: bool = False
) -> float:
    """Return the object scale a circle size corresponds to.

    Args:
        circle_size: The beatmap's circle size.
        apply_fudge: Whether to apply osu!stable's rounding allowance.

    Returns:
        The scale factor applied to the base object radius.
    """
    # osu! narrows to single precision at each step here; the intermediate
    # rounding shifts every object's radius slightly.
    inner = f32(1.0 - f32(0.7) * BeatmapDifficulty.DifficultyRange(circle_size))
    scale = f32(inner / 2.0)
    if apply_fudge:
        scale = f32(scale * f32(BROKEN_GAMEFIELD_ROUNDING_ALLOWANCE))
    return scale


def CalculateDifficultyPeppyStars(
    difficulty, object_count: int, drain_length: int
) -> int:
    """Return the rough star count osu!stable multiplied its scores by.

    This is not a star rating. It is the number osu!stable derived from the
    three drain settings and how densely packed the beatmap is, and every point
    of osu!stable score was scaled by it.

    osu!stable computed this on the x87 registers of the .NET Framework, which
    are eighty bits wide -- wider than a double. osu!lazer reproduces that with
    a decimal type rather than a double, and so does this, because on a good
    number of ranked beatmaps the rounding lands differently otherwise.

    Args:
        difficulty: The beatmap's difficulty settings.
        object_count: How many objects the beatmap has.
        drain_length: How many seconds of it are played, breaks excluded.

    Returns:
        The multiplier, rounded to a whole number.
    """
    object_to_drain_ratio = (
        min(max(Decimal(object_count) / Decimal(drain_length) * 8, DECIMAL_ZERO), DECIMAL_SIXTEEN)
        if drain_length != 0
        else DECIMAL_SIXTEEN
    )

    drain_rate = _double_to_decimal(difficulty.DrainRate)
    overall_difficulty = _double_to_decimal(difficulty.OverallDifficulty)
    circle_size = _double_to_decimal(difficulty.CircleSize)

    total = (
        drain_rate + overall_difficulty + circle_size + object_to_drain_ratio
    ) / 38 * 5

    return int(total.quantize(DECIMAL_ZERO, rounding=ROUND_HALF_EVEN))


def _double_to_decimal(value: float) -> Decimal:
    """Return a double as the decimal osu! converts it to.

    Args:
        value: The value to convert.
    """
    if value == 0:
        return DECIMAL_ZERO

    # A double keeps at most fifteen significant digits when it becomes a
    # decimal, so the exponent of the fifteenth digit is where it is rounded.
    exponent = math.floor(math.log10(abs(value)))
    return Decimal(repr(value)).quantize(
        Decimal(1).scaleb(exponent - 14), rounding=ROUND_HALF_EVEN
    )
