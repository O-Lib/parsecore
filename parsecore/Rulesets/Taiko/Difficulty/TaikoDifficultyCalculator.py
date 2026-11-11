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

from parsecore.Beatmaps.Beatmap import Beatmap
from parsecore.Beatmaps.BeatmapConverter import BeatmapConverter
from parsecore.Beatmaps.BeatmapProcessor import BeatmapProcessor
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Difficulty.DifficultyAttributes import DifficultyAttributes
from parsecore.Rulesets.Difficulty.DifficultyCalculator import DifficultyCalculator
from parsecore.Rulesets.Difficulty.Preprocessing.DifficultyHitObject import (
    DifficultyHitObject,
)
from parsecore.Rulesets.Difficulty.Skills.Skill import Skill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Mods.Mod import Mod
from parsecore.Rulesets.Taiko.Beatmaps.TaikoBeatmapConverter import (
    TaikoBeatmapConverter,
)
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Colour import (
    TaikoColourDifficultyPreprocessor,
)
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Rhythm import (
    TaikoRhythmDifficultyPreprocessor,
)
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.TaikoDifficultyHitObject import (
    TaikoDifficultyHitObject,
)
from parsecore.Rulesets.Taiko.Difficulty.Skills.Colour import Colour
from parsecore.Rulesets.Taiko.Difficulty.Skills.Reading import Reading
from parsecore.Rulesets.Taiko.Difficulty.Skills.Rhythm import Rhythm
from parsecore.Rulesets.Taiko.Difficulty.Skills.Stamina import Stamina
from parsecore.Rulesets.Taiko.Difficulty.TaikoDifficultyAttributes import (
    TaikoDifficultyAttributes,
)
from parsecore.Rulesets.Taiko.Mods.TaikoModRelax import TaikoModRelax
from parsecore.Utils import ModUtils

# The difficulty algorithm this matches, as osu! versions it.
VERSION = 20260706

DIFFICULTY_MULTIPLIER = 0.084375
RHYTHM_SKILL_MULTIPLIER = 0.770 * DIFFICULTY_MULTIPLIER
READING_SKILL_MULTIPLIER = 0.100 * DIFFICULTY_MULTIPLIER
COLOUR_SKILL_MULTIPLIER = 0.375 * DIFFICULTY_MULTIPLIER
STAMINA_SKILL_MULTIPLIER = 0.445 * DIFFICULTY_MULTIPLIER

# Playing with more fingers than taiko intends makes stamina cheaper.
EXTRA_FINGER_DIVISOR = 1.5

OSU_RULESET_ID = 0


