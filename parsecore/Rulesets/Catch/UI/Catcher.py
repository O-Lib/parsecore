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

from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    CalculateScaleFromCircleSize,
)
from parsecore.Utils.Vector2 import f32

# The plate's width before circle size is taken into account.
BASE_SIZE = f32(106.75)

# The fraction of the plate that actually catches fruit.
ALLOWED_CATCH_RANGE = f32(0.8)

# How fast the plate moves while dashing, in osu! pixels per millisecond.
BASE_DASH_SPEED = 1.0

# How fast the plate moves while walking.
BASE_WALK_SPEED = 0.5


def CalculateScale(difficulty) -> float:
    """Return how large the plate is drawn.

    The plate is drawn at twice the scale a circle would be, so this is not the
    same number the objects themselves use.

    Args:
        difficulty: The beatmap's difficulty settings.
    """
    return f32(CalculateScaleFromCircleSize(difficulty.CircleSize) * 2)


def CalculateCatchWidth(difficulty) -> float:
    """Return how wide a stretch of playfield the plate catches.

    Args:
        difficulty: The beatmap's difficulty settings.
    """
    scale = CalculateScale(difficulty)
    return f32(f32(BASE_SIZE * abs(scale)) * ALLOWED_CATCH_RANGE)
