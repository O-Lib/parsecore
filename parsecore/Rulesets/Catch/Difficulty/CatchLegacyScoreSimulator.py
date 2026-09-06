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

from parsecore.Rulesets.Catch.Objects.Banana import Banana, BananaShower
from parsecore.Rulesets.Catch.Objects.Droplet import Droplet, TinyDroplet
from parsecore.Rulesets.Catch.Objects.Fruit import Fruit
from parsecore.Rulesets.Catch.Objects.JuiceStream import JuiceStream
from parsecore.Rulesets.Catch.Scoring.CatchScoreProcessor import (
    GetBaseScoreForResult,
)
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    CalculateDifficultyPeppyStars,
)
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Rulesets.Scoring.Legacy.ILegacyScoreSimulator import (
    ILegacyScoreSimulator,
)
from parsecore.Rulesets.Scoring.Legacy.LegacyScoreAttributes import (
    LegacyScoreAttributes,
)

# What the mods multiply an osu!stable score by, and what they multiply it by
# once the second scoring version is in play.
MOD_MULTIPLIERS = {
    "NF": (0.5, 1.0),
    "EZ": (0.5, 0.5),
    "HT": (0.3, 0.3),
    "DC": (0.3, 0.3),
    "HD": (1.06, 1.0),
    "HR": (1.12, 1.12),
    "DT": (1.06, 1.06),
    "NC": (1.06, 1.06),
    "FL": (1.12, 1.12),
}

# Mods osu!stable refused to score at all.
UNSCORED_MODS = ("RX",)


class CatchLegacyScoreSimulator(ILegacyScoreSimulator):
    """Simulates a perfect catch play under osu!stable's first scoring system."""

    def __init__(self) -> None:
        """Create the simulator."""
        self._legacy_bonus_score = 0
        self._standardised_bonus_score = 0
        self._combo = 0
        self._score_multiplier = 0.0

    def Simulate(self, beatmap, playable_beatmap) -> LegacyScoreAttributes:
        """Return the highest osu!stable score a beatmap allows.

        Args:
            beatmap: The beatmap as it was decoded.
            playable_beatmap: The same beatmap as catch plays it.
        """
        count_normal = 0
        count_slider = 0
        count_spinner = 0

        for hit_object in beatmap.HitObjects:
            if hasattr(hit_object, "Path"):
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

    def _simulate_hit(self, hit_object, attributes: LegacyScoreAttributes) -> None:
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

    def GetLegacyScoreMultiplier(self, mods: list, difficulty=None) -> float:
        """Return what the mods multiply an osu!stable score by.

        Args:
            mods: The mods the score was set with.
            difficulty: Unused by catch; mania reads it.
        """
        acronyms = [getattr(mod, "Acronym", None) for mod in mods]
        score_v2 = "SV2" in acronyms

        multiplier = 1.0

        for acronym in acronyms:
            if acronym in UNSCORED_MODS:
                return 0.0

            pair = MOD_MULTIPLIERS.get(acronym)
            if pair is not None:
                multiplier *= pair[1] if score_v2 else pair[0]

        return multiplier
