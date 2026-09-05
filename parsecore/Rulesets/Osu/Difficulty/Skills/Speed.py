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
from parsecore.Rulesets.Difficulty.Skills.HarmonicSkill import HarmonicSkill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Osu.Difficulty.Evaluators.Speed import (
    RhythmEvaluator,
    SpeedEvaluator,
)
from parsecore.Rulesets.Osu.Mods.OsuModAutopilot import OsuModAutopilot
from parsecore.Rulesets.Osu.Mods.OsuModRelax import OsuModRelax
from parsecore.Rulesets.Osu.Objects.Slider import Slider

SKILL_MULTIPLIER = 1.16


class Speed(HarmonicSkill):
    """Measures how hard a beatmap is to tap."""

    HarmonicScale = 20
    DecayExponent = 0.9

    def __init__(self, mods: list | None = None) -> None:
        """Create the speed skill.

        Args:
            mods: The mods the score was set with.
        """
        super().__init__(mods)
        self._current_strain = 0.0
        self._slider_strains: list[float] = []

    @staticmethod
    def _strain_decay(ms: float) -> float:
        """Return the decay factor over a time span.

        Args:
            ms: The elapsed time in milliseconds.
        """
        return DiffUtils.Pow(0.3, ms / 1000)

    def ObjectDifficultyOf(self, current: DifficultyHitObject) -> float:
        """Return how hard a single object is to tap.

        Args:
            current: The object being processed.
        """
        if any(isinstance(m, OsuModRelax) for m in self.Mods):
            # Relax taps for the player.
            return 0.0

        decay = self._strain_decay(current.AdjustedDeltaTime)
        self._current_strain *= decay
        self._current_strain += (
            self._calculate_adjusted_difficulty(current) * (1 - decay) * SKILL_MULTIPLIER
        )

        current_rhythm = RhythmEvaluator.EvaluateDifficultyOf(current)
        total_strain = self._current_strain * current_rhythm

        if isinstance(current.BaseObject, Slider):
            self._slider_strains.append(total_strain)

        return total_strain

    def _calculate_adjusted_difficulty(self, current: DifficultyHitObject) -> float:
        """Return the tap difficulty of one object, adjusted for mods.

        Args:
            current: The object being processed.
        """
        difficulty = SpeedEvaluator.EvaluateDifficultyOf(current)

        if any(isinstance(m, OsuModAutopilot) for m in self.Mods):
            difficulty *= 0.5

        return difficulty

    def RelevantObjectCount(self) -> float:
        """Return how many objects carry meaningful speed difficulty."""
        if not self.ObjectDifficulties:
            return 0.0

        max_strain = max(self.ObjectDifficulties)
        if max_strain == 0:
            return 0.0

        return sum(
            DiffUtils.Logistic(strain / max_strain, 0.5, 12.0)
            for strain in self.ObjectDifficulties
        )

    def CountTopWeightedSliders(self, difficulty_value: float) -> float:
        """Return how many sliders carry most of the speed difficulty.

        Args:
            difficulty_value: The skill's total difficulty.
        """
        if not self._slider_strains:
            return 0.0
        if self.ObjectWeightSum == 0:
            return 0.0

        consistent_top_object = difficulty_value / self.ObjectWeightSum
        if consistent_top_object == 0:
            return 0.0

        return sum(
            DiffUtils.Logistic(s / consistent_top_object, 0.88, 10, 1.1)
            for s in self._slider_strains
        )
