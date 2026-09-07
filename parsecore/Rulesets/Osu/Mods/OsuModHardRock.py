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

from parsecore.Rulesets.Mods.ModHardRock import ADJUST_RATIO, ModHardRock
from parsecore.Rulesets.Osu.Utils.OsuHitObjectGenerationUtils import (
    ReflectVerticallyAlongPlayfield,
)
from parsecore.Utils.Vector2 import f32

# Circle size grows by less than the other settings. As with the shared ratio,
# osu! writes this as a ``float``, which is a shade under 1.3.
CIRCLE_SIZE_RATIO = f32(1.3)


class OsuModHardRock(ModHardRock):
    """Everything just got a bit harder, and the playfield is upside down."""

    IncompatibleMods = ModHardRock.IncompatibleMods + ("MR",)

    def ApplyToDifficulty(self, difficulty) -> None:
        """Raise every difficulty setting, capped at ten.

        Args:
            difficulty: The difficulty to modify.
        """
        super().ApplyToDifficulty(difficulty)

        difficulty.OverallDifficulty = min(
            difficulty.OverallDifficulty * ADJUST_RATIO, 10.0
        )
        difficulty.CircleSize = min(difficulty.CircleSize * CIRCLE_SIZE_RATIO, 10.0)
        difficulty.ApproachRate = min(difficulty.ApproachRate * ADJUST_RATIO, 10.0)

    def ApplyToHitObject(self, hit_object) -> None:
        """Mirror an object across the middle of the playfield.

        Args:
            hit_object: The object to reflect.
        """
        ReflectVerticallyAlongPlayfield(hit_object)
