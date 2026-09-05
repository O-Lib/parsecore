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
from parsecore.Rulesets.Difficulty.Skills.HarmonicSkill import HarmonicSkill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Osu.Difficulty.Evaluators import ReadingEvaluator
from parsecore.Rulesets.Osu.Mods.OsuModAutopilot import OsuModAutopilot
from parsecore.Rulesets.Osu.Mods.OsuModHidden import OsuModHidden
from parsecore.Rulesets.Osu.Mods.OsuModMagnetised import OsuModMagnetised
from parsecore.Rulesets.Osu.Mods.OsuModRelax import OsuModRelax
from parsecore.Rulesets.Osu.Mods.OsuModTouchDevice import OsuModTouchDevice
from parsecore.Utils.Interpolation import Lerp

SKILL_MULTIPLIER = 2.5
REDUCED_DIFFICULTY_DURATION = 60 * 1000

# The opening is assumed to be fully memorised, so it starts at zero.
REDUCED_DIFFICULTY_BASE_LINE = 0.0


class Reading(HarmonicSkill):
    """Measures how hard a beatmap is to read."""

    def __init__(self, mods: list | None = None) -> None:
        """Create the reading skill.

        Args:
            mods: The mods the score was set with.
        """
        super().__init__(mods)
        self._has_hidden_mod = any(
            isinstance(m, OsuModHidden)
            and not getattr(m, "OnlyFadeApproachCircles", False)
            for m in self.Mods
        )
        self._current_strain = 0.0
        self._reduced_note_count = 0.0
        self._reduced_duration: float | None = None

    @staticmethod
    def _strain_decay(ms: float) -> float:
        """Return the decay factor over a time span.

        Args:
            ms: The elapsed time in milliseconds.
        """
        return DiffUtils.Pow(0.8, ms / 1000)

    def ObjectDifficultyOf(self, current: DifficultyHitObject) -> float:
        """Return how hard a single object is to read.

        Objects are assumed to arrive once each and in order, which is what
        lets the opening minute be counted off here.

        Args:
            current: The object being processed.
        """
        decay = self._strain_decay(current.DeltaTime)
        self._current_strain *= decay
        self._current_strain += (
            self._calculate_adjusted_difficulty(current) * (1 - decay) * SKILL_MULTIPLIER
        )

        if self._reduced_duration is None:
            self._reduced_duration = current.StartTime + REDUCED_DIFFICULTY_DURATION

        if current.StartTime <= self._reduced_duration:
            self._reduced_note_count += 1

        return self._current_strain

    def _calculate_adjusted_difficulty(self, current: DifficultyHitObject) -> float:
        """Return the reading difficulty of one object, adjusted for mods.

        Args:
            current: The object being processed.
        """
        difficulty = ReadingEvaluator.EvaluateDifficultyOf(current, self._has_hidden_mod)

        if any(isinstance(m, OsuModTouchDevice) for m in self.Mods):
            difficulty = DiffUtils.Pow(difficulty, 0.89)

        magnetised = next(
            (m for m in self.Mods if isinstance(m, OsuModMagnetised)), None
        )
        if magnetised is not None:
            difficulty *= 1.0 - magnetised.AttractionStrength

        if any(isinstance(m, OsuModRelax) for m in self.Mods):
            difficulty *= 0.4
        if any(isinstance(m, OsuModAutopilot) for m in self.Mods):
            difficulty *= 0.1

        difficulty *= (
            0.825 + DiffUtils.Pow(max(0.0, current.OverallDifficulty), 2.2) / 1125.0
        )

        return difficulty

    def GetTransformedDifficulties(self, difficulties: list[float]) -> list[float]:
        """Return the difficulties with the opening minute discounted.

        Args:
            difficulties: What each object contributed, in order.
        """
        difficulties = [v for v in difficulties if v > 0]

        if self._reduced_note_count <= 0:
            return difficulties

        for i in range(int(min(len(difficulties), self._reduced_note_count))):
            scale = math.log10(
                Lerp(1, 10, min(max(i / self._reduced_note_count, 0.0), 1.0))
            )
            difficulties[i] *= Lerp(REDUCED_DIFFICULTY_BASE_LINE, 1.0, scale)

        return difficulties

    def CountTopWeightedObjectDifficulties(self, difficulty_value: float) -> float:
        """Return how many objects carry most of the reading difficulty.

        Args:
            difficulty_value: The skill's total difficulty.
        """
        if not self.ObjectDifficulties:
            return 0.0
        if self.ObjectWeightSum == 0:
            return 0.0

        consistent_top_note = difficulty_value / self.ObjectWeightSum
        if consistent_top_note == 0:
            return 0.0

        return sum(
            DiffUtils.Logistic(d / consistent_top_note, 1.15, 5, 1.1)
            for d in self.ObjectDifficulties
        )
