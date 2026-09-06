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

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Rulesets.Catch.Difficulty.CatchPerformanceAttributes import (
    CatchPerformanceAttributes,
)
from parsecore.Rulesets.Catch.Objects.CatchHitObject import (
    PREEMPT_MAX,
    PREEMPT_MID,
    PREEMPT_MIN,
)
from parsecore.Rulesets.Difficulty.PerformanceCalculator import PerformanceCalculator
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Scoring.HitResult import HitResult


class CatchPerformanceCalculator(PerformanceCalculator):
    """Calculates what a catch score is worth."""

    def __init__(self) -> None:
        """Create the calculator."""
        self._num300 = 0
        self._num100 = 0
        self._num50 = 0
        self._num_katu = 0
        self._num_miss = 0

    def CreatePerformanceAttributes(self, score, attributes):
        """Return what a catch score is worth.

        Args:
            score: The score to evaluate.
            attributes: The difficulty of the beatmap it was set on.

        Returns:
            The performance breakdown.
        """
        mods = list(score.Mods)

        # Catch scores its four kinds of object separately: fruit, droplets,
        # tiny droplets, and the tiny droplets that were dropped.
        self._num300 = score.GetCount(HitResult.Great)
        self._num100 = score.GetCount(HitResult.LargeTickHit)
        self._num50 = score.GetCount(HitResult.SmallTickHit)
        self._num_katu = score.GetCount(HitResult.SmallTickMiss)
        self._num_miss = max(
            0, score.GetCount(HitResult.Miss) + score.GetCount(HitResult.LargeTickMiss)
        )

        score_max_combo = min(max(score.MaxCombo, 0), attributes.MaxCombo)

        value = (
            DiffUtils.Pow(5.0 * max(1.0, attributes.StarRating / 0.0049) - 4.0, 2.0)
            / 100000.0
        )

        total_hits = self._total_combo_hits()
        length_bonus = (
            0.95
            + 0.3 * min(1.0, total_hits / 2500.0)
            + (math.log10(total_hits / 2500.0) * 0.475 if total_hits > 2500 else 0.0)
        )
        value *= length_bonus

        value *= DiffUtils.Pow(0.97, self._num_miss)

        if attributes.MaxCombo > 0:
            value *= min(
                DiffUtils.Pow(score_max_combo, 0.35)
                / DiffUtils.Pow(attributes.MaxCombo, 0.35),
                1.0,
            )

        difficulty = score.BeatmapDifficulty.Clone()
        for mod in mods:
            apply = getattr(mod, "ApplyToDifficulty", None)
            if callable(apply):
                apply(difficulty)

        clock_rate = _clock_rate_with_mods(mods)

        preempt = (
            BeatmapDifficulty.DifficultyRange(
                difficulty.ApproachRate, PREEMPT_MAX, PREEMPT_MID, PREEMPT_MIN
            )
            / clock_rate
        )
        approach_rate = (
            -(preempt - 1800.0) / 120.0
            if preempt > 1200.0
            else -(preempt - 1200.0) / 150.0 + 5.0
        )

        approach_rate_factor = 1.0
        if approach_rate > 9.0:
            approach_rate_factor += 0.1 * (approach_rate - 9.0)
        if approach_rate > 10.0:
            approach_rate_factor += 0.1 * (approach_rate - 10.0)
        elif approach_rate < 8.0:
            approach_rate_factor += 0.025 * (8.0 - approach_rate)

        value *= approach_rate_factor

        if _has_mod(mods, "HD"):
            if approach_rate <= 10.0:
                value *= 1.05 + 0.075 * (10.0 - approach_rate)
            else:
                value *= 1.01 + 0.04 * (11.0 - min(11.0, approach_rate))

        if _has_mod(mods, "FL"):
            value *= 1.35 * length_bonus

        value *= DiffUtils.Pow(self._accuracy(), 5.5)

        if _has_mod(mods, "NF"):
            value *= max(0.90, 1.0 - 0.02 * self._num_miss)

        return CatchPerformanceAttributes(Total=value)

    def _accuracy(self) -> float:
        """Return the fraction of catchable objects the player caught."""
        total = self._total_hits()
        if total == 0:
            return 0.0
        return min(max(self._total_successful_hits() / total, 0.0), 1.0)

    def _total_hits(self) -> int:
        """Return how many objects the player was judged on."""
        return (
            self._num50
            + self._num100
            + self._num300
            + self._num_miss
            + self._num_katu
        )

    def _total_successful_hits(self) -> int:
        """Return how many objects the player caught."""
        return self._num50 + self._num100 + self._num300

    def _total_combo_hits(self) -> int:
        """Return how many objects counted towards the combo."""
        return self._num_miss + self._num100 + self._num300


def _has_mod(mods: list, acronym: str) -> bool:
    """Return whether a mod is among those the score was set with.

    Args:
        mods: The mods the score was set with.
        acronym: The mod to look for.
    """
    return any(getattr(mod, "Acronym", None) == acronym for mod in mods)


def _clock_rate_with_mods(mods: list) -> float:
    """Return the rate the beatmap is played at.

    Args:
        mods: The mods the score was set with.
    """
    from parsecore.Rulesets.Difficulty.DifficultyCalculator import DifficultyCalculator

    return DifficultyCalculator.GetClockRate(mods)
