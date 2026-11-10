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
from typing import cast

from parsecore.Rulesets.Difficulty.DifficultyAttributes import DifficultyAttributes
from parsecore.Rulesets.Difficulty.PerformanceAttributes import PerformanceAttributes
from parsecore.Rulesets.Difficulty.PerformanceCalculator import PerformanceCalculator
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Mods.IApplicableToDifficulty import IApplicableToDifficulty
from parsecore.Rulesets.Mods.ModClassic import ModClassic
from parsecore.Rulesets.Mods.ModEasy import ModEasy
from parsecore.Rulesets.Mods.ModFlashlight import ModFlashlight
from parsecore.Rulesets.Mods.ModHidden import ModHidden
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Rulesets.Taiko.Difficulty.TaikoDifficultyAttributes import (
    TaikoDifficultyAttributes,
)
from parsecore.Rulesets.Taiko.Difficulty.TaikoPerformanceAttributes import (
    TaikoPerformanceAttributes,
)
from parsecore.Rulesets.Taiko.Scoring.TaikoHitWindows import TaikoHitWindows
from parsecore.Scoring.ScoreInfo import ScoreInfo
from parsecore.Utils import ModUtils

# The one-tailed 99% critical value of the normal distribution.
DEVIATION_CONFIDENCE_Z = 2.32634787404

TAIKO_RULESET_ID = 1


