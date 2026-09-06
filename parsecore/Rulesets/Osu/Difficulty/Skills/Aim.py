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
from parsecore.Rulesets.Difficulty.Skills.VariableLengthStrainSkill import (
    StrainPeak,
    VariableLengthStrainSkill,
)
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Osu.Difficulty.Evaluators.Aim import (
    AgilityEvaluator,
    FlowAimEvaluator,
    SnapAimEvaluator,
)
from parsecore.Rulesets.Osu.Mods.OsuModAutopilot import OsuModAutopilot
from parsecore.Rulesets.Osu.Mods.OsuModMagnetised import OsuModMagnetised
from parsecore.Rulesets.Osu.Mods.OsuModRelax import OsuModRelax
from parsecore.Rulesets.Osu.Mods.OsuModTouchDevice import OsuModTouchDevice
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Utils.Interpolation import Lerp

SKILL_MULTIPLIER_SNAP = 70.9
SKILL_MULTIPLIER_AGILITY = 2.35
SKILL_MULTIPLIER_FLOW = 242.0
SKILL_MULTIPLIER_TOTAL = 1.12

COMBINED_SNAP_NORM_EXPONENT = 1.2

# Tunes how sharply the snap/flow blend switches between the two.
SNAP_FLOW_PROBABILITY_K = 7.27

REDUCED_SECTION_TIME = 4000
REDUCED_STRAIN_BASELINE = 0.727
CHUNK_SIZE = 20


