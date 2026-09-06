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
from parsecore.Rulesets.Difficulty.Skills.Skill import Skill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils


class StrainSkill(Skill):
    """A skill whose difficulty is the weighted sum of section peak strains."""

    DecayWeight = 0.9
    SectionLength = 400

    def __init__(self, mods: list | None = None) -> None:
        """Create a strain skill.

        Args:
            mods: The mods the score was set with.
        """
        super().__init__(mods)
        self._current_section_peak = 0.0
        self._current_section_end = 0.0
        self._strain_peaks: list[float] = []

    def StrainValueAt(self, current: DifficultyHitObject) -> float:
        """Return the strain after processing an object.

        Args:
            current: The object being processed.
        """
        raise NotImplementedError

    def CalculateInitialStrain(
        self, time: float, current: DifficultyHitObject
    ) -> float:
        """Return the strain a new section starts at.

        Args:
            time: The time the section starts.
            current: The object that triggered the new section.
        """
        raise NotImplementedError

    def ProcessInternal(self, current: DifficultyHitObject) -> float:
        """Return this object's strain, closing off sections as needed.

        Args:
            current: The object to process.
        """
        # The first object does not generate strain, so the section is started
        # one boundary ahead of it.
        if current.Index == 0:
            self._current_section_end = (
                math.ceil(current.StartTime / self.SectionLength) * self.SectionLength
            )

        while current.StartTime > self._current_section_end:
            self._save_current_peak()
            self._start_new_section_from(self._current_section_end, current)
            self._current_section_end += self.SectionLength

        strain = self.StrainValueAt(current)
        self._current_section_peak = max(strain, self._current_section_peak)
        return strain

    def CountTopWeightedStrains(self, difficulty_value: float) -> float:
        """Return how many objects carry most of the difficulty.

        Args:
            difficulty_value: The skill's total difficulty.

        Returns:
            An effective object count, used to scale length bonuses.
        """
        if not self.ObjectDifficulties:
            return 0.0

        # The top strain if every strain were identical.
        consistent_top_strain = difficulty_value * (1 - self.DecayWeight)

        if consistent_top_strain == 0:
            return float(len(self.ObjectDifficulties))

        return sum(
            DiffUtils.Logistic(s / consistent_top_strain, 0.88, 10, 1.1)
            for s in self.ObjectDifficulties
        )

    def GetCurrentStrainPeaks(self) -> list[float]:
        """Return every section peak, including the one still being filled."""
        return [*self._strain_peaks, self._current_section_peak]

    def DifficultyValue(self) -> float:
        """Return the weighted sum of the section peaks, highest first."""
        difficulty = 0.0
        weight = 1.0

        # Empty sections contribute nothing and are dropped before sorting.
        peaks = [p for p in self.GetCurrentStrainPeaks() if p > 0]

        for strain in sorted(peaks, reverse=True):
            difficulty += strain * weight
            weight *= self.DecayWeight

        return difficulty

    def _save_current_peak(self) -> None:
        """Store the peak of the section just finished."""
        self._strain_peaks.append(self._current_section_peak)

    def _start_new_section_from(
        self, time: float, current: DifficultyHitObject
    ) -> None:
        """Begin a new section at the strain the previous one decayed to.

        Args:
            time: The time the section starts.
            current: The object that triggered the new section.
        """
        self._current_section_peak = self.CalculateInitialStrain(time, current)
