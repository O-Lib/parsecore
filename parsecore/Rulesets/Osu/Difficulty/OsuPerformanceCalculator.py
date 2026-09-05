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

from parsecore.Rulesets.Difficulty.PerformanceCalculator import PerformanceCalculator
from parsecore.Rulesets.Difficulty.Skills.HarmonicSkill import HarmonicSkill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Mods.ModScoreV2 import ModScoreV2
from parsecore.Rulesets.Osu.Difficulty.OsuDifficultyCalculator import (
    PERFORMANCE_BASE_MULTIPLIER,
    PERFORMANCE_NORM_EXPONENT,
    SumCognitionDifficulty,
)
from parsecore.Rulesets.Osu.Difficulty.OsuLegacyScoreMissCalculator import (
    OsuLegacyScoreMissCalculator,
)
from parsecore.Rulesets.Osu.Difficulty.OsuPerformanceAttributes import (
    OsuPerformanceAttributes,
)
from parsecore.Rulesets.Osu.Difficulty.Skills.Flashlight import Flashlight
from parsecore.Rulesets.Osu.Mods.OsuModAutopilot import OsuModAutopilot
from parsecore.Rulesets.Osu.Mods.OsuModBlinds import OsuModBlinds
from parsecore.Rulesets.Osu.Mods.OsuModClassic import OsuModClassic
from parsecore.Rulesets.Osu.Mods.OsuModFlashlight import OsuModFlashlight
from parsecore.Rulesets.Osu.Mods.OsuModNoFail import OsuModNoFail
from parsecore.Rulesets.Osu.Mods.OsuModRelax import OsuModRelax
from parsecore.Rulesets.Osu.Mods.OsuModSpunOut import OsuModSpunOut
from parsecore.Rulesets.Osu.Mods.OsuModTraceable import OsuModTraceable
from parsecore.Rulesets.Osu.Objects.OsuHitObject import (
    PREEMPT_MAX,
    PREEMPT_MID,
    PREEMPT_MIN,
)
from parsecore.Rulesets.Osu.Scoring.OsuHitWindows import OsuHitWindows
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Utils.Interpolation import DoubleLerp

# The 99% one-tailed critical value of the normal distribution.
Z_99 = 2.32634787404


def DifficultyToPerformance(difficulty: float) -> float:
    """Return the performance an aim difficulty value is worth.

    Args:
        difficulty: The aim difficulty value.
    """
    return 4.0 * DiffUtils.Pow(difficulty, 3)


