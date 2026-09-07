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

import bisect
from dataclasses import dataclass

from parsecore.Rulesets.Difficulty.Preprocessing.DifficultyHitObject import (
    DifficultyHitObject,
)
from parsecore.Rulesets.Difficulty.Skills.Skill import Skill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils


@dataclass(frozen=True, slots=True)
class StrainPeak:
    """The peak strain of one section, and how long that section ran."""

    Value: float
    SectionLength: float

    @staticmethod
    def create(value: float, section_length: float) -> StrainPeak:
        """Return a peak with its section length rounded, as osu! stores it.

        Args:
            value: The peak strain of the section.
            section_length: How long the section ran, in milliseconds.
        """
        return StrainPeak(value, round(section_length))


class VariableLengthStrainSkill(Skill):
    """A strain skill with sections that end on peaks rather than on a grid."""

    def __init__(
        self,
        mods: list | None = None,
        decay_weight: float = 0.9,
        max_section_length: int = 400,
    ) -> None:
        """Create a variable-length strain skill.

        Args:
            mods: The mods the score was set with.
            decay_weight: How quickly later sections stop mattering.
            max_section_length: The longest a section may run.
        """
        super().__init__(mods)
        self.DecayWeight = decay_weight
        self.MaxSectionLength = max_section_length

        # Enough sections to preserve 99.999% of the difficulty value.
        self._max_stored_length = 11 / (1 - self.DecayWeight)

        self._current_section_peak = 0.0
        self._current_section_begin = 0.0
        self._current_section_end = 0.0

        self._strain_peaks: list[StrainPeak] = []
        self._total_length = 0.0
        self._queued_strains: list[tuple[float, float]] = []
        self._final_peak: StrainPeak | None = None

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
        if current.Index == 0:
            self._current_section_begin = current.StartTime
            self._current_section_end = (
                self._current_section_begin + self.MaxSectionLength
            )
            self._current_section_peak = self.StrainValueAt(current)
            return self._current_section_peak

        self._backfill_peaks(current)

        current_strain = self.StrainValueAt(current)

        if current_strain > self._current_section_peak:
            # A new peak ends the section; nothing queued behind it matters.
            self._queued_strains.clear()
            self._save_current_peak(current.StartTime - self._current_section_begin)

            self._current_section_begin = current.StartTime
            self._current_section_end = (
                self._current_section_begin + self.MaxSectionLength
            )
            self._current_section_peak = current_strain
        else:
            # Keep only strains that could still become a section's peak.
            while (
                self._queued_strains
                and self._queued_strains[-1][0] < current_strain
            ):
                self._queued_strains.pop()
            self._queued_strains.append((current_strain, current.StartTime))

        return current_strain

    def _backfill_peaks(self, current: DifficultyHitObject) -> None:
        """Close off sections the current object has already run past.

        Queued strains are used first, so a gap does not drop the difficulty
        sharply between two sections.

        Args:
            current: The object being processed.
        """
        while current.StartTime > self._current_section_end:
            self._save_current_peak(
                self._current_section_end - self._current_section_begin
            )
            self._current_section_begin = self._current_section_end

            if self._queued_strains:
                strain, start_time = self._queued_strains.pop(0)

                # The section ends one length after the strain it is built on,
                # so a distant queued strain gets a section of its own.
                self._current_section_end = start_time + self.MaxSectionLength
                self._start_new_section_from(self._current_section_begin, current)

                # Never let a queued strain lower an already higher peak.
                self._current_section_peak = max(
                    self._current_section_peak, strain
                )
            else:
                self._current_section_end = (
                    self._current_section_begin + self.MaxSectionLength
                )
                self._start_new_section_from(self._current_section_begin, current)

    def _save_current_peak(self, section_length: float) -> None:
        """Store the peak of the section just finished.

        Args:
            section_length: How long that section ran, in milliseconds.
        """
        if self._final_peak is not None:
            self._strain_peaks.remove(self._final_peak)
            self._final_peak = None

        peak = StrainPeak.create(self._current_section_peak, section_length)
        # Peaks are kept sorted from highest to lowest.
        bisect.insort(self._strain_peaks, peak, key=lambda p: -p.Value)
        self._total_length += section_length

        # Drop peaks too far down the list to affect the difficulty.
        while self._total_length > self._max_stored_length * self.MaxSectionLength:
            self._total_length -= self._strain_peaks[-1].SectionLength
            self._strain_peaks.pop()

    def _start_new_section_from(
        self, time: float, current: DifficultyHitObject
    ) -> None:
        """Begin a new section at the strain the previous one decayed to.

        Args:
            time: The time the section starts.
            current: The object that triggered the new section.
        """
        self._current_section_peak = self.CalculateInitialStrain(time, current)

    def GetCurrentStrainPeaks(self) -> list[StrainPeak]:
        """Return every section peak, including the one still being filled."""
        if self._final_peak is None:
            self._final_peak = StrainPeak.create(
                self._current_section_peak,
                self._current_section_end - self._current_section_begin,
            )
            bisect.insort(
                self._strain_peaks, self._final_peak, key=lambda p: -p.Value
            )
        return self._strain_peaks

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
