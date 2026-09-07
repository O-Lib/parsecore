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

from parsecore.Rulesets.Difficulty.DifficultyCalculator import DifficultyCalculator
from parsecore.Rulesets.Mania.Difficulty.ManiaDifficultyAttributes import (
    ManiaDifficultyAttributes,
)
from parsecore.Rulesets.Mania.Difficulty.Preprocessing.ManiaDifficultyHitObject import (
    ManiaDifficultyHitObject,
)
from parsecore.Rulesets.Mania.Difficulty.Skills.Strain import Strain
from parsecore.Rulesets.Mania.MathUtils import LegacySortHelper
from parsecore.Rulesets.Mania.Objects.HoldNote import HoldNote

# The difficulty algorithm this matches, as osu! versions it.
VERSION = 20241007

DIFFICULTY_MULTIPLIER = 0.018


class ManiaDifficultyCalculator(DifficultyCalculator):
    """Calculates what a mania beatmap is worth."""

    Version = VERSION

    def CreateSkills(self, beatmap, mods: list, clock_rate: float) -> list:
        """Return the skills a mania beatmap is rated on.

        Args:
            beatmap: The beatmap being rated.
            mods: The mods the score was set with.
            clock_rate: The rate the beatmap is played at.
        """
        return [Strain(mods, beatmap.TotalColumns)]

    def CreateDifficultyHitObjects(self, beatmap, clock_rate: float) -> list:
        """Return one difficulty object per note, in the order osu! reads them.

        Notes are sorted by whole milliseconds, so the notes of a chord all
        compare equal and their order is whatever osu!'s own sort leaves --
        which is why that sort is reproduced rather than replaced.

        Args:
            beatmap: The beatmap being rated.
            clock_rate: The rate the beatmap is played at.
        """
        sorted_objects = list(beatmap.HitObjects)
        total_columns = beatmap.TotalColumns

        LegacySortHelper.Sort(
            sorted_objects,
            lambda a, b: int(round(a.StartTime)) - int(round(b.StartTime)),
        )

        objects: list = []
        per_column_objects: list[list] = [[] for _ in range(total_columns)]

        for i in range(1, len(sorted_objects)):
            current_object = ManiaDifficultyHitObject(
                sorted_objects[i],
                sorted_objects[i - 1],
                clock_rate,
                objects,
                per_column_objects,
                len(objects),
            )
            objects.append(current_object)
            per_column_objects[current_object.Column].append(current_object)

        return objects

    def CreateDifficultyAttributes(
        self, beatmap, mods: list, skills: list, clock_rate: float
    ):
        """Return what a mania beatmap is worth.

        Args:
            beatmap: The beatmap being rated.
            mods: The mods the score was set with.
            skills: The skills, already fed every note.
            clock_rate: The rate the beatmap is played at.
        """
        if not beatmap.HitObjects:
            return ManiaDifficultyAttributes(Mods=list(mods))

        strain = next(s for s in skills if isinstance(s, Strain))

        return ManiaDifficultyAttributes(
            Mods=list(mods),
            StarRating=strain.DifficultyValue() * DIFFICULTY_MULTIPLIER,
            MaxCombo=sum(_max_combo_for_object(h) for h in beatmap.HitObjects),
        )


def _max_combo_for_object(hit_object) -> int:
    """Return how much combo one object is worth.

    A hold is worth its head plus one for every tenth of a second it lasts,
    which is how osu! counts the ticks it would award.

    Args:
        hit_object: The object to count.
    """
    if isinstance(hit_object, HoldNote):
        return 1 + int((hit_object.EndTime - hit_object.StartTime) / 100)

    return 1
