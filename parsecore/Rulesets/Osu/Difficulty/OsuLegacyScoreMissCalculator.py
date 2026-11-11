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

from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Mods.ModScoreV2 import ModScoreV2
from parsecore.Rulesets.Osu.Difficulty.OsuDifficultyAttributes import (
    OsuDifficultyAttributes,
)
from parsecore.Rulesets.Osu.Mods.OsuModAutopilot import OsuModAutopilot
from parsecore.Rulesets.Osu.Mods.OsuModDaycore import OsuModDaycore
from parsecore.Rulesets.Osu.Mods.OsuModDoubleTime import OsuModDoubleTime
from parsecore.Rulesets.Osu.Mods.OsuModEasy import OsuModEasy
from parsecore.Rulesets.Osu.Mods.OsuModFlashlight import OsuModFlashlight
from parsecore.Rulesets.Osu.Mods.OsuModHalfTime import OsuModHalfTime
from parsecore.Rulesets.Osu.Mods.OsuModHardRock import OsuModHardRock
from parsecore.Rulesets.Osu.Mods.OsuModHidden import OsuModHidden
from parsecore.Rulesets.Osu.Mods.OsuModNightcore import OsuModNightcore
from parsecore.Rulesets.Osu.Mods.OsuModNoFail import OsuModNoFail
from parsecore.Rulesets.Osu.Mods.OsuModRelax import OsuModRelax
from parsecore.Rulesets.Osu.Mods.OsuModSpunOut import OsuModSpunOut
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Scoring.ScoreInfo import ScoreInfo


