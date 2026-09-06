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
from parsecore.Rulesets.Difficulty.Skills.StrainSkill import StrainSkill


class StrainDecaySkill(StrainSkill):
    """A strain skill that decays towards zero between objects."""

    SkillMultiplier = 1.0
    StrainDecayBase = 0.15

    def __init__(self, mods: list | None = None) -> None:
        """Create a strain decay skill.

        Args:
            mods: The mods the score was set with.
        """
        super().__init__(mods)
        self.CurrentStrain = 0.0

    def StrainValueOf(self, current: DifficultyHitObject) -> float:
        """Return how much strain an object adds.

        Args:
            current: The object being processed.
        """
        raise NotImplementedError

    def StrainValueAt(self, current: DifficultyHitObject) -> float:
        """Return the strain after decaying and adding this object.

        Args:
            current: The object being processed.
        """
        self.CurrentStrain *= self._strain_decay(current.DeltaTime)
        self.CurrentStrain += self.StrainValueOf(current) * self.SkillMultiplier
        return self.CurrentStrain

    def CalculateInitialStrain(
        self, time: float, current: DifficultyHitObject
    ) -> float:
        """Return the strain decayed to the start of a new section.

        Args:
            time: The time the section starts.
            current: The object that triggered the new section.
        """
        previous = current.Previous(0)
        if previous is None:
            return 0.0
        return self.CurrentStrain * self._strain_decay(time - previous.StartTime)

    def _strain_decay(self, ms: float) -> float:
        """Return the decay factor over a time span.

        Args:
            ms: The elapsed time in milliseconds.
        """
        return math.pow(self.StrainDecayBase, ms / 1000.0)
