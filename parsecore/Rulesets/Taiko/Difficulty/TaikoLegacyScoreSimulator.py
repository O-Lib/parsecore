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
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Rulesets.Scoring.Legacy.ILegacyScoreSimulator import (
    ILegacyScoreSimulator,
)
from parsecore.Rulesets.Scoring.Legacy.LegacyScoreAttributes import (
    LegacyScoreAttributes,
)
from parsecore.Rulesets.Taiko.Mods.TaikoModDaycore import TaikoModDaycore
from parsecore.Rulesets.Taiko.Mods.TaikoModDoubleTime import TaikoModDoubleTime
from parsecore.Rulesets.Taiko.Mods.TaikoModEasy import TaikoModEasy
from parsecore.Rulesets.Taiko.Mods.TaikoModFlashlight import TaikoModFlashlight
from parsecore.Rulesets.Taiko.Mods.TaikoModHalfTime import TaikoModHalfTime
from parsecore.Rulesets.Taiko.Mods.TaikoModHardRock import TaikoModHardRock
from parsecore.Rulesets.Taiko.Mods.TaikoModHidden import TaikoModHidden
from parsecore.Rulesets.Taiko.Mods.TaikoModNightcore import TaikoModNightcore
from parsecore.Rulesets.Taiko.Mods.TaikoModNoFail import TaikoModNoFail
from parsecore.Rulesets.Taiko.Mods.TaikoModRelax import TaikoModRelax
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


class TaikoLegacyScoreSimulator(ILegacyScoreSimulator):
    """Simulates a perfect taiko play under osu!stable's first scoring system."""

    def __init__(self) -> None:
        """Create the simulator."""
        self._legacy_bonus_score = 0
        self._standardised_bonus_score = 0
        self._combo = 0
        self._difficulty_peppy_stars = 0
        self._playable_beatmap = None

    def Simulate(self, workingBeatmap: WorkingBeatmap, playable_beatmap: Beatmap) -> LegacyScoreAttributes:
        """Return the highest osu!stable score a beatmap allows.

        Args:
            workingBeatmap: The beatmap as it was decoded.
            playable_beatmap: The same beatmap as taiko plays it.
        """
        self._playable_beatmap = playable_beatmap
        beatmap = workingBeatmap.Beatmap

        count_normal = 0
        count_slider = 0
        count_spinner = 0

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
        self, hit_object: HitObject, next_hit_object: HitObject | None, attributes: LegacyScoreAttributes
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
            drum_roll = hit_object
            min_hit_delay = self._slider_taiko_min_hit_delay(drum_roll)

            if next_hit_object is not None:
                next_hittable_start_time = (
                        next_hit_object.StartTime - self._slider_taiko_min_hit_delay(next_hit_object)
                        if isinstance(next_hit_object, DrumRoll)
                        else next_hit_object.StartTime
                )

                endpoint_hittable = (
                        next_hittable_start_time is None
                        or next_hittable_start_time - (drum_roll.EndTime + int(min_hit_delay)) > int(min_hit_delay)
                )

                hittable_end_time = drum_roll.EndTime + int(min_hit_delay) if endpoint_hittable else drum_roll.EndTime

                while drum_roll.StartTime < hittable_end_time:
                    drum_roll_tick = DrumRollTick(drum_roll)
                    drum_roll_tick.IsStrong = drum_roll.IsStrong
                    self._simulate_hit(drum_roll_tick, None, attributes)

                    drum_roll.StartTime += min_hit_delay
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

    def _slider_taiko_min_hit_delay(self, drum_roll: DrumRoll) -> float:
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

    @staticmethod
    def GetLegacyScoreMultiplier(mods: list[Mod]) -> float:
        """Return what the mods multiply an osu!stable score by.

        Args:
            mods: The mods the score was set with.
        """
        score_v2 = any(m for m in mods if isinstance(m, ModScoreV2))

        multiplier = 1.0

        for mod in mods:
            if isinstance(mod, (TaikoModDoubleTime, TaikoModNightcore, TaikoModFlashlight)):
                multiplier *= 1.12

            elif isinstance(mod, (TaikoModHidden, TaikoModHardRock)):
                multiplier *= 1.06

            elif isinstance(mod, (TaikoModHalfTime, TaikoModDaycore)):
                multiplier *= 0.3

            elif isinstance(mod, TaikoModEasy):
                multiplier *= 0.5

            elif isinstance(mod, TaikoModNoFail):
                multiplier *= 1.0 if score_v2 else 0.5

            elif isinstance(mod, TaikoModRelax):
                return 0.0

        return multiplier