class OsuLegacyScoreMissCalculator:
    """Estimates the combo breaks behind an osu!stable score."""

    def __init__(self, score: ScoreInfo, attributes: OsuDifficultyAttributes) -> None:
        """Create the calculator for one score.

        Args:
            score: The score to estimate for.
            attributes: The difficulty of the beatmap it was set on.
        """
        self._score = score
        self._attributes = attributes

    def Calculate(self) -> float:
        """Return how many combo breaks the score most likely hid."""

        if self._attributes.MaxCombo == 0 or self._score.LegacyTotalScore is None or self._score.LegacyTotalScore == 0:
            return 0.0

        score_v1_multiplier = self._attributes.LegacyScoreBaseMultiplier * self._getLegacyScoreMultiplier()
        relevant_combo_per_object = self._relevant_score_combo_per_object()

        maximum_miss_count = self._maximum_combo_based_miss_count()

        score_obtained_during_max_combo = self._score_at_combo(
            self._score.MaxCombo, relevant_combo_per_object, score_v1_multiplier
        )
        remaining_score = self._score.LegacyTotalScore - score_obtained_during_max_combo

        if remaining_score <= 0:
            return maximum_miss_count

        remaining_combo = self._attributes.MaxCombo - self._score.MaxCombo
        expected_remaining_score = self._score_at_combo(
            remaining_combo, relevant_combo_per_object, score_v1_multiplier
        )

        score_based_miss_count = expected_remaining_score / remaining_score

        # Below one break, the combo-based estimate decides whether this was a
        # full combo at all.
        score_based_miss_count = max(score_based_miss_count, 1.0)

        # A harsh combo-based estimate caps the result.
        return min(score_based_miss_count, maximum_miss_count)

    def _score_at_combo(
        self, combo: float, relevant_combo_per_object: float, score_v1_multiplier: float
    ) -> float:
        """Return the score a play would have reached at a given combo.

        Args:
            combo: The combo reached.
            relevant_combo_per_object: How much combo one object is worth.
            score_v1_multiplier: What the beatmap and mods scale the score by.
        """
        count_great = self._score.GetCount(HitResult.Great)
        count_ok = self._score.GetCount(HitResult.Ok)
        count_meh = self._score.GetCount(HitResult.Meh)
        count_miss = self._score.GetCount(HitResult.Miss)

        total_hits = count_great + count_ok + count_meh + count_miss

        estimated_objects = combo / relevant_combo_per_object - 1

        # The combo part of an osu!stable score is an arithmetic progression,
        # so it follows from the combo per object and the combo reached.
        combo_score = (
            (
                2 * (relevant_combo_per_object - 1)
                + (estimated_objects - 1) * relevant_combo_per_object
            )
            * estimated_objects / 2
            if relevant_combo_per_object > 0
            else 0.0
        )

        combo_score *= self._score.Accuracy * 300 / 25 * score_v1_multiplier

        objects_hit = (
            (total_hits - count_miss) * combo / self._attributes.MaxCombo
        )

        # The rest of the score does not depend on the combo at all.
        non_combo_score = (
            (300 + self._attributes.NestedScorePerObject)
            * self._score.Accuracy
            * objects_hit
        )

        return combo_score + non_combo_score

    def _relevant_score_combo_per_object(self) -> float:
        """Return how much combo one object of this beatmap is worth.

        Circles and sliders are assumed to be spread evenly, which keeps
        beatmaps whose sliders do not fit an arithmetic progression -- a buzz
        slider, say -- from throwing the estimate off.
        """
        combo_score = self._attributes.MaximumLegacyComboScore

        # Undo the score multipliers to get back to the raw progression.
        combo_score /= 300.0 / 25.0 * self._attributes.LegacyScoreBaseMultiplier

        max_combo = self._attributes.MaxCombo
        result = (max_combo - 2) * max_combo
        result /= max(max_combo + 2 * (combo_score - 1), 1)

        return result

    def _maximum_combo_based_miss_count(self) -> float:
        """Return a deliberately harsh estimate of the combo breaks.

        This exists to bound the score-based estimate where that one cannot
        give a sensible answer on its own.
        """
        count_miss = self._score.GetCount(HitResult.Miss)

        if self._attributes.SliderCount <= 0:
            return float(count_miss)

        count_ok = self._score.GetCount(HitResult.Ok)
        count_meh = self._score.GetCount(HitResult.Meh)

        total_imperfect_hits = count_ok + count_meh + count_miss

        miss_count = 0.0

        # Hard sliders are dropped at the end; easy ones are broken on.
        likely_missed_sliderend_portion = 0.04 + 0.06 * DiffUtils.Pow(
            min(self._attributes.AimTopWeightedSliderFactor, 1), 2
        )

        # A dropped slider tail costs no combo but earns none either, so a full
        # combo sits below the maximum. An old score does not say how many were
        # dropped, so it is estimated.
        full_combo_threshold = self._attributes.MaxCombo - min(
            4 + likely_missed_sliderend_portion * self._attributes.SliderCount,
            self._attributes.SliderCount,
        )

        if self._score.MaxCombo < full_combo_threshold:
            miss_count = DiffUtils.Pow(
                full_combo_threshold / max(1.0, self._score.MaxCombo), 2.5
            )

        # An old score cannot have more breaks than it has imperfect hits.
        miss_count = min(miss_count, total_imperfect_hits)

        # Every slider is worth at least two combo under classic rules, so a
        # score that lost only one combo cannot have broken on a slider it
        # must have dropped a tail.
        max_possible_slider_breaks = min(
            self._attributes.SliderCount,
            (self._attributes.MaxCombo - self._score.MaxCombo) // 2,
        )

        slider_breaks = miss_count - count_miss

        if slider_breaks > max_possible_slider_breaks:
            miss_count = count_miss + max_possible_slider_breaks

        return miss_count

    def _getLegacyScoreMultiplier(self) -> float:
        """Return what the mods multiply an osu!stable score by."""

        score_v2 = any(isinstance(m, ModScoreV2) for m in self._score.Mods)

        multiplier = 1.0

        for mod in self._score.Mods:
            if isinstance(mod, OsuModNoFail):
                multiplier *= 1.0 if score_v2 else 0.5
            elif isinstance(mod, OsuModEasy):
                multiplier *= 0.5
            elif isinstance(mod, (OsuModHalfTime, OsuModDaycore)):
                multiplier *= 0.3
            elif isinstance(mod, OsuModHidden):
                multiplier *= 1.06
            elif isinstance(mod, OsuModHardRock):
                multiplier *= 1.10 if score_v2 else 1.06
            elif isinstance(mod, (OsuModDoubleTime, OsuModNightcore)):
                multiplier *= 1.20 if score_v2 else 1.12
            elif isinstance(mod, OsuModFlashlight):
                multiplier *= 1.12
            elif isinstance(mod, OsuModSpunOut):
                multiplier *= 0.9
            elif isinstance(mod, (OsuModRelax, OsuModAutopilot)):
                return 0.0

        return multiplier
