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
from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmap import GetPalpableObjects
from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmapConverter import (
    CatchBeatmapConverter,
)
from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmapProcessor import (
    CatchBeatmapProcessor,
)
from parsecore.Rulesets.Catch.Difficulty.CatchDifficultyAttributes import (
    CatchDifficultyAttributes,
)
from parsecore.Rulesets.Catch.Difficulty.Preprocessing.CatchDifficultyHitObject import (
    CatchDifficultyHitObject,
)
from parsecore.Rulesets.Catch.Difficulty.Skills.Movement import Movement
from parsecore.Rulesets.Catch.Objects.Banana import Banana
from parsecore.Rulesets.Catch.Objects.CatchHitObject import CatchHitObject
from parsecore.Rulesets.Catch.Objects.Droplet import TinyDroplet
from parsecore.Rulesets.Catch.UI.Catcher import CalculateCatchWidth
from parsecore.Rulesets.Difficulty.DifficultyAttributes import DifficultyAttributes
from parsecore.Rulesets.Difficulty.DifficultyCalculator import DifficultyCalculator
from parsecore.Rulesets.Difficulty.Preprocessing.DifficultyHitObject import (
    DifficultyHitObject,
)
from parsecore.Rulesets.Difficulty.Skills.Skill import Skill
from parsecore.Rulesets.Mods.Mod import Mod
from parsecore.Utils import ModUtils
from parsecore.Utils.Vector2 import f32

DIFFICULTY_MULTIPLIER = 4.59

# Above this circle size the plate shrinks faster than its width suggests.
NARROW_CATCHER_CIRCLE_SIZE = f32(5.5)
NARROW_CATCHER_RATE = f32(0.0625)


class CatchDifficultyCalculator(DifficultyCalculator):
    """Calculates what a catch beatmap is worth."""
    
    def __init__(self, beatmap: WorkingBeatmap) -> None:
        """Creates a new catch difficulty calculator.

        Args:
            beatmap: The working beatmap to calculate difficulty for.
        """
        super().__init__(beatmap)

    @property
    def converter_type(self) -> type[BeatmapConverter]:
        """The type of beatmap converter used for catch beatmaps."""
        return CatchBeatmapConverter

    @property
    def processor_type(self) -> type[BeatmapProcessor] | None:
        """The type of beatmap processor used for catch beatmaps."""
        return CatchBeatmapProcessor

    def CreateSkills(self, beatmap: Beatmap, mods: list[Mod]) -> list[Skill]:
        """Return the skills a catch beatmap is rated on.

        Args:
            beatmap: The beatmap being rated.
            mods: The mods the score was set with.
        """
        return [Movement(mods)]

    def CreateDifficultyHitObjects(self, beatmap: Beatmap, mods: list[Mod]) -> list[DifficultyHitObject]:
        """Return one difficulty object per fruit or droplet worth catching.

        Args:
            beatmap: The beatmap being rated.
            mods: The mods to create difficulty objects.
        """
        half_catcher_width = f32(CalculateCatchWidth(beatmap.Difficulty) * 0.5)
        half_catcher_width = f32(
            half_catcher_width
            * f32(
                1
                - f32(
                    max(0.0, beatmap.Difficulty.CircleSize - NARROW_CATCHER_CIRCLE_SIZE)
                    * NARROW_CATCHER_RATE
                )
            )
        )

        objects: list[DifficultyHitObject] = []
        last_object: CatchHitObject | None = None
        clock_rate = ModUtils.CalculateRateWithMods(mods)

        for hit_object in GetPalpableObjects(beatmap.HitObjects):
            # The plate passes through these on its way elsewhere.
            if isinstance(hit_object, (Banana, TinyDroplet)):
                continue

            if last_object is not None:
                objects.append(
                    CatchDifficultyHitObject(
                        hit_object,
                        last_object,
                        clock_rate,
                        half_catcher_width,
                        objects,
                        len(objects),
                    )
                )

            last_object = hit_object

        return objects

    def CreateDifficultyAttributes(
            self, beatmap: Beatmap, mods: list[Mod], skills: list[Skill]
    ) -> DifficultyAttributes:
        """Return what the beatmap is worth once the skill has run.

        Args:
            beatmap: The beatmap being rated.
            mods: The mods the score was set with.
            skills: The skills, already fed every object.
        """
        if not beatmap.HitObjects:
            return CatchDifficultyAttributes(Mods=mods)
        
        star_rating = math.sqrt(
            next(s for s in skills if isinstance(s, Movement)).DifficultyValue()
        )

        return CatchDifficultyAttributes(
            Mods=mods,
            StarRating=star_rating * DIFFICULTY_MULTIPLIER,
            MaxCombo=beatmap.GetMaxCombo(),
        )
