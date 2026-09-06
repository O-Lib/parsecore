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
from parsecore.Rulesets.Difficulty.Skills.Skill import Skill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils


class HarmonicSkill(Skill):
    """A skill whose difficulty is a harmonically weighted sum of objects."""

    HarmonicScale = 1.0
    DecayExponent = 0.9

    def __init__(self, mods: list | None = None) -> None:
        """Create a harmonic skill.

        Args:
            mods: The mods the score was set with.
        """
        super().__init__(mods)
        self.ObjectWeightSum = 0.0

    def ObjectDifficultyOf(self, current: DifficultyHitObject) -> float:
        """Return how hard a single object is.

        Args:
            current: The object being processed.
        """
        raise NotImplementedError

    def ProcessInternal(self, current: DifficultyHitObject) -> float:
        """Return this object's difficulty.

        Args:
            current: The object to process.
        """
        return self.ObjectDifficultyOf(current)

    def GetTransformedDifficulties(self, difficulties: list[float]) -> list[float]:
        """Return the per-object difficulties, optionally reshaped.

        Args:
            difficulties: What each object contributed, in order.
        """
        return difficulties

    def DifficultyValue(self) -> float:
        """Return the harmonically weighted sum of every object's difficulty."""
        self.ObjectWeightSum = 0.0

        if not self.ObjectDifficulties:
            return 0.0

        difficulties = self.GetTransformedDifficulties(self.ObjectDifficulties)

        difficulty = 0.0
        index = 0

        # Objects worth nothing are dropped before sorting; they contribute
        # nothing either way.
        for obj in sorted((v for v in difficulties if v > 0), reverse=True):
            weight = (1 + (self.HarmonicScale / (1 + index))) / (
                DiffUtils.Pow(index, self.DecayExponent)
                + 1
                + (self.HarmonicScale / (1 + index))
            )
            self.ObjectWeightSum += weight
            difficulty += obj * weight
            index += 1

        return difficulty

    def CountTopWeightedObjectDifficulties(self, difficulty_value: float) -> float:
        """Return how many objects carry most of the difficulty.

        Args:
            difficulty_value: The skill's total difficulty.

        Returns:
            An effective object count, used to scale length bonuses.
        """
        if not self.ObjectDifficulties:
            return 0.0
        if self.ObjectWeightSum == 0:
            return 0.0

        # The top difficulty if every object were equally hard.
        consistent_top_object = difficulty_value / self.ObjectWeightSum
        if consistent_top_object == 0:
            return 0.0

        return sum(
            DiffUtils.Logistic(d / consistent_top_object, 0.88, 10, 1.1)
            for d in self.ObjectDifficulties
        )

    @staticmethod
    def DifficultyToPerformance(difficulty: float) -> float:
        """Return the performance a difficulty value is worth.

        Args:
            difficulty: The skill's difficulty value.
        """
        return 4.0 * DiffUtils.Pow(difficulty, 3)
