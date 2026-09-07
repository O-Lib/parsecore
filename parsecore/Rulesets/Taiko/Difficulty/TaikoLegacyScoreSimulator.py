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
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Rulesets.Scoring.Legacy.ILegacyScoreSimulator import (
    ILegacyScoreSimulator,
)
from parsecore.Rulesets.Scoring.Legacy.LegacyScoreAttributes import (
    LegacyScoreAttributes,
)
from parsecore.Rulesets.Taiko.Objects.DrumRoll import DrumRoll
from parsecore.Rulesets.Taiko.Objects.DrumRollTick import DrumRollTick
from parsecore.Rulesets.Taiko.Objects.Hit import Hit
from parsecore.Rulesets.Taiko.Objects.StrongNestedHitObject import (
    StrongNestedHitObject,
)
from parsecore.Rulesets.Taiko.Objects.Swell import Swell
from parsecore.Rulesets.Taiko.Objects.SwellTick import SwellTick
from parsecore.Rulesets.Taiko.Objects.TaikoStrongableHitObject import (
    TaikoStrongableHitObject,
)
from parsecore.Rulesets.Taiko.Scoring.TaikoScoreProcessor import (
    GetBaseScoreForResult,
)
from parsecore.Utils.Vector2 import f32

# What osu!stable scored a taiko beatmap's circle size as, whatever the file
# said. See osu-stable's HitObjectManagerTaiko.
TAIKO_CIRCLE_SIZE = 2

# The slowest a swell can be turned and still be completed. This depends on the
# overall difficulty in the game; the easiest case is taken, because the point
# is the most rotations a swell could possibly demand.
MINIMUM_ROTATIONS_PER_SECOND = 7.5

# What kiai multiplies a note by.
KIAI_MULTIPLIER = 1.2

# What the mods multiply an osu!stable score by, and what they multiply it by
# once the second scoring version is in play.
MOD_MULTIPLIERS = {
    "NF": (0.5, 1.0),
    "EZ": (0.5, 0.5),
    "HT": (0.3, 0.3),
    "DC": (0.3, 0.3),
    "HD": (1.06, 1.06),
    "HR": (1.06, 1.06),
    "DT": (1.12, 1.12),
    "NC": (1.12, 1.12),
    "FL": (1.12, 1.12),
}

# Mods osu!stable refused to score at all.
UNSCORED_MODS = ("RX",)