class Aim(VariableLengthStrainSkill):
    """Measures how hard a beatmap is to aim."""

    def __init__(self, mods: list | None = None, include_sliders: bool = True) -> None:
        """Create the aim skill.

        Args:
            mods: The mods the score was set with.
            include_sliders: Whether slider travel counts towards aim.
        """
        super().__init__(mods)
        self.IncludeSliders = include_sliders
        self._current_strain = 0.0
        self._slider_strains: list[float] = []

    @staticmethod
    def _strain_decay(ms: float) -> float:
        """Return the decay factor over a time span.

        Args:
            ms: The elapsed time in milliseconds.
        """
        return DiffUtils.Pow(0.2, ms / 1000)

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
        if any(isinstance(m, OsuModAutopilot) for m in self.Mods):
            # Autopilot aims for the player.
            return 0.0

        decay = self._strain_decay(current.AdjustedDeltaTime)
        self._current_strain *= decay
        self._current_strain += self._calculate_adjusted_difficulty(current) * (
            1 - decay
        )

        if isinstance(current.BaseObject, Slider):
            self._slider_strains.append(self._current_strain)

        return self._current_strain

    def _calculate_adjusted_difficulty(self, current: DifficultyHitObject) -> float:
        """Return the blended aim difficulty of one object.

        Args:
            current: The object being processed.
        """
        snap_difficulty = (
            SnapAimEvaluator.EvaluateDifficultyOf(current, self.IncludeSliders)
            * SKILL_MULTIPLIER_SNAP
        )
        agility_difficulty = (
            AgilityEvaluator.EvaluateDifficultyOf(current) * SKILL_MULTIPLIER_AGILITY
        )
        flow_difficulty = (
            FlowAimEvaluator.EvaluateDifficultyOf(current, self.IncludeSliders)
            * SKILL_MULTIPLIER_FLOW
        )

        total_difficulty = self._calculate_total_value(
            snap_difficulty, agility_difficulty, flow_difficulty
        )

        magnetised = next(
            (m for m in self.Mods if isinstance(m, OsuModMagnetised)), None
        )
        if magnetised is not None:
            total_difficulty *= 1.0 - magnetised.AttractionStrength

        total_difficulty *= (
            0.985 + DiffUtils.Pow(max(0.0, current.OverallDifficulty), 2) / 4000
        )

        return total_difficulty

    def _calculate_total_value(
        self,
        snap_difficulty: float,
        agility_difficulty: float,
        flow_difficulty: float,
    ) -> float:
        """Blend snap, agility and flow into one difficulty.

        Flow is compared against snap and agility combined: snapping every
        circle of a stream demands enormous agility, at which point flowing
        becomes the easier choice.

        Args:
            snap_difficulty: The snap-aim difficulty of the object.
            agility_difficulty: The agility difficulty of the object.
            flow_difficulty: The flow-aim difficulty of the object.
        """
        combined_snap_difficulty = DiffUtils.Norm(
            COMBINED_SNAP_NORM_EXPONENT, snap_difficulty, agility_difficulty
        )

        p_snap = _calculate_snap_flow_probability(
            flow_difficulty / combined_snap_difficulty
            if combined_snap_difficulty
            else float("nan")
        )
        p_flow = 1 - p_snap

        if any(isinstance(m, OsuModTouchDevice) for m in self.Mods):
            # Agility already represents touch difficulty well enough.
            snap_difficulty = DiffUtils.Pow(snap_difficulty, 0.89)
            combined_snap_difficulty = DiffUtils.Norm(
                COMBINED_SNAP_NORM_EXPONENT, snap_difficulty, agility_difficulty
            )

        if any(isinstance(m, OsuModRelax) for m in self.Mods):
            combined_snap_difficulty *= 0.75
            flow_difficulty *= 0.6

        total_difficulty = combined_snap_difficulty * p_snap + flow_difficulty * p_flow
        return total_difficulty * SKILL_MULTIPLIER_TOTAL

    def GetDifficultSliders(self) -> float:
        """Return how many sliders are hard relative to the hardest one."""
        if not self._slider_strains:
            return 0.0

        max_slider_strain = max(self._slider_strains)
        if max_slider_strain == 0:
            return 0.0

        return sum(
            DiffUtils.Logistic(strain / max_slider_strain, 0.5, 12.0)
            for strain in self._slider_strains
        )

    def CountTopWeightedSliders(self, difficulty_value: float) -> float:
        """Return how many sliders carry most of the aim difficulty.

        Args:
            difficulty_value: The skill's total difficulty.
        """
        if not self._slider_strains:
            return 0.0

        consistent_top_strain = difficulty_value * (1 - self.DecayWeight)
        if consistent_top_strain == 0:
            return 0.0

        return sum(
            DiffUtils.Logistic(s / consistent_top_strain, 0.88, 10, 1.1)
            for s in self._slider_strains
        )

    def DifficultyValue(self) -> float:
        """Return the weighted sum of the sorted section peaks.

        The weighting integrates the decay across each section's length, so a
        map built purely of full-length sections matches what a fixed-length
        strain skill would produce.
        """
        difficulty = 0.0
        time = 0.0

        for strain in self._get_reduced_strain_peaks():
            start_time = time
            end_time = time + strain.SectionLength / self.MaxSectionLength

            weight = DiffUtils.Pow(self.DecayWeight, start_time) - DiffUtils.Pow(
                self.DecayWeight, end_time
            )

            difficulty += strain.Value * weight
            time = end_time

        return difficulty / (1 - self.DecayWeight)

    def _get_reduced_strain_peaks(self) -> list[StrainPeak]:
        """Return the section peaks with the very highest ones flattened.

        The hardest few seconds of a map are reduced towards a baseline, so a
        single extreme spike cannot carry the whole rating. The reduction runs
        in small chunks to keep it smooth.
        """
        strains = [p for p in self.GetCurrentStrainPeaks() if p.Value > 0]

        time = 0.0
        skip_count = 0

        while len(strains) > skip_count and time < REDUCED_SECTION_TIME:
            strain = strains[skip_count]

            added_time = 0.0
            while added_time < strain.SectionLength:
                scale = math.log10(
                    Lerp(
                        1,
                        10,
                        min(max((time + added_time) / REDUCED_SECTION_TIME, 0.0), 1.0),
                    )
                )
                strains.append(
                    StrainPeak.create(
                        strain.Value * Lerp(REDUCED_STRAIN_BASELINE, 1.0, scale),
                        min(CHUNK_SIZE, strain.SectionLength - added_time),
                    )
                )
                added_time += CHUNK_SIZE

            time += strain.SectionLength
            skip_count += 1

        return sorted(strains[skip_count:], key=lambda p: p.Value, reverse=True)


def _calculate_snap_flow_probability(ratio: float) -> float:
    """Return the probability a pattern is snapped rather than flowed.

    The function satisfies ``f(x) + f(1/x) = 1``, so snapping and flowing stay
    symmetric and always sum to one.

    Args:
        ratio: Flow difficulty divided by combined snap difficulty.
    """
    if ratio == 0:
        return 0.0
    if math.isnan(ratio):
        return 1.0
    return DiffUtils.LogisticExp(-SNAP_FLOW_PROBABILITY_K * math.log(ratio))
