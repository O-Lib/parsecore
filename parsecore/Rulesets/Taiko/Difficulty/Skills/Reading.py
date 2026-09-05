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
from parsecore.Rulesets.Difficulty.Skills.StrainDecaySkill import StrainDecaySkill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Taiko.Difficulty.Evaluators import ReadingEvaluator
from parsecore.Rulesets.Taiko.Difficulty.Skills.Stamina import index_in_mono_streak
from parsecore.Rulesets.Taiko.Objects.Hit import Hit


class Reading(StrainDecaySkill):
    """The strain of reading a fast-scrolling playfield."""

    SkillMultiplier = 1.0
    StrainDecayBase = 0.4

    def __init__(self, mods: list | None = None) -> None:
        """Create the reading skill.

        Args:
            mods: The mods the score was set with.
        """
        super().__init__(mods)
        self._current_strain = 0.0

    def StrainValueOf(self, current: DifficultyHitObject) -> float:
        """Return the reading strain after this object.

        This skill carries its own strain rather than the one the base class
        keeps, because it decays by how deep into a colour run the note sits
        as well as by time.

        Args:
            current: The object being processed.
        """
        if not isinstance(current.BaseObject, Hit):
            return 0.0

        index = index_in_mono_streak(current)

        self._current_strain *= DiffUtils.Logistic(index, 4, -1 / 25.0, 0.5) + 0.5
        self._current_strain *= self.StrainDecayBase
        self._current_strain += (
            ReadingEvaluator.EvaluateDifficultyOf(current) * self.SkillMultiplier
        )

        return self._current_strain
