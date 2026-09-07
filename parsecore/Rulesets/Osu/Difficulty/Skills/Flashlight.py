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

from parsecore.Rulesets.Difficulty.Preprocessing.DifficultyHitObject import (
    DifficultyHitObject,
)
from parsecore.Rulesets.Difficulty.Skills.StrainSkill import StrainSkill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Osu.Difficulty.Evaluators import FlashlightEvaluator
from parsecore.Rulesets.Osu.Mods.OsuModAutopilot import OsuModAutopilot
from parsecore.Rulesets.Osu.Mods.OsuModDeflate import OsuModDeflate
from parsecore.Rulesets.Osu.Mods.OsuModFlashlight import OsuModFlashlight
from parsecore.Rulesets.Osu.Mods.OsuModMagnetised import OsuModMagnetised
from parsecore.Rulesets.Osu.Mods.OsuModRelax import OsuModRelax
from parsecore.Rulesets.Osu.Mods.OsuModTouchDevice import OsuModTouchDevice

SKILL_MULTIPLIER = 0.058


class Flashlight(StrainSkill):
    """Measures how hard a beatmap is with a restricted view."""

    def __init__(self, mods: list | None = None, total_objects: int = 0) -> None:
        """Create the flashlight skill.

        Args:
            mods: The mods the score was set with.
            total_objects: How many objects the beatmap has.
        """
        super().__init__(mods)
        self._total_objects = total_objects
        self._current_strain = 0.0

    @staticmethod
    def _strain_decay(ms: float) -> float:
        """Return the decay factor over a time span.

        Args:
            ms: The elapsed time in milliseconds.
        """
        return DiffUtils.Pow(0.15, ms / 1000)

    def CalculateInitialStrain(
        self, time: float, current: DifficultyHitObject
    ) -> float:
        """Return the strain decayed to the start of a new section.

        Args:
            time: The time the section starts.
            current: The object that triggered the new section.
        """
        previous = current.Previous()
        if previous is None:
            return 0.0
        return self._current_strain * self._strain_decay(time - previous.StartTime)

    def StrainValueAt(self, current: DifficultyHitObject) -> float:
        """Return the strain after processing an object.

        Args:
            current: The object being processed.
        """
        if not any(isinstance(m, OsuModFlashlight) for m in self.Mods):
            # Without the mod there is nothing to read blind.
            return 0.0

        self._current_strain *= self._strain_decay(current.DeltaTime)
        self._current_strain += (
            self._calculate_adjusted_difficulty(current) * SKILL_MULTIPLIER
        )
        return self._current_strain

    def _calculate_adjusted_difficulty(self, current: DifficultyHitObject) -> float:
        """Return the flashlight difficulty of one object, adjusted for mods.

        Args:
            current: The object being processed.
        """
        difficulty = FlashlightEvaluator.EvaluateDifficultyOf(current, self.Mods)

        if any(isinstance(m, OsuModTouchDevice) for m in self.Mods):
            difficulty = DiffUtils.Pow(difficulty, 0.9)

        magnetised = next(
            (m for m in self.Mods if isinstance(m, OsuModMagnetised)), None
        )
        if magnetised is not None:
            difficulty *= 1.0 - magnetised.AttractionStrength

        deflate = next((m for m in self.Mods if isinstance(m, OsuModDeflate)), None)
        if deflate is not None:
            difficulty *= min(
                max(DiffUtils.ReverseLerp(deflate.StartScale, 11, 1), 0.1), 1.0
            )

        if any(isinstance(m, OsuModRelax) for m in self.Mods):
            difficulty *= 0.7
        if any(isinstance(m, OsuModAutopilot) for m in self.Mods):
            difficulty *= 0.4

        difficulty *= (
            0.985 + DiffUtils.Pow(max(0.0, current.OverallDifficulty), 2) / 4000
        )

        return difficulty

    def DifficultyValue(self) -> float:
        """Return the summed section peaks, scaled by beatmap length."""
        total = sum(self.GetCurrentStrainPeaks())

        # Shorter maps spend more of their time at the wider low-combo radius.
        total *= (
            0.7
            + 0.1 * min(1.0, self._total_objects / 200.0)
            + (
                0.2 * min(1.0, (self._total_objects - 200) / 200.0)
                if self._total_objects > 200
                else 0.0
            )
        )

        return total

    @staticmethod
    def DifficultyToPerformance(difficulty: float) -> float:
        """Return the performance a difficulty value is worth.

        Args:
            difficulty: The skill's difficulty value.
        """
        return 25 * DiffUtils.Pow(difficulty, 2)
