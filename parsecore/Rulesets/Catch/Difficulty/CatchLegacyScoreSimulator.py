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
from parsecore.Rulesets.Catch.Mods.CatchModDaycore import CatchModDaycore
from parsecore.Rulesets.Catch.Mods.CatchModDoubleTime import CatchModDoubleTime
from parsecore.Rulesets.Catch.Mods.CatchModEasy import CatchModEasy
from parsecore.Rulesets.Catch.Mods.CatchModFlashlight import CatchModFlashlight
from parsecore.Rulesets.Catch.Mods.CatchModHalfTime import CatchModHalfTime
from parsecore.Rulesets.Catch.Mods.CatchModHardRock import CatchModHardRock
from parsecore.Rulesets.Catch.Mods.CatchModHidden import CatchModHidden
from parsecore.Rulesets.Catch.Mods.CatchModNightcore import CatchModNightcore
from parsecore.Rulesets.Catch.Mods.CatchModNoFail import CatchModNoFail
from parsecore.Rulesets.Catch.Mods.CatchModRelax import CatchModRelax
from parsecore.Rulesets.Catch.Objects.Banana import Banana, BananaShower
from parsecore.Rulesets.Catch.Objects.Droplet import Droplet, TinyDroplet
from parsecore.Rulesets.Catch.Objects.Fruit import Fruit
from parsecore.Rulesets.Catch.Objects.JuiceStream import JuiceStream
from parsecore.Rulesets.Catch.Scoring.CatchScoreProcessor import (
    GetBaseScoreForResult,
)
from parsecore.Rulesets.Mods.Mod import Mod
from parsecore.Rulesets.Mods.ModScoreV2 import ModScoreV2
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    CalculateDifficultyPeppyStars,
)
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
from parsecore.Rulesets.Objects.Types.IHasPath import IHasPath
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Rulesets.Scoring.Legacy.ILegacyScoreSimulator import (
    ILegacyScoreSimulator,
)
from parsecore.Rulesets.Scoring.Legacy.LegacyScoreAttributes import (
    LegacyScoreAttributes,
)


class CatchLegacyScoreSimulator(ILegacyScoreSimulator):
    """Simulates a perfect catch play under osu!stable's first scoring system."""

    def __init__(self) -> None:
        """Create the simulator."""
        self._legacy_bonus_score = 0
        self._standardised_bonus_score = 0
        self._combo = 0
        self._score_multiplier = 0.0

    def Simulate(self, workingBeatmap: WorkingBeatmap, playable_beatmap: Beatmap) -> LegacyScoreAttributes:
        """Return the highest osu!stable score a beatmap allows.

        Args:
            workingBeatmap: The beatmap as it was decoded.
            playable_beatmap: The same beatmap as catch plays it.
        """
        count_normal = 0
        count_slider = 0
        count_spinner = 0

        beatmap = workingBeatmap.Beatmap
        for hit_object in beatmap.HitObjects:
            if isinstance(hit_object, IHasPath):
                count_slider += 1
            elif isinstance(hit_object, IHasDuration):
                count_spinner += 1
            else:
                count_normal += 1

        object_count = count_normal + count_slider + count_spinner

        drain_length = 0

        if beatmap.HitObjects:
            break_length = sum(
                int(round(b.EndTime)) - int(round(b.StartTime))
                for b in beatmap.Breaks
            )
            # osu! divides two whole numbers here, truncating towards zero.
            drain_length = int(
                (
                    int(round(beatmap.HitObjects[-1].StartTime))
                    - int(round(beatmap.HitObjects[0].StartTime))
                    - break_length
                )
                / 1000
            )

        self._score_multiplier = CalculateDifficultyPeppyStars(
            beatmap.Difficulty, object_count, drain_length
        )

        attributes = LegacyScoreAttributes()

        for hit_object in playable_beatmap.HitObjects:
            self._simulate_hit(hit_object, attributes)

        attributes.BonusScoreRatio = (
            0.0
            if self._legacy_bonus_score == 0
            else self._standardised_bonus_score / self._legacy_bonus_score
        )
        attributes.BonusScore = self._legacy_bonus_score
        attributes.MaxCombo = self._combo

        return attributes

    def _simulate_hit(self, hit_object: HitObject, attributes: LegacyScoreAttributes) -> None:
        """Add what one object is worth to the running score.

        Args:
            hit_object: The object being caught.
            attributes: The score being built up.
        """
        increase_combo = True
        add_score_combo_multiplier = False

        is_bonus = False
        bonus_result = HitResult.None_

        score_increase = 0

        if isinstance(hit_object, (JuiceStream, BananaShower)):
            for nested in hit_object.NestedHitObjects:
                self._simulate_hit(nested, attributes)
            return

        if isinstance(hit_object, TinyDroplet):
            score_increase = 10
            increase_combo = False
        elif isinstance(hit_object, Droplet):
            score_increase = 100
        elif isinstance(hit_object, Fruit):
            score_increase = 300
            add_score_combo_multiplier = True
            increase_combo = True
        elif isinstance(hit_object, Banana):
            score_increase = 1100
            increase_combo = False
            is_bonus = True
            bonus_result = HitResult.LargeBonus

        if add_score_combo_multiplier:
            # osu!stable divided two whole numbers here, losing the remainder.
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
        score_v2 = any(m for m in mods if isinstance(m, ModScoreV2))
        multiplier = 1.0

        for mod in mods:
            if isinstance(mod, (CatchModHardRock, CatchModFlashlight)):
                multiplier *= 1.12

            elif isinstance(mod, (CatchModDoubleTime, CatchModNightcore)):
                multiplier *= 1.06

            elif isinstance(mod, (CatchModHalfTime, CatchModDaycore)):
                multiplier *= 0.3

            elif isinstance(mod, CatchModNoFail):
                multiplier *= 1.0 if score_v2 else 0.5

            elif isinstance(mod, CatchModHidden):
                multiplier *= 1.0 if score_v2 else 1.06

            elif isinstance(mod, CatchModEasy):
                multiplier *= 0.5

            elif isinstance(mod, CatchModRelax):
                return 0.0

        return multiplier