class TaikoLegacyScoreSimulator(ILegacyScoreSimulator):
    """Simulates a perfect taiko play under osu!stable's first scoring system."""

    def __init__(self) -> None:
        """Create the simulator."""
        self._legacy_bonus_score = 0
        self._standardised_bonus_score = 0
        self._combo = 0
        self._difficulty_peppy_stars = 0
        self._playable_beatmap = None

    def Simulate(self, beatmap, playable_beatmap) -> LegacyScoreAttributes:
        """Return the highest osu!stable score a beatmap allows.

        Args:
            beatmap: The beatmap as it was decoded.
            playable_beatmap: The same beatmap as taiko plays it.
        """
        self._playable_beatmap = playable_beatmap

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

        # osu!stable ignored the beatmap's own circle size for taiko.
        altered_difficulty = beatmap.Difficulty.Clone()
        altered_difficulty.CircleSize = TAIKO_CIRCLE_SIZE

        self._difficulty_peppy_stars = CalculateDifficultyPeppyStars(
            altered_difficulty, object_count, drain_length
        )

        attributes = LegacyScoreAttributes()

        objects = playable_beatmap.HitObjects
        for i, hit_object in enumerate(objects):
            self._simulate_hit(
                hit_object,
                objects[i + 1] if i < len(objects) - 1 else None,
                attributes,
            )

        attributes.BonusScoreRatio = (
            0.0
            if self._legacy_bonus_score == 0
            else self._standardised_bonus_score / self._legacy_bonus_score
        )
        attributes.BonusScore = self._legacy_bonus_score
        attributes.MaxCombo = self._combo

        return attributes

    def _simulate_hit(
        self, hit_object, next_hit_object, attributes: LegacyScoreAttributes
    ) -> None:
        """Add what one object is worth to the running score.

        Args:
            hit_object: The object being hit.
            next_hit_object: The object after it, if there is one.
            attributes: The score being built up.
        """
        increase_combo = True
        add_score_combo_multiplier = False

        is_bonus = False
        bonus_result = HitResult.None_

        score_increase = 0

        if isinstance(hit_object, SwellTick):
            score_increase = 300
            increase_combo = False
            is_bonus = True
            bonus_result = HitResult.IgnoreHit
        elif isinstance(hit_object, DrumRollTick):
            score_increase = 300
            increase_combo = False
            is_bonus = True
            bonus_result = HitResult.SmallBonus
        elif isinstance(hit_object, Swell):
            # osu!lazer's swell shares almost nothing with osu!stable's, so the
            # ticks are worked out again from osu!stable's own rules.
            half_spins_required = int(
                hit_object.Duration / 1000 * MINIMUM_ROTATIONS_PER_SECOND
            )
            half_spins_required = int(max(1, f32(half_spins_required * f32(1.65))))

            # The rate this depends on varies with the mods; the case that
            # demands the most rotations is taken, so a converted score stays
            # beatable at the cost of being a little low.
            half_spins_required = max(1, int(f32(half_spins_required * f32(1.5))))

            for _ in range(half_spins_required + 1):
                self._simulate_hit(SwellTick(), None, attributes)

            score_increase = 300
            add_score_combo_multiplier = True
            increase_combo = False
            is_bonus = True
            bonus_result = HitResult.LargeBonus
        elif isinstance(hit_object, DrumRoll):
            self._simulate_drum_roll(hit_object, next_hit_object, attributes)
            return
        elif isinstance(hit_object, StrongNestedHitObject):
            # These never need handling on their own. All a strong hit does to
            # the score is double its parent, which the parent sees to itself;
            # walking into them here would also count them towards the combo.
            return
        elif isinstance(hit_object, Hit):
            score_increase = 300
            add_score_combo_multiplier = True

        if isinstance(hit_object, DrumRollTick):
            if self._playable_beatmap.ControlPointInfo.EffectPointAt(
                hit_object.Parent.StartTime
            ).KiaiMode:
                score_increase = int(f32(score_increase * f32(KIAI_MULTIPLIER)))

            if hit_object.IsStrong:
                score_increase += score_increase // 5

        # How much of the increase came from the combo multiplier.
        combo_score_increase = 0

        if add_score_combo_multiplier:
            old_score_increase = score_increase

            # Every division here is between whole numbers, and each one throws
            # its remainder away.
            score_increase += (
                score_increase
                // 35
                * 2
                * (self._difficulty_peppy_stars + 1)
                * (min(100, self._combo) // 10)
            )

            kiai_time = (
                hit_object.GetEndTime()
                if isinstance(hit_object, Swell)
                else hit_object.StartTime
            )
            if self._playable_beatmap.ControlPointInfo.EffectPointAt(
                kiai_time
            ).KiaiMode:
                score_increase = int(f32(score_increase * f32(KIAI_MULTIPLIER)))

            combo_score_increase = score_increase - old_score_increase

        if isinstance(hit_object, Swell) or (
            isinstance(hit_object, TaikoStrongableHitObject) and hit_object.IsStrong
        ):
            score_increase *= 2
            combo_score_increase *= 2

        score_increase -= combo_score_increase

        if add_score_combo_multiplier:
            attributes.ComboScore += combo_score_increase

        if is_bonus:
            self._legacy_bonus_score += score_increase
            self._standardised_bonus_score += GetBaseScoreForResult(bonus_result)
        else:
            attributes.AccuracyScore += score_increase

        if increase_combo:
            self._combo += 1

    def _simulate_drum_roll(
        self, drum_roll, next_hit_object, attributes: LegacyScoreAttributes
    ) -> None:
        """Add the ticks osu!stable would have placed along a drum roll.

        Args:
            drum_roll: The drum roll being hit.
            next_hit_object: The object after it, if there is one.
            attributes: The score being built up.
        """
        min_hit_delay = self._slider_taiko_min_hit_delay(drum_roll)

        # osu!stable let a drum roll be hit slightly past its end, but only
        # where the next object leaves room for it.
        if isinstance(next_hit_object, DrumRoll):
            next_start = next_hit_object.StartTime - self._slider_taiko_min_hit_delay(
                next_hit_object
            )
        elif next_hit_object is not None:
            next_start = next_hit_object.StartTime
        else:
            next_start = None

        endpoint_hittable = next_start is None or (
            next_start - (drum_roll.EndTime + int(min_hit_delay)) > int(min_hit_delay)
        )
        hittable_end_time = (
            drum_roll.EndTime + int(min_hit_delay)
            if endpoint_hittable
            else drum_roll.EndTime
        )

        time = drum_roll.StartTime
        while time < hittable_end_time:
            tick = DrumRollTick(drum_roll)
            tick.IsStrong = drum_roll.IsStrong
            self._simulate_hit(tick, None, attributes)
            time += min_hit_delay

    def _slider_taiko_min_hit_delay(self, drum_roll) -> float:
        """Return how far apart osu!stable placed a drum roll's ticks.

        Args:
            drum_roll: The drum roll to measure.
        """
        beat_length = self._playable_beatmap.ControlPointInfo.TimingPointAt(
            drum_roll.StartTime
        ).BeatLength

        if self._playable_beatmap.BeatmapInfo.BeatmapVersion >= 8:
            slider_tick_rate = self._playable_beatmap.Difficulty.SliderTickRate
            if slider_tick_rate in (3, 6, 1.5):
                max_rate = beat_length / 6
            else:
                max_rate = beat_length / 8
        else:
            max_rate = beat_length / 8

        while max_rate < 60:
            max_rate *= 2
        while max_rate > 120:
            max_rate /= 2

        return max_rate

    def GetLegacyScoreMultiplier(self, mods: list, difficulty=None) -> float:
        """Return what the mods multiply an osu!stable score by.

        Args:
            mods: The mods the score was set with.
            difficulty: Unused by taiko; mania reads it.
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