class OsuPerformanceCalculator(PerformanceCalculator):
    """Calculates what an osu! score is worth."""

    def __init__(self) -> None:
        """Create the calculator."""
        self._using_classic_slider_accuracy = False
        self._using_score_v2 = False
        self._accuracy = 1.0
        self._score_max_combo = 0
        self._count_great = 0
        self._count_ok = 0
        self._count_meh = 0
        self._count_miss = 0
        self._count_slider_tick_miss = 0
        self._count_slider_ends_dropped = 0
        self._effective_miss_count = 0.0
        self._clock_rate = 1.0
        self._great_hit_window = 0.0
        self._ok_hit_window = 0.0
        self._meh_hit_window = 0.0
        self._overall_difficulty = 0.0
        self._approach_rate = 0.0
        self._drain_rate = 0.0
        self._speed_deviation: float | None = None
        self._aim_estimated_slider_breaks = 0.0
        self._speed_estimated_slider_breaks = 0.0

    @property
    def _total_hits(self) -> int:
        """Return how many objects were judged."""
        return (
            self._count_great + self._count_ok + self._count_meh + self._count_miss
        )

    @property
    def _total_successful_hits(self) -> int:
        """Return how many objects were hit at all."""
        return self._count_great + self._count_ok + self._count_meh

    @property
    def _total_imperfect_hits(self) -> int:
        """Return how many objects were not hit perfectly."""
        return self._count_ok + self._count_meh + self._count_miss

    def CreatePerformanceAttributes(
        self, score, attributes
    ) -> OsuPerformanceAttributes:
        """Return what a score is worth.

        Args:
            score: The score to evaluate.
            attributes: The beatmap's osu! difficulty attributes.
        """
        mods = list(score.Mods)

        self._using_classic_slider_accuracy = any(
            isinstance(m, OsuModClassic) and getattr(m, "NoSliderHeadAccuracy", False)
            for m in mods
        )
        self._using_score_v2 = any(isinstance(m, ModScoreV2) for m in mods)

        self._accuracy = min(max(score.Accuracy, 0.0), 1.0)
        self._score_max_combo = min(max(score.MaxCombo, 0), attributes.MaxCombo)

        self._count_great = score.GetCount(HitResult.Great)
        self._count_ok = score.GetCount(HitResult.Ok)
        self._count_meh = score.GetCount(HitResult.Meh)
        self._count_miss = score.GetCount(HitResult.Miss)
        self._count_slider_ends_dropped = attributes.SliderCount - score.GetCount(
            HitResult.SliderTailHit
        )
        self._count_slider_tick_miss = score.GetCount(HitResult.LargeTickMiss)

        difficulty = score.BeatmapDifficulty.Clone()
        for mod in mods:
            apply = getattr(mod, "ApplyToDifficulty", None)
            if callable(apply):
                apply(difficulty)

        self._clock_rate = _clock_rate_with_mods(mods)

        hit_windows = OsuHitWindows()
        hit_windows.SetDifficulty(difficulty.OverallDifficulty)
        self._great_hit_window = (
            hit_windows.WindowFor(HitResult.Great) / self._clock_rate
        )
        self._ok_hit_window = hit_windows.WindowFor(HitResult.Ok) / self._clock_rate
        self._meh_hit_window = hit_windows.WindowFor(HitResult.Meh) / self._clock_rate

        self._approach_rate = _rate_adjusted_approach_rate(
            difficulty.ApproachRate, self._clock_rate
        )
        self._overall_difficulty = (79.5 - self._great_hit_window) / 6
        self._drain_rate = difficulty.DrainRate

        combo_based_estimated_miss_count = self._combo_based_estimated_miss_count(
            attributes
        )

        if (
            self._using_classic_slider_accuracy
            and not self._using_score_v2
            and getattr(score, "LegacyTotalScore", None) is not None
        ):
            # An osu!stable score records a total but not where the combo
            # broke, and what the total falls short by says more than the
            # combo alone does.
            self._effective_miss_count = OsuLegacyScoreMissCalculator(
                score, attributes
            ).Calculate()
        else:
            self._effective_miss_count = combo_based_estimated_miss_count

        self._effective_miss_count = max(
            self._count_miss, self._effective_miss_count
        )
        self._effective_miss_count = min(
            self._total_hits, self._effective_miss_count
        )
        self._effective_miss_count = max(0.0, self._effective_miss_count)

        if self._effective_miss_count > 0:
            self._aim_estimated_slider_breaks = self._estimated_slider_breaks(
                attributes.AimTopWeightedSliderFactor, attributes
            )
            self._speed_estimated_slider_breaks = self._estimated_slider_breaks(
                attributes.SpeedTopWeightedSliderFactor, attributes
            )

        multiplier = PERFORMANCE_BASE_MULTIPLIER

        if any(isinstance(m, OsuModNoFail) for m in mods):
            multiplier *= max(0.90, 1.0 - 0.02 * self._effective_miss_count)

        if any(isinstance(m, OsuModSpunOut) for m in mods) and self._total_hits > 0:
            multiplier *= 1.0 - DiffUtils.Pow(
                attributes.SpinnerCount / self._total_hits, 0.85
            )

        if any(isinstance(m, OsuModRelax) for m in mods):
            # Relax turns oks and mehs into what are effectively combo breaks.
            # OD 13.33 is where the great window reaches zero.
            ok_multiplier = 0.75 * max(
                0.0,
                1 - self._overall_difficulty / 13.33
                if self._overall_difficulty > 0.0
                else 1.0,
            )
            meh_multiplier = max(
                0.0,
                1 - DiffUtils.Pow(self._overall_difficulty / 13.33, 5)
                if self._overall_difficulty > 0.0
                else 1.0,
            )
            self._effective_miss_count = min(
                self._effective_miss_count
                + self._count_ok * ok_multiplier
                + self._count_meh * meh_multiplier,
                self._total_hits,
            )

        self._speed_deviation = self._calculate_speed_deviation(attributes)

        aim_value = self._compute_aim_value(mods, attributes)
        speed_value = self._compute_speed_value(mods, attributes)
        accuracy_value = self._compute_accuracy_value(mods, attributes)
        reading_value = self._compute_reading_value(attributes)
        flashlight_value = self._compute_flashlight_value(mods, attributes)

        cognition_value = SumCognitionDifficulty(reading_value, flashlight_value)

        total_value = (
            DiffUtils.Norm(
                PERFORMANCE_NORM_EXPONENT,
                aim_value,
                speed_value,
                accuracy_value,
                cognition_value,
            )
            * multiplier
        )

        return OsuPerformanceAttributes(
            Total=total_value,
            Aim=aim_value,
            Speed=speed_value,
            Accuracy=accuracy_value,
            Flashlight=flashlight_value,
            Reading=reading_value,
            EffectiveMissCount=self._effective_miss_count,
            ComboBasedEstimatedMissCount=combo_based_estimated_miss_count,
            AimEstimatedSliderBreaks=self._aim_estimated_slider_breaks,
            SpeedEstimatedSliderBreaks=self._speed_estimated_slider_breaks,
            SpeedDeviation=self._speed_deviation,
        )

    def _compute_aim_value(self, mods: list, attributes) -> float:
        """Return the aim portion of the score's performance.

        Args:
            mods: The mods the score was set with.
            attributes: The beatmap's difficulty attributes.
        """
        if any(isinstance(m, OsuModAutopilot) for m in mods):
            return 0.0

        aim_difficulty = attributes.AimDifficulty

        if attributes.SliderCount > 0 and attributes.AimDifficultSliderCount > 0:
            if self._using_classic_slider_accuracy:
                # Classic scores cannot report dropped ends, so every point of
                # missing combo is treated as a dropped difficult slider.
                maximum_possible_dropped_sliders = self._total_imperfect_hits
                estimate = min(
                    max(
                        min(
                            maximum_possible_dropped_sliders,
                            attributes.MaxCombo - self._score_max_combo,
                        ),
                        0,
                    ),
                    attributes.AimDifficultSliderCount,
                )
            else:
                # Tick misses count too; plain misses do not, because missing a
                # slider head is punished harshly on its own.
                estimate = min(
                    max(
                        self._count_slider_ends_dropped + self._count_slider_tick_miss,
                        0,
                    ),
                    attributes.AimDifficultSliderCount,
                )

            slider_nerf_factor = (1 - attributes.SliderFactor) * DiffUtils.Pow(
                1 - estimate / attributes.AimDifficultSliderCount, 3
            ) + attributes.SliderFactor
            aim_difficulty *= slider_nerf_factor

        aim_value = DifficultyToPerformance(aim_difficulty)

        length_bonus = (
            0.95
            + 0.35 * min(1.0, self._total_hits / 2000.0)
            + (
                math.log10(self._total_hits / 2000.0) * 0.5
                if self._total_hits > 2000
                else 0.0
            )
        )
        aim_value *= length_bonus

        if self._effective_miss_count > 0:
            relevant_miss_count = min(
                self._effective_miss_count + self._aim_estimated_slider_breaks,
                self._total_imperfect_hits + self._count_slider_tick_miss,
            )
            aim_value *= _miss_penalty(
                relevant_miss_count, attributes.AimDifficultStrainCount
            )

        # Traceable's bonus is dropped under blinds, where nothing is visible.
        if any(isinstance(m, OsuModBlinds) for m in mods):
            aim_value *= 1.3 + (
                self._total_hits
                * (0.0016 / (1 + 2 * self._effective_miss_count))
                * DiffUtils.Pow(self._accuracy, 16)
            ) * (1 - 0.003 * self._drain_rate * self._drain_rate)
        elif any(isinstance(m, OsuModTraceable) for m in mods):
            aim_value *= 1.0 + self._traceable_bonus(attributes.SliderFactor)

        return aim_value * self._accuracy

    def _compute_speed_value(self, mods: list, attributes) -> float:
        """Return the speed portion of the score's performance.

        Args:
            mods: The mods the score was set with.
            attributes: The beatmap's difficulty attributes.
        """
        if any(isinstance(m, OsuModRelax) for m in mods) or self._speed_deviation is None:
            return 0.0

        speed_value = HarmonicSkill.DifficultyToPerformance(attributes.SpeedDifficulty)

        if self._effective_miss_count > 0:
            relevant_miss_count = min(
                self._effective_miss_count + self._speed_estimated_slider_breaks,
                self._total_imperfect_hits + self._count_slider_tick_miss,
            )
            speed_value *= _miss_penalty(
                relevant_miss_count, attributes.SpeedDifficultStrainCount
            )

        if any(isinstance(m, OsuModBlinds) for m in mods):
            # Scaling speed by object count under blinds would be too strong.
            speed_value *= 1.12

        speed_value *= self._speed_high_deviation_nerf(attributes)

        # A tighter effective window is implied by a higher speed rating: a
        # speed rating of 4 corresponds to roughly a 20 ms window, or OD 10.
        effective_hit_window = 20 * DiffUtils.Pow(
            4 / attributes.SpeedDifficulty, 0.35
        ) if attributes.SpeedDifficulty else 0.0

        effective_accuracy = DiffUtils.Erf(
            effective_hit_window / self._speed_deviation
        ) if self._speed_deviation else 0.0

        return speed_value * DiffUtils.Pow(effective_accuracy, 2)

    def _compute_accuracy_value(self, mods: list, attributes) -> float:
        """Return the accuracy portion of the score's performance.

        Args:
            mods: The mods the score was set with.
            attributes: The beatmap's difficulty attributes.
        """
        if any(isinstance(m, OsuModRelax) for m in mods):
            return 0.0

        # Only objects judged on timing count towards this.
        amount_hit_objects_with_accuracy = attributes.HitCircleCount
        if not self._using_classic_slider_accuracy or self._using_score_v2:
            amount_hit_objects_with_accuracy += attributes.SliderCount

        if amount_hit_objects_with_accuracy > 0:
            better_accuracy_percentage = (
                (
                    self._count_great
                    - max(self._total_hits - amount_hit_objects_with_accuracy, 0)
                )
                * 6
                + self._count_ok * 2
                + self._count_meh
            ) / (amount_hit_objects_with_accuracy * 6)
        else:
            better_accuracy_percentage = 0.0

        # The formula above can go negative; that is worth nothing, not less.
        better_accuracy_percentage = max(0.0, better_accuracy_percentage)

        accuracy_value = (
            DiffUtils.Pow(1.52163, self._overall_difficulty)
            * DiffUtils.Pow(better_accuracy_percentage, 24)
            * 2.83
        )

        # Holding accuracy over more objects is harder.
        accuracy_value *= (
            DiffUtils.Pow(amount_hit_objects_with_accuracy / 1000.0, 0.3)
            if amount_hit_objects_with_accuracy < 1000
            else DiffUtils.Pow(amount_hit_objects_with_accuracy / 1000.0, 0.1)
        )

        if any(isinstance(m, OsuModBlinds) for m in mods):
            accuracy_value *= 1.14
        elif any(isinstance(m, OsuModTraceable) for m in mods):
            accuracy_value *= 1 + 0.08 * DiffUtils.ReverseLerp(
                self._approach_rate, 11.5, 10
            )

        return accuracy_value

    def _compute_reading_value(self, attributes) -> float:
        """Return the reading portion of the score's performance.

        Args:
            attributes: The beatmap's difficulty attributes.
        """
        reading_value = HarmonicSkill.DifficultyToPerformance(
            attributes.ReadingDifficulty
        )

        if self._effective_miss_count > 0:
            reading_value *= _miss_penalty(
                self._effective_miss_count + self._aim_estimated_slider_breaks,
                attributes.ReadingDifficultNoteCount,
            )

        # Reading scales harshly with accuracy.
        return reading_value * DiffUtils.Pow(self._accuracy, 3)

    def _compute_flashlight_value(self, mods: list, attributes) -> float:
        """Return the flashlight portion of the score's performance.

        Args:
            mods: The mods the score was set with.
            attributes: The beatmap's difficulty attributes.
        """
        if not any(isinstance(m, OsuModFlashlight) for m in mods):
            return 0.0

        flashlight_value = Flashlight.DifficultyToPerformance(
            attributes.FlashlightDifficulty
        )

        if self._effective_miss_count > 0 and self._total_hits > 0:
            flashlight_value *= 0.97 * DiffUtils.Pow(
                1
                - DiffUtils.Pow(self._effective_miss_count / self._total_hits, 0.775),
                DiffUtils.Pow(self._effective_miss_count, 0.875),
            )

        flashlight_value *= self._combo_scaling_factor(attributes)

        # Flashlight scales only slightly with accuracy.
        return flashlight_value * (0.5 + self._accuracy / 2.0)

    def _combo_based_estimated_miss_count(self, attributes) -> float:
        """Estimate how many mistakes a score's combo implies.

        A slider break costs combo without recording a miss, so the combo a
        score reached says more about its mistakes than its miss count does.

        Args:
            attributes: The beatmap's difficulty attributes.
        """
        if attributes.SliderCount <= 0:
            return float(self._count_miss)

        miss_count = float(self._count_miss)

        if self._using_classic_slider_accuracy:
            # Hard sliders tend to have dropped ends; easy ones tend to break.
            likely_missed_sliderend_portion = 0.04 + 0.06 * DiffUtils.Pow(
                min(attributes.AimTopWeightedSliderFactor, 1), 2
            )

            # Dropped tails cost no combo, so a full combo sits below the max.
            full_combo_threshold = attributes.MaxCombo - min(
                4 + likely_missed_sliderend_portion * attributes.SliderCount,
                attributes.SliderCount,
            )

            if self._score_max_combo < full_combo_threshold:
                miss_count = full_combo_threshold / max(1.0, self._score_max_combo)

            miss_count = min(miss_count, self._total_imperfect_hits)

            # Every slider is worth at least two combo under classic rules, so
            # losing a single point of combo cannot have been a slider break.
            max_possible_slider_breaks = min(
                attributes.SliderCount,
                (attributes.MaxCombo - self._score_max_combo) // 2,
            )
            slider_breaks = miss_count - self._count_miss
            if slider_breaks > max_possible_slider_breaks:
                miss_count = self._count_miss + max_possible_slider_breaks
        else:
            full_combo_threshold = (
                attributes.MaxCombo - self._count_slider_ends_dropped
            )
            if self._score_max_combo < full_combo_threshold:
                miss_count = full_combo_threshold / max(1.0, self._score_max_combo)

            # Tick misses break combo too.
            miss_count = min(
                miss_count, self._count_slider_tick_miss + self._count_miss
            )

        return miss_count

    def _estimated_slider_breaks(
        self, top_weighted_slider_factor: float, attributes
    ) -> float:
        """Estimate how many of a score's mistakes were slider breaks.

        Args:
            top_weighted_slider_factor: How much of the difficulty sits on
                sliders for the skill in question.
            attributes: The beatmap's difficulty attributes.
        """
        non_miss_mistakes = self._count_ok + self._count_meh

        if not self._using_classic_slider_accuracy or non_miss_mistakes == 0:
            return 0.0

        missed_combo_percent = 1.0 - self._score_max_combo / attributes.MaxCombo

        estimated_slider_breaks = min(
            non_miss_mistakes, self._effective_miss_count * top_weighted_slider_factor
        )

        # More oks and mehs make slider breaks likelier. The added constants
        # keep the ratio stable at the extremes.
        non_miss_mistake_adjustment = (
            non_miss_mistakes - estimated_slider_breaks + 4.5
        ) / (non_miss_mistakes + 4)

        # Around a single effective miss, score-based reasoning is reliable
        # enough that extra breaks are unlikely.
        estimated_slider_breaks *= DiffUtils.Smoothstep(
            self._effective_miss_count, 1, 2
        )

        return (
            estimated_slider_breaks
            * non_miss_mistake_adjustment
            * DiffUtils.Logistic(missed_combo_percent, 0.33, 15)
        )

    def _calculate_speed_deviation(self, attributes) -> float | None:
        """Estimate the player's tapping deviation, in milliseconds.

        Args:
            attributes: The beatmap's difficulty attributes.
        """
        if self._total_successful_hits == 0:
            return None

        speed_note_count = attributes.SpeedNoteCount
        speed_note_count += (self._total_hits - attributes.SpeedNoteCount) * 0.1

        # Assume the worst case: every mistake fell on a speed note.
        relevant_count_miss = min(self._count_miss, speed_note_count)
        relevant_count_meh = min(
            self._count_meh, speed_note_count - relevant_count_miss
        )
        relevant_count_ok = min(
            self._count_ok,
            speed_note_count - relevant_count_miss - relevant_count_meh,
        )
        relevant_count_great = max(
            0.0,
            speed_note_count
            - relevant_count_miss
            - relevant_count_meh
            - relevant_count_ok,
        )

        return self._calculate_deviation(
            relevant_count_great, relevant_count_ok, relevant_count_meh
        )

    def _calculate_deviation(
        self,
        relevant_count_great: float,
        relevant_count_ok: float,
        relevant_count_meh: float,
    ) -> float | None:
        """Return the deviation implied by a judgement distribution.

        Args:
            relevant_count_great: How many greats fell on speed notes.
            relevant_count_ok: How many oks fell on speed notes.
            relevant_count_meh: How many mehs fell on speed notes.
        """
        if relevant_count_great + relevant_count_ok + relevant_count_meh <= 0:
            return None

        n = max(1.0, relevant_count_great + relevant_count_ok)
        p = relevant_count_great / n

        # The lower bound we can be 99% confident the true proportion exceeds.
        p_lower_bound = min(
            p,
            (n * p + Z_99 * Z_99 / 2) / (n + Z_99 * Z_99)
            - Z_99
            / (n + Z_99 * Z_99)
            * math.sqrt(n * p * (1 - p) + Z_99 * Z_99 / 4),
        )

        if p_lower_bound > 0.01:
            # Greats and oks are assumed normally distributed.
            deviation = self._great_hit_window / (
                DiffUtils.SQRT2 * DiffUtils.ErfInv(p_lower_bound)
            )

            # Remove the tails that fall outside the ok window, which is the
            # deviation of a distribution truncated at plus or minus that window.
            ok_hit_window_tail_amount = (
                math.sqrt(2 / math.pi)
                * self._ok_hit_window
                * math.exp(
                    -0.5 * DiffUtils.Pow(self._ok_hit_window / deviation, 2)
                )
                / (
                    deviation
                    * DiffUtils.Erf(
                        self._ok_hit_window / (DiffUtils.SQRT2 * deviation)
                    )
                )
            )
            deviation *= math.sqrt(1 - ok_hit_window_tail_amount)
        else:
            # The limit for a score containing only oks.
            deviation = self._ok_hit_window / math.sqrt(3)

        # Mehs are assumed uniformly distributed across their window.
        meh_variance = (
            self._meh_hit_window * self._meh_hit_window
            + self._ok_hit_window * self._meh_hit_window
            + self._ok_hit_window * self._ok_hit_window
        ) / 3

        return math.sqrt(
            (
                (relevant_count_great + relevant_count_ok)
                * DiffUtils.Pow(deviation, 2)
                + relevant_count_meh * meh_variance
            )
            / (relevant_count_great + relevant_count_ok + relevant_count_meh)
        )

    def _speed_high_deviation_nerf(self, attributes) -> float:
        """Return a multiplier reducing speed value for imprecise tapping.

        Args:
            attributes: The beatmap's difficulty attributes.
        """
        if self._speed_deviation is None:
            return 0.0

        speed_value = HarmonicSkill.DifficultyToPerformance(attributes.SpeedDifficulty)

        # Performance beyond this point, relative to the deviation, is taken as
        # tapped imprecisely and scaled logarithmically.
        excess_speed_difficulty_cutoff = 100 + 220 * DiffUtils.Pow(
            22 / self._speed_deviation, 6.5
        )

        if speed_value <= excess_speed_difficulty_cutoff:
            return 1.0

        scale = 50.0
        adjusted_speed_value = scale * (
            math.log((speed_value - excess_speed_difficulty_cutoff) / scale + 1)
            + excess_speed_difficulty_cutoff / scale
        )

        # A deviation of 22 or below counts as tapped correctly.
        lerp = 1 - DiffUtils.ReverseLerp(self._speed_deviation, 22.0, 27.0)
        # osu! reaches for .NET's own lerp here, not the framework's.
        adjusted_speed_value = DoubleLerp(adjusted_speed_value, speed_value, lerp)

        return adjusted_speed_value / speed_value

    def _traceable_bonus(self, slider_factor: float = 1.0) -> float:
        """Return the bonus traceable earns at the score's approach rate.

        Args:
            slider_factor: How much of the aim difficulty sits on sliders.
        """
        high_ar_slider_visibility = 0.5 + (DiffUtils.Pow(slider_factor, 6) / 2)
        low_ar_slider_visibility = DiffUtils.Pow(slider_factor, 6)

        traceable_bonus = 0.0275
        traceable_bonus += (
            0.025 * (12.0 - max(self._approach_rate, 7)) * high_ar_slider_visibility
        )

        # Below approach rate 7 the object is visible, so reward less.
        if self._approach_rate < 7:
            traceable_bonus += (
                0.025 * (7.0 - max(self._approach_rate, 0)) * low_ar_slider_visibility
            )

        # Cap the value below approach rate 0 so it cannot grow without bound.
        if self._approach_rate < 0:
            traceable_bonus += (
                0.025
                * (1 - DiffUtils.Pow(1.5, self._approach_rate))
                * low_ar_slider_visibility
            )

        return traceable_bonus

    def _combo_scaling_factor(self, attributes) -> float:
        """Return how much of the maximum combo the score reached.

        Args:
            attributes: The beatmap's difficulty attributes.
        """
        if attributes.MaxCombo <= 0:
            return 1.0
        return min(
            DiffUtils.Pow(self._score_max_combo, 0.8)
            / DiffUtils.Pow(attributes.MaxCombo, 0.8),
            1.0,
        )


