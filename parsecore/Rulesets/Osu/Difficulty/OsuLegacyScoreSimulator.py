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

from parsecore.Beatmaps.Beatmap import Beatmap
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Mods.Mod import Mod
from parsecore.Rulesets.Mods.ModScoreV2 import ModScoreV2
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    CalculateDifficultyPeppyStars,
)
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
from parsecore.Rulesets.Objects.Types.IHasPath import IHasPath
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
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.SliderHeadCircle import SliderHeadCircle
from parsecore.Rulesets.Osu.Objects.SliderRepeat import SliderRepeat
from parsecore.Rulesets.Osu.Objects.SliderTailCircle import SliderTailCircle
from parsecore.Rulesets.Osu.Objects.SliderTick import SliderTick
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner
from parsecore.Rulesets.Osu.Objects.SpinnerTick import SpinnerBonusTick, SpinnerTick
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Rulesets.Scoring.Legacy.ILegacyScoreSimulator import (
    ILegacyScoreSimulator,
)
from parsecore.Rulesets.Scoring.Legacy.LegacyScoreAttributes import (
    LegacyScoreAttributes,
)
from parsecore.Rulesets.Scoring.ScoreProcessor import GetBaseScoreForResult

# The fastest a spinner can be turned, in rotations per second.
MAXIMUM_ROTATIONS_PER_SECOND = 477.0 / 60

MINIMUM_ROTATIONS_PER_SECOND = 3


class OsuLegacyScoreSimulator(ILegacyScoreSimulator):
    """Simulates a perfect osu! play under osu!stable's first scoring system."""

    def __init__(self) -> None:
        """Create the simulator."""
        self._legacy_bonus_score = 0
        self._standardised_bonus_score = 0
        self._combo = 0
        self._score_multiplier = 0.0

    def Simulate(self, workingBeatmap: WorkingBeatmap, playable_beatmap: Beatmap) -> LegacyScoreAttributes:
        """Return the highest osu!stable score a beatmap allows.

        Args:
            workingBeatmap: The working beatmap.
            playable_beatmap: A playable version of the beatmap for the ruleset.
        """
        base_beatmap = workingBeatmap.Beatmap

        count_normal = 0
        count_slider = 0
        count_spinner = 0

        for hit_object in workingBeatmap.Beatmap.HitObjects:
            if isinstance(hit_object, IHasPath):
                count_slider += 1
            elif isinstance(hit_object, IHasDuration):
                count_spinner += 1
            else:
                count_normal += 1

        object_count = count_normal + count_slider + count_spinner

        drain_length = 0

        if base_beatmap.HitObjects:
            break_length = sum(
                int(round(b.EndTime)) - int(round(b.StartTime))
                for b in base_beatmap.Breaks
            )
            # osu! divides two whole numbers here, truncating towards zero.
            drain_length = int(
                (
                    int(round(base_beatmap.HitObjects[-1].StartTime))
                    - int(round(base_beatmap.HitObjects[0].StartTime))
                    - break_length
                )
                / 1000
            )

        self._score_multiplier = CalculateDifficultyPeppyStars(
            base_beatmap.Difficulty, object_count, drain_length
        )

        attributes = LegacyScoreAttributes()

        for hit_object in playable_beatmap.HitObjects:
            self._simulate_hit(hit_object, attributes)

        attributes.BonusScoreRatio = (
            0.0
            if self._legacy_bonus_score == 0
            else float(self._standardised_bonus_score) / self._legacy_bonus_score
        )
        attributes.BonusScore = self._legacy_bonus_score
        attributes.MaxCombo = self._combo

        return attributes

    def _simulate_hit(self, hit_object: HitObject, attributes: LegacyScoreAttributes) -> None:
        """Add what one object is worth to the running score.

        Args:
            hit_object: The object being hit.
            attributes: The score being built up.
        """
        increase_combo = True
        add_score_combo_multiplier = False

        is_bonus = False
        bonus_result = HitResult.None_

        score_increase = 0

        if isinstance(hit_object, (SliderHeadCircle, SliderTailCircle, SliderRepeat)):
            score_increase = 30
        elif isinstance(hit_object, SliderTick):
            score_increase = 10
        elif isinstance(hit_object, SpinnerBonusTick):
            score_increase = 1100
            increase_combo = False
            is_bonus = True
            bonus_result = HitResult.LargeBonus
        elif isinstance(hit_object, SpinnerTick):
            score_increase = 100
            increase_combo = False
            is_bonus = True
            bonus_result = HitResult.SmallBonus
        elif isinstance(hit_object, Slider):
            for nested in hit_object.NestedHitObjects:
                self._simulate_hit(nested, attributes)

            score_increase = 300
            increase_combo = False
            add_score_combo_multiplier = True
        elif isinstance(hit_object, Spinner):
            # osu!lazer's spinner is more forgiving than osu!stable's, so the
            # ticks are worked out again here rather than read off the object.
            seconds_duration = hit_object.Duration / 1000

            # Every half spin the whole spinner allows.
            total_half_spins_possible = int(
                seconds_duration * MAXIMUM_ROTATIONS_PER_SECOND * 2
            )
            # The half spins needed to complete it, which earns a three hundred.
            half_spins_required_for_completion = int(
                seconds_duration * MINIMUM_ROTATIONS_PER_SECOND
            )
            # Another one and a half spins are needed before a bonus is paid.
            half_spins_required_before_bonus = half_spins_required_for_completion + 3

            for i in range(total_half_spins_possible):
                if (
                    i > half_spins_required_before_bonus
                    and (i - half_spins_required_before_bonus) % 2 == 0
                ):
                    self._simulate_hit(SpinnerBonusTick(), attributes)
                elif i > 1 and i % 2 == 0:
                    self._simulate_hit(SpinnerTick(), attributes)

            score_increase = 300
            add_score_combo_multiplier = True
        elif isinstance(hit_object, HitCircle):
            score_increase = 300
            add_score_combo_multiplier = True

        if add_score_combo_multiplier:
            # osu!stable divided two whole numbers here, losing the remainder;
            # that is reproduced deliberately.
            attributes.ComboScore += int(
                max(0, self._combo - 1) * (score_increase // 25 * self._score_multiplier)
            )

        if is_bonus:
            self._legacy_bonus_score += score_increase
            self._standardised_bonus_score += GetBaseScoreForResult(bonus_result)
        else:
            attributes.AccuracyScore += score_increase

        if increase_combo:
            self._combo += 1

    @staticmethod
    def GetLegacyScoreMultiplier(mods: list[Mod]) -> float:
        """Return what the mods multiply an osu!stable score by.

        Args:
            mods: The mods the score was set with.
        """

        score_v2 = any(isinstance(m, ModScoreV2) for m in mods)

        multiplier = 1.0

        for mod in mods:
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
