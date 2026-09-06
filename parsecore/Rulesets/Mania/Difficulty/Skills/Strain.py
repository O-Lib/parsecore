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

from parsecore.Rulesets.Difficulty.Skills.StrainDecaySkill import StrainDecaySkill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Mania.Difficulty.Evaluators import (
    IndividualStrainEvaluator,
    OverallStrainEvaluator,
)

# How fast one finger's strain falls away, per second.
INDIVIDUAL_DECAY_BASE = 0.125

# How fast the whole stage's strain falls away, per second.
OVERALL_DECAY_BASE = 0.30


class Strain(StrainDecaySkill):
    """Measures how hard a mania beatmap is to play."""

    SkillMultiplier = 1
    StrainDecayBase = 1

    def __init__(self, mods: list | None = None, total_columns: int = 0) -> None:
        """Create the skill.

        Args:
            mods: The mods the score was set with.
            total_columns: How many columns the stage has.
        """
        super().__init__(mods)

        self._individual_strains = [0.0] * total_columns
        self._highest_individual_strain = 0.0
        self._overall_strain = 1.0

    def StrainValueOf(self, current) -> float:
        """Return what one note adds to the standing strain.

        Args:
            current: The difficulty object to rate.
        """
        column = current.Column

        self._individual_strains[column] = _apply_decay(
            self._individual_strains[column],
            current.ColumnStrainTime,
            INDIVIDUAL_DECAY_BASE,
        )
        self._individual_strains[column] += IndividualStrainEvaluator.EvaluateDifficultyOf(
            current
        )

        # Notes struck together are one chord, so the hardest of them stands
        # for all of them; otherwise the order they are processed in would
        # change the result.
        self._highest_individual_strain = (
            max(self._highest_individual_strain, self._individual_strains[column])
            if current.DeltaTime <= 1
            else self._individual_strains[column]
        )

        self._overall_strain = _apply_decay(
            self._overall_strain, current.DeltaTime, OVERALL_DECAY_BASE
        )
        self._overall_strain += OverallStrainEvaluator.EvaluateDifficultyOf(current)

        # Subtracting what already stood leaves only the hardest single note of
        # each strain section counting towards it.
        return (
            self._highest_individual_strain
            + self._overall_strain
            - self.CurrentStrain
        )

    def CalculateInitialStrain(self, offset: float, current) -> float:
        """Return the strain a new section starts at.

        Args:
            offset: When the section begins.
            current: The first object of the new section.
        """
        elapsed = offset - current.Previous(0).StartTime

        return _apply_decay(
            self._highest_individual_strain, elapsed, INDIVIDUAL_DECAY_BASE
        ) + _apply_decay(self._overall_strain, elapsed, OVERALL_DECAY_BASE)


def _apply_decay(value: float, delta_time: float, decay_base: float) -> float:
    """Return a strain after it has been left alone for a while.

    Args:
        value: The strain as it stood.
        delta_time: How long has passed, in milliseconds.
        decay_base: What fraction of the strain survives one second.
    """
    return value * DiffUtils.Pow(decay_base, delta_time / 1000)
