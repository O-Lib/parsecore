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

from parsecore.Rulesets.Difficulty.DifficultyCalculator import DifficultyCalculator
from parsecore.Rulesets.Difficulty.Skills.HarmonicSkill import HarmonicSkill
from parsecore.Rulesets.Difficulty.Skills.Skill import Skill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Osu.Difficulty.OsuDifficultyAttributes import (
    OsuDifficultyAttributes,
)
from parsecore.Rulesets.Osu.Difficulty.OsuLegacyScoreSimulator import (
    OsuLegacyScoreSimulator,
)
from parsecore.Rulesets.Osu.Difficulty.Preprocessing.OsuDifficultyHitObject import (
    OsuDifficultyHitObject,
)
from parsecore.Rulesets.Osu.Difficulty.Skills.Aim import Aim
from parsecore.Rulesets.Osu.Difficulty.Skills.Flashlight import Flashlight
from parsecore.Rulesets.Osu.Difficulty.Skills.Reading import Reading
from parsecore.Rulesets.Osu.Difficulty.Skills.Speed import Speed
from parsecore.Rulesets.Osu.Difficulty.Utils import LegacyScoreUtils
from parsecore.Rulesets.Osu.Mods.OsuModFlashlight import OsuModFlashlight
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner

# The difficulty algorithm this port follows, as osu! versions it.
VERSION = 20260706

# Keeps the final pp value scaled around what it used to be.
PERFORMANCE_BASE_MULTIPLIER = 1.12
PERFORMANCE_NORM_EXPONENT = 1.1


def DifficultyToPerformance(difficulty: float) -> float:
    """Return the performance an aim difficulty value is worth.

    Args:
        difficulty: The aim difficulty value.
    """
    return 4.0 * DiffUtils.Pow(difficulty, 3)


def SumCognitionDifficulty(reading: float, flashlight: float) -> float:
    """Combine reading and flashlight into one cognition difficulty.

    Flashlight is scaled down where it far exceeds reading, because the two
    overlap: much of what flashlight measures is reading the player already did.

    Args:
        reading: The reading difficulty.
        flashlight: The flashlight difficulty.
    """
    if reading <= 0:
        return flashlight
    if flashlight <= 0:
        return reading

    return DiffUtils.Norm(
        PERFORMANCE_NORM_EXPONENT,
        reading,
        flashlight * min(max(flashlight / reading, 0.25), 1.0),
    )


def _calculate_aim_difficulty_rating(difficulty_value: float) -> float:
    """Return the aim rating a raw aim difficulty corresponds to.

    Args:
        difficulty_value: The aim skill's difficulty value.
    """
    return DiffUtils.Pow(difficulty_value, 0.63) * 0.02275


def _calculate_difficulty_rating(difficulty_value: float) -> float:
    """Return the rating a raw skill difficulty corresponds to.

    Args:
        difficulty_value: The skill's difficulty value.
    """
    return math.sqrt(difficulty_value) * 0.0675


def _calculate_star_rating(base_performance: float) -> float:
    """Return the star rating a base performance value corresponds to.

    Args:
        base_performance: The combined performance of every skill.
    """
    return _cbrt(base_performance * PERFORMANCE_BASE_MULTIPLIER)


def _cbrt(value: float) -> float:
    """Return the cube root of a value, keeping the sign.

    osu! calls ``Math.Cbrt``, a dedicated cube root that is correct to the last
    bit where ``pow(x, 1/3)`` is not. That last bit reaches the star rating,
    which is why this package requires Python 3.11 for ``math.cbrt``.

    Args:
        value: The value to take the cube root of.
    """
    return math.cbrt(value)