class TaikoDifficultyCalculator(DifficultyCalculator):
    """Calculates what a taiko beatmap is worth."""

    Version = VERSION

    def __init__(self, beatmap: WorkingBeatmap) -> None:
        """Create a calculator for a beatmap.

        Args:
            beatmap: The converted taiko beatmap.
        """
        super().__init__(beatmap)
        self._strain_length_bonus = 1.0
        self._pattern_multiplier = 1.0
        self._is_relax = False
        self._is_convert = False

    @property
    def converter_type(self) -> type[BeatmapConverter]:
        """Return the converter type used to convert beatmaps for taiko."""
        return TaikoBeatmapConverter

    @property
    def processor_type(self) -> type[BeatmapProcessor] | None:
        """Return the beatmap processor type for taiko, if any."""
        return None

    def CreateSkills(self, beatmap: Beatmap, mods: list[Mod]) -> list[Skill]:
        """Return the skills a taiko beatmap is rated on.

        Args:
            beatmap: The beatmap being rated.
            mods: The mods the score was set with.
        """
        self._is_convert = beatmap.BeatmapInfo.RulesetID == OSU_RULESET_ID
        self._is_relax = any(m for m in mods if isinstance(m, TaikoModRelax))

        return [
            Rhythm(mods),
            Reading(mods),
            Colour(mods),
            Stamina(mods, False, self._is_convert),
            Stamina(mods, True, self._is_convert),
        ]

    def CreateDifficultyHitObjects(self, beatmap: Beatmap, mods: list[Mod]) -> list[DifficultyHitObject]:
        """Return one difficulty object per note, with its groupings assigned.

        The first two objects only provide timing, so the run starts at the
        third.

        Args:
            beatmap: The beatmap being rated.
            mods: The mods to create difficulty objects.
        """
        difficulty_hit_objects: list = []
        centre_objects: list = []
        rim_objects: list = []
        note_objects: list = []

        clock_rate = ModUtils.CalculateRateWithMods(mods)

        for i in range(2, len(beatmap.HitObjects)):
            difficulty_hit_objects.append(
                TaikoDifficultyHitObject(
                    beatmap.HitObjects[i],
                    beatmap.HitObjects[i - 1],
                    clock_rate,
                    difficulty_hit_objects,
                    centre_objects,
                    rim_objects,
                    note_objects,
                    len(difficulty_hit_objects),
                    beatmap.ControlPointInfo,
                    beatmap.Difficulty.SliderMultiplier,
                )
            )

        TaikoColourDifficultyPreprocessor.ProcessAndAssign(difficulty_hit_objects)
        TaikoRhythmDifficultyPreprocessor.ProcessAndAssign(note_objects)

        return difficulty_hit_objects

    def CreateDifficultyAttributes(
            self, beatmap: Beatmap, mods: list[Mod], skills: list[Skill]
    ) -> DifficultyAttributes:
        """Return what the beatmap is worth once every skill has run.

        Args:
            beatmap: The beatmap being rated.
            mods: The mods the score was set with.
            skills: The skills, already fed every object.
        """
        if not beatmap.HitObjects:
            return TaikoDifficultyAttributes(Mods=mods)

        rhythm = next(s for s in skills if isinstance(s, Rhythm))
        reading = next(s for s in skills if isinstance(s, Reading))
        colour = next(s for s in skills if isinstance(s, Colour))
        stamina = next(s for s in skills if isinstance(s, Stamina) and not s.SingleColourStamina)
        single_colour_stamina = next(s for s in skills if isinstance(s, Stamina) and s.SingleColourStamina)

        stamina_difficulty_value = stamina.DifficultyValue()

        rhythm_skill = rhythm.DifficultyValue() * RHYTHM_SKILL_MULTIPLIER
        reading_skill = reading.DifficultyValue() * READING_SKILL_MULTIPLIER
        colour_skill = colour.DifficultyValue() * COLOUR_SKILL_MULTIPLIER
        stamina_skill = stamina_difficulty_value * STAMINA_SKILL_MULTIPLIER
        mono_stamina_skill = (
            single_colour_stamina.DifficultyValue() * STAMINA_SKILL_MULTIPLIER
        )

        mono_stamina_factor = (
            1.0
            if stamina_skill == 0
            else DiffUtils.Pow(mono_stamina_skill / stamina_skill, 5)
        )
        stamina_difficult_strains = stamina.CountTopWeightedStrains(
            stamina_difficulty_value
        )

        self._pattern_multiplier = DiffUtils.Pow(stamina_skill * colour_skill, 0.10)
        self._strain_length_bonus = 1 + 0.15 * DiffUtils.ReverseLerp(
            stamina_difficult_strains, 1000, 1555
        )

        combined_rating, consistency_factor = self._combined_difficulty_value(
            rhythm, reading, colour, stamina
        )
        star_rating = _rescale(combined_rating * 1.4)

        # Each skill is reported as its share of the finished star rating
        # rather than as its own raw value.
        total_skill = rhythm_skill + reading_skill + colour_skill + stamina_skill
        skill_rating = star_rating / total_skill

        colour_difficulty = colour_skill * skill_rating
        stamina_difficulty = stamina_skill * skill_rating

        return TaikoDifficultyAttributes(
            Mods=mods,
            StarRating=star_rating,
            MaxCombo=beatmap.GetMaxCombo(),
            MechanicalDifficulty=colour_difficulty + stamina_difficulty,
            RhythmDifficulty=rhythm_skill * skill_rating,
            ReadingDifficulty=reading_skill * skill_rating,
            ColourDifficulty=colour_difficulty,
            StaminaDifficulty=stamina_difficulty,
            MonoStaminaFactor=mono_stamina_factor,
            StaminaTopStrains=stamina_difficult_strains,
            ConsistencyFactor=consistency_factor,
        )

    def _combined_difficulty_value(
        self, rhythm: Rhythm, reading: Reading, colour: Colour, stamina: Stamina
    ) -> tuple[float, float]:
        """Return the beatmap's combined rating and how evenly it is spread.

        Args:
            rhythm: The rhythm skill.
            reading: The reading skill.
            colour: The colour skill.
            stamina: The stamina skill.

        Returns:
            The combined rating and the consistency factor.
        """
        peaks = self._combine_peaks(
            rhythm.GetCurrentStrainPeaks(),
            reading.GetCurrentStrainPeaks(),
            colour.GetCurrentStrainPeaks(),
            stamina.GetCurrentStrainPeaks(),
        )

        if not peaks:
            return 0.0, 0.0

        difficulty = 0.0
        weight = 1.0

        for strain in sorted(peaks, reverse=True):
            difficulty += strain * weight
            weight *= 0.9

        object_peaks = self._combine_peaks(
            rhythm.GetObjectDifficulties(),
            reading.GetObjectDifficulties(),
            colour.GetObjectDifficulties(),
            stamina.GetObjectDifficulties(),
        )

        if not object_peaks:
            return 0.0, 0.0

        # How the whole beatmap compares to its hardest twentieth: a map whose
        # difficulty sits in a few spikes scores far below one that sustains it.
        top_count = 1 + len(object_peaks) // 20
        top_objects = sorted(object_peaks, reverse=True)[:top_count]
        top_average = sum(top_objects) / len(top_objects)
        consistency_factor = sum(object_peaks) / (top_average * len(object_peaks))

        return difficulty, consistency_factor

    def _combine_peaks(
        self,
        rhythm_peaks: list[float],
        reading_peaks: list[float],
        colour_peaks: list[float],
        stamina_peaks: list[float],
    ) -> list[float]:
        """Fold the four skills' values together, one entry at a time.

        Colour and stamina are combined first, because both describe what the
        hands are doing; rhythm and reading are then folded in around that.

        Args:
            rhythm_peaks: The rhythm skill's values.
            reading_peaks: The reading skill's values.
            colour_peaks: The colour skill's values.
            stamina_peaks: The stamina skill's values.

        Returns:
            The combined values, with zeroes dropped.
        """
        combined: list[float] = []

        for i in range(len(colour_peaks)):
            rhythm_peak = (
                rhythm_peaks[i] * RHYTHM_SKILL_MULTIPLIER * self._pattern_multiplier
            )
            reading_peak = reading_peaks[i] * READING_SKILL_MULTIPLIER
            # Relax removes the need to hit the right side of the drum.
            colour_peak = (
                0.0 if self._is_relax else colour_peaks[i] * COLOUR_SKILL_MULTIPLIER
            )
            stamina_peak = (
                stamina_peaks[i] * STAMINA_SKILL_MULTIPLIER * self._strain_length_bonus
            )
            # A convert or a relax score is played with more fingers than taiko
            # expects, so the same speed costs less.
            if self._is_convert or self._is_relax:
                stamina_peak /= EXTRA_FINGER_DIVISOR

            peak = DiffUtils.Norm(
                2,
                DiffUtils.Norm(1.5, colour_peak, stamina_peak),
                rhythm_peak,
                reading_peak,
            )

            if peak > 0:
                combined.append(peak)

        return combined


def _rescale(star_rating: float) -> float:
    """Return a star rating pulled onto the scale players are used to.

    Args:
        star_rating: The raw combined rating.
    """
    if star_rating < 0:
        return star_rating

    return 10.43 * math.log(star_rating / 8 + 1)
