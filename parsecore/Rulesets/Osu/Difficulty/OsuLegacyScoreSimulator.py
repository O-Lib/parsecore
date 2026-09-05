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

from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    CalculateDifficultyPeppyStars,
)
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
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

# What the mods multiply an osu!stable score by, and what they multiply it by
# once the second scoring version is in play.
MOD_MULTIPLIERS = {
    "NF": (0.5, 1.0),
    "EZ": (0.5, 0.5),
    "HT": (0.3, 0.3),
    "DC": (0.3, 0.3),
    "HD": (1.06, 1.06),
    "HR": (1.06, 1.10),
    "DT": (1.12, 1.20),
    "NC": (1.12, 1.20),
    "FL": (1.12, 1.12),
    "SO": (0.9, 0.9),
}

# Mods osu!stable refused to score at all.
UNSCORED_MODS = ("RX", "AP")


class OsuLegacyScoreSimulator(ILegacyScoreSimulator):
    """Simulates a perfect osu! play under osu!stable's first scoring system."""

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
            playable_beatmap: The same beatmap as osu! plays it.
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

            for i in range(total_half_spins_possible + 1):
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

    def GetLegacyScoreMultiplier(self, mods: list, difficulty=None) -> float:
        """Return what the mods multiply an osu!stable score by.

        Args:
            mods: The mods the score was set with.
            difficulty: Unused by osu!; the other rulesets read it.
        """
        return GetLegacyScoreMultiplier(mods)


def GetLegacyScoreMultiplier(mods: list) -> float:
    """Return what the mods multiply an osu!stable score by.

    Args:
        mods: The mods the score was set with.
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