class TaikoPerformanceCalculator(PerformanceCalculator):
    """Calculates what a taiko score is worth."""

    def __init__(self) -> None:
        """Create the calculator."""
        self._count_great = 0
        self._count_ok = 0
        self._count_meh = 0
        self._count_miss = 0
        self._estimated_unstable_rate: float | None = None
        self._clock_rate = 1.0
        self._great_hit_window = 0.0
        self._total_difficult_hits = 0.0

    @property
    def _total_hits(self) -> int:
        """Return how many objects the player was judged on."""
        return (
            self._count_great + self._count_ok + self._count_meh + self._count_miss
        )

    def CreatePerformanceAttributes(
        self, score: ScoreInfo, attributes: DifficultyAttributes
    ) -> PerformanceAttributes:
        """Return what a taiko score is worth.

        Args:
            score: The score to evaluate.
            attributes: The difficulty of the beatmap it was set on.

        Returns:
            The performance breakdown.
        """
        mods = score.Mods
        attributes = cast(TaikoDifficultyAttributes, attributes)

        self._count_great = score.GetCount(HitResult.Great)
        self._count_ok = score.GetCount(HitResult.Ok)
        self._count_meh = score.GetCount(HitResult.Meh)
        self._count_miss = max(0, score.GetCount(HitResult.Miss))

        self._clock_rate = ModUtils.CalculateRateWithMods(mods)

        difficulty = score.BeatmapInfo.Difficulty.Clone()
        for mod in mods:
            if isinstance(mod, IApplicableToDifficulty):
                mod.ApplyToDifficulty(difficulty)

        hit_windows = TaikoHitWindows()
        hit_windows.SetDifficulty(difficulty.OverallDifficulty)
        self._great_hit_window = (
            hit_windows.WindowFor(HitResult.Great) / self._clock_rate
        )

        self._estimated_unstable_rate = (
            None
            if self._count_great == 0 or self._great_hit_window <= 0
            else self._deviation_upper_bound(self._count_great / self._total_hits) * 10
        )

        # Only the part of the beatmap that actually demanded something counts
        # towards length; a map whose difficulty sits in a few spikes is short.
        self._total_difficult_hits = self._total_hits * attributes.ConsistencyFactor

        is_convert = score.BeatmapInfo.RulesetID != 1
        is_classic = any(m for m in mods if isinstance(m, ModClassic))

        difficulty_value = (
            self._compute_difficulty_value(score, attributes, is_convert, is_classic)
            * 1.08
        )
        accuracy_value = self._compute_accuracy_value(score, attributes, is_convert) * 1.1

        return TaikoPerformanceAttributes(
            Total=difficulty_value + accuracy_value,
            Difficulty=difficulty_value,
            Accuracy=accuracy_value,
            EstimatedUnstableRate=self._estimated_unstable_rate,
        )

    def _compute_difficulty_value(
        self, score: ScoreInfo, attributes: TaikoDifficultyAttributes, is_convert: bool, is_classic: bool
    ) -> float:
        """Return what the beatmap's difficulty is worth to this score.

        Args:
            score: The score was set with.
            attributes: The beatmap's difficulty.
            is_convert: Whether the beatmap was written for another ruleset.
            is_classic: Whether the score was set with the classic mod.
        """
        estimated_ur = self._estimated_unstable_rate
        if estimated_ur is None or self._total_difficult_hits == 0:
            return 0.0

        # A rhythm-heavy beatmap played loosely is not really being read, so
        # the rating is pulled back towards what the timing supports.
        rhythm_expected_unstable_rate = self._deviation_upper_bound(1.0) * 10
        rhythm_maximum_unstable_rate = self._deviation_upper_bound(0.8) * 10

        rhythm_factor = DiffUtils.ReverseLerp(
            attributes.RhythmDifficulty / attributes.StarRating, 0.15, 0.4
        )
        rhythm_penalty = 1 - DiffUtils.Logistic(
            estimated_ur,
            midpoint_offset=(
                rhythm_expected_unstable_rate + rhythm_maximum_unstable_rate
            )
            / 2,
            multiplier=10
            / (rhythm_maximum_unstable_rate - rhythm_expected_unstable_rate),
            max_value=0.25 * DiffUtils.Pow(rhythm_factor, 3),
        )

        base_difficulty = (
            5 * max(1.0, attributes.StarRating * rhythm_penalty / 0.110) - 4.0
        )
        difficulty_value = min(
            DiffUtils.Pow(base_difficulty, 3) / 69052.51,
            DiffUtils.Pow(base_difficulty, 2.25) / 1250.0,
        )
        difficulty_value *= 1 + 0.10 * max(0.0, attributes.StarRating - 10)

        length_bonus = 1 + 0.25 * self._total_difficult_hits / (
            self._total_difficult_hits + 4000
        )
        difficulty_value *= length_bonus

        miss_penalty = 0.97 + 0.03 * self._total_difficult_hits / (
            self._total_difficult_hits + 1500
        )
        difficulty_value *= DiffUtils.Pow(miss_penalty, self._count_miss)

        if any(m for m in score.Mods if isinstance(m, ModHidden)):
            hidden_bonus = 0.025 if is_convert else 0.1

            if not any(m for m in score.Mods if isinstance(m, ModFlashlight)):
                if not is_classic:
                    hidden_bonus *= 0.2

                if any(m for m in score.Mods if isinstance(m, ModEasy)) and is_classic:
                    hidden_bonus *= 0.5

            difficulty_value *= 1.0 + hidden_bonus

        if any(m for m in score.Mods if isinstance(m, ModFlashlight)):
            difficulty_value *= max(1.0, 1.050 - min(attributes.MonoStaminaFactor / 50, 1.0) * length_bonus)

        # A beatmap leaning on single-colour runs punishes loose timing harder,
        # because there is no hand change to hide behind.
        mono_acc_scaling_exponent = 2 + attributes.MonoStaminaFactor
        mono_acc_scaling_shift = 500 - 100 * (attributes.MonoStaminaFactor * 3)

        return difficulty_value * DiffUtils.Pow(
            DiffUtils.Erf(
                mono_acc_scaling_shift
                / (DiffUtils.SQRT2 * estimated_ur)
            ),
            mono_acc_scaling_exponent,
        )

    def _compute_accuracy_value(
        self, score: ScoreInfo, attributes: TaikoDifficultyAttributes, is_convert: bool
    ) -> float:
        """Return what the player's timing is worth on its own.

        Args:
            score: The score was set with.
            attributes: The beatmap's difficulty.
            is_convert: Whether the beatmap was written for another ruleset.
        """
        if self._great_hit_window <= 0 or self._estimated_unstable_rate is None:
            return 0.0

        accuracy_value = 470 * DiffUtils.Pow(0.9885, self._estimated_unstable_rate)

        accuracy_value *= (
            1
            + DiffUtils.Pow(50 / self._estimated_unstable_rate, 2)
            * DiffUtils.Pow(attributes.StarRating, 2.8)
            / 600
        )

        if any(m for m in score.Mods if isinstance(m, ModHidden)) and not is_convert:
            accuracy_value *= 1.075

        accuracy_value *= 1 + 0.3 * self._total_difficult_hits / (
            self._total_difficult_hits + 4000
        )

        memory_length_bonus = min(
            1.15, DiffUtils.Pow(self._total_hits / 1500.0, 0.3)
        )
        if (
            any(m for m in score.Mods if isinstance(m, ModFlashlight))
            and any(m for m in score.Mods if isinstance(m, ModHidden))
            and not is_convert
        ):
            accuracy_value *= max(1.0, 1.05 * memory_length_bonus)

        return accuracy_value

    def _deviation_upper_bound(self, accuracy: float) -> float:
        """Return the loosest timing that could still have reached an accuracy.

        The count of good hits is treated as a sample, and its lower confidence
        bound is turned back into how far off the player's hits must have been.

        Args:
            accuracy: The fraction of hits that were judged great.
        """
        z = DEVIATION_CONFIDENCE_Z
        n = self._total_hits
        p = accuracy

        lower_bound = (n * p + z * z / 2) / (n + z * z) - z / (n + z * z) * math.sqrt(
            n * p * (1 - p) + z * z / 4
        )

        return self._great_hit_window / (DiffUtils.SQRT2 * DiffUtils.ErfInv(lower_bound))