class OsuDifficultyCalculator(DifficultyCalculator):
    """Calculates how hard an osu! beatmap is."""

    Version = VERSION

    def CreateDifficultyHitObjects(
        self, beatmap, clock_rate: float
    ) -> list[OsuDifficultyHitObject]:
        """Return the objects the skills walk, in time order.

        Args:
            beatmap: The beatmap being calculated.
            clock_rate: The rate the beatmap is played at.
        """
        objects: list[OsuDifficultyHitObject] = []

        # The first jump is formed by the first two objects of the map.
        for i in range(1, len(beatmap.HitObjects)):
            objects.append(
                OsuDifficultyHitObject(
                    beatmap.HitObjects[i],
                    beatmap.HitObjects[i - 1],
                    clock_rate,
                    objects,
                    len(objects),
                )
            )

        return objects

    def CreateSkills(self, beatmap, mods: list, clock_rate: float) -> list[Skill]:
        """Return the skills osu! measures.

        Args:
            beatmap: The beatmap being calculated.
            mods: The mods in effect.
            clock_rate: The rate the beatmap is played at.
        """
        skills: list[Skill] = [
            Aim(mods, True),
            Aim(mods, False),
            Speed(mods),
            Reading(mods),
        ]

        if any(isinstance(m, OsuModFlashlight) for m in mods):
            skills.append(Flashlight(mods, len(beatmap.HitObjects)))

        return skills

    def CreateDifficultyAttributes(
        self, beatmap, mods: list, skills: list[Skill], clock_rate: float
    ) -> OsuDifficultyAttributes:
        """Reduce the processed skills to osu!'s difficulty attributes.

        Args:
            beatmap: The beatmap being calculated.
            mods: The mods in effect.
            skills: The skills, already fed every object.
            clock_rate: The rate the beatmap is played at.

        Returns:
            The beatmap's difficulty attributes, including its star rating.
        """
        if not beatmap.HitObjects:
            return OsuDifficultyAttributes(Mods=list(mods))

        aim = next(s for s in skills if isinstance(s, Aim) and s.IncludeSliders)
        aim_without_sliders = next(
            s for s in skills if isinstance(s, Aim) and not s.IncludeSliders
        )
        speed = next(s for s in skills if isinstance(s, Speed))
        reading = next(s for s in skills if isinstance(s, Reading))
        flashlight = next((s for s in skills if isinstance(s, Flashlight)), None)

        aim_difficulty_value = aim.DifficultyValue()
        aim_no_sliders_difficulty_value = aim_without_sliders.DifficultyValue()
        speed_difficulty_value = speed.DifficultyValue()
        reading_difficulty_value = reading.DifficultyValue()

        aim_difficult_strain_count = aim.CountTopWeightedStrains(aim_difficulty_value)
        speed_difficult_strain_count = speed.CountTopWeightedObjectDifficulties(
            speed_difficulty_value
        )
        reading_difficult_note_count = reading.CountTopWeightedObjectDifficulties(
            reading_difficulty_value
        )
        speed_notes = speed.RelevantObjectCount()

        aim_no_sliders_top_weighted_slider_count = (
            aim_without_sliders.CountTopWeightedSliders(
                aim_no_sliders_difficulty_value
            )
        )
        aim_no_sliders_difficult_strain_count = (
            aim_without_sliders.CountTopWeightedStrains(
                aim_no_sliders_difficulty_value
            )
        )
        aim_top_weighted_slider_factor = aim_no_sliders_top_weighted_slider_count / max(
            1.0,
            aim_no_sliders_difficult_strain_count
            - aim_no_sliders_top_weighted_slider_count,
        )

        speed_top_weighted_slider_count = speed.CountTopWeightedSliders(
            speed_difficulty_value
        )
        speed_top_weighted_slider_factor = speed_top_weighted_slider_count / max(
            1.0, speed_difficult_strain_count - speed_top_weighted_slider_count
        )

        difficult_sliders = aim.GetDifficultSliders()

        hit_circle_count = sum(
            1 for h in beatmap.HitObjects if isinstance(h, HitCircle)
        )
        slider_count = sum(1 for h in beatmap.HitObjects if isinstance(h, Slider))
        spinner_count = sum(1 for h in beatmap.HitObjects if isinstance(h, Spinner))

        aim_rating = _calculate_aim_difficulty_rating(aim_difficulty_value)
        aim_no_sliders_rating = _calculate_aim_difficulty_rating(
            aim_no_sliders_difficulty_value
        )
        slider_factor = (
            aim_no_sliders_rating / aim_rating if aim_difficulty_value > 0 else 1.0
        )

        speed_rating = _calculate_difficulty_rating(speed_difficulty_value)
        reading_rating = _calculate_difficulty_rating(reading_difficulty_value)

        flashlight_rating = 0.0
        if flashlight is not None:
            flashlight_rating = _calculate_difficulty_rating(
                flashlight.DifficultyValue()
            )

        base_aim_performance = DifficultyToPerformance(aim_rating)
        base_speed_performance = HarmonicSkill.DifficultyToPerformance(speed_rating)
        base_reading_performance = HarmonicSkill.DifficultyToPerformance(reading_rating)
        base_flashlight_performance = Flashlight.DifficultyToPerformance(
            flashlight_rating
        )

        base_cognition_performance = SumCognitionDifficulty(
            base_reading_performance, base_flashlight_performance
        )

        base_performance = DiffUtils.Norm(
            PERFORMANCE_NORM_EXPONENT,
            base_aim_performance,
            base_speed_performance,
            base_cognition_performance,
        )

        # What osu!stable would have scored this beatmap at. None of this feeds
        # the star rating; it lets a score from that era be read for the combo
        # breaks it does not record.
        nested_score_per_object = LegacyScoreUtils.CalculateNestedScorePerObject(
            beatmap, len(beatmap.HitObjects)
        )
        legacy_score_base_multiplier = (
            LegacyScoreUtils.CalculateDifficultyPeppyStarsFor(self.OriginalBeatmap)
        )
        score_attributes = OsuLegacyScoreSimulator().Simulate(
            self.OriginalBeatmap, beatmap
        )

        return OsuDifficultyAttributes(
            Mods=list(mods),
            StarRating=_calculate_star_rating(base_performance),
            MaxCombo=beatmap.GetMaxCombo(),
            AimDifficulty=aim_rating,
            AimDifficultSliderCount=difficult_sliders,
            SpeedDifficulty=speed_rating,
            SpeedNoteCount=speed_notes,
            FlashlightDifficulty=flashlight_rating,
            ReadingDifficulty=reading_rating,
            SliderFactor=slider_factor,
            AimDifficultStrainCount=aim_difficult_strain_count,
            SpeedDifficultStrainCount=speed_difficult_strain_count,
            ReadingDifficultNoteCount=reading_difficult_note_count,
            AimTopWeightedSliderFactor=aim_top_weighted_slider_factor,
            SpeedTopWeightedSliderFactor=speed_top_weighted_slider_factor,
            HitCircleCount=hit_circle_count,
            SliderCount=slider_count,
            SpinnerCount=spinner_count,
            NestedScorePerObject=nested_score_per_object,
            LegacyScoreBaseMultiplier=legacy_score_base_multiplier,
            MaximumLegacyComboScore=score_attributes.ComboScore,
        )