def _miss_penalty(miss_count: float, difficult_strain_count: float) -> float:
    """Return the penalty for missing, scaled by how many hard sections exist.

    A player is assumed to miss on the hardest parts, so a map with few hard
    sections is punished more per miss than one with many.

    Args:
        miss_count: The effective number of mistakes.
        difficult_strain_count: How many sections carry the difficulty.
    """
    divisor = 4 * math.log(max(1.0, difficult_strain_count))

    # With no difficult sections at all the divisor is zero; osu! divides by it
    # anyway and lands on a penalty of zero, so match that rather than guard.
    if divisor == 0:
        return 0.0

    return 0.93 / (miss_count / divisor + 1)


def _rate_adjusted_approach_rate(approach_rate: float, clock_rate: float) -> float:
    """Return the approach rate a score effectively played at.

    Args:
        approach_rate: The beatmap's approach rate.
        clock_rate: The rate the beatmap was played at.
    """
    from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty

    preempt = (
        BeatmapDifficulty.DifficultyRange(
            approach_rate, PREEMPT_MAX, PREEMPT_MID, PREEMPT_MIN
        )
        / clock_rate
    )
    return BeatmapDifficulty.InverseDifficultyRange(
        preempt, PREEMPT_MAX, PREEMPT_MID, PREEMPT_MIN
    )


def _clock_rate_with_mods(mods: list) -> float:
    """Return the rate a set of mods plays a beatmap at.

    Args:
        mods: The mods the score was set with.
    """
    rate = 1.0
    for mod in mods:
        apply = getattr(mod, "ApplyToRate", None)
        if callable(apply):
            rate = apply(0.0, rate)
    return rate
