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

from parsecore.Rulesets.Difficulty.DifficultyAttributes import DifficultyAttributes
from parsecore.Rulesets.Difficulty.Preprocessing.DifficultyHitObject import (
    DifficultyHitObject,
)
from parsecore.Rulesets.Difficulty.Skills.Skill import Skill
from parsecore.Rulesets.Difficulty.TimedDifficultyAttributes import (
    TimedDifficultyAttributes,
)


class DifficultyCalculator:
    """Calculates how hard a beatmap is for one ruleset."""

    def __init__(self, beatmap, original_beatmap=None) -> None:
        """Create a calculator for a beatmap.

        Args:
            beatmap: The beatmap to calculate difficulty for, as the ruleset
                plays it.
            original_beatmap: The same beatmap as it was decoded, before it was
                converted and before any mod touched its settings. Only osu!
                reads it, and only to work out what osu!stable would have
                scored the beatmap at. Defaults to the playable beatmap, which
                is right whenever no mod changes the difficulty settings.
        """
        self.Beatmap = beatmap
        self.OriginalBeatmap = beatmap if original_beatmap is None else original_beatmap

    def CreateSkills(self, beatmap, mods: list, clock_rate: float) -> list[Skill]:
        """Return the skills this ruleset measures.

        Args:
            beatmap: The beatmap being calculated.
            mods: The mods in effect.
            clock_rate: The rate the beatmap is played at.
        """
        raise NotImplementedError

    def CreateDifficultyHitObjects(
        self, beatmap, clock_rate: float
    ) -> list[DifficultyHitObject]:
        """Return the objects the skills walk, in time order.

        Args:
            beatmap: The beatmap being calculated.
            clock_rate: The rate the beatmap is played at.
        """
        raise NotImplementedError

    def CreateDifficultyAttributes(
        self, beatmap, mods: list, skills: list[Skill], clock_rate: float
    ) -> DifficultyAttributes:
        """Reduce the processed skills to this ruleset's attributes.

        Args:
            beatmap: The beatmap being calculated.
            mods: The mods in effect.
            skills: The skills, already fed every object.
            clock_rate: The rate the beatmap is played at.
        """
        raise NotImplementedError

    def Calculate(self, mods: list | None = None) -> DifficultyAttributes:
        """Calculate the difficulty of the beatmap.

        Args:
            mods: The mods to calculate for.

        Returns:
            The ruleset's difficulty attributes.
        """
        mods = list(mods or [])
        clock_rate = self.GetClockRate(mods)

        skills = self.CreateSkills(self.Beatmap, mods, clock_rate)
        objects = self.CreateDifficultyHitObjects(self.Beatmap, clock_rate)

        for hit_object in objects:
            for skill in skills:
                skill.Process(hit_object)

        return self.CreateDifficultyAttributes(
            self.Beatmap, mods, skills, clock_rate
        )

    def CalculateTimed(self, mods: list | None = None) -> list[TimedDifficultyAttributes]:
        """Calculate difficulty after each object, for a live graph.

        Args:
            mods: The mods to calculate for.

        Returns:
            The attributes measured after every object, in time order.
        """
        mods = list(mods or [])
        clock_rate = self.GetClockRate(mods)

        skills = self.CreateSkills(self.Beatmap, mods, clock_rate)
        objects = self.CreateDifficultyHitObjects(self.Beatmap, clock_rate)

        results: list[TimedDifficultyAttributes] = []
        for hit_object in objects:
            for skill in skills:
                skill.Process(hit_object)
            results.append(
                TimedDifficultyAttributes(
                    hit_object.EndTime * clock_rate,
                    self.CreateDifficultyAttributes(
                        self.Beatmap, mods, skills, clock_rate
                    ),
                )
            )
        return results

    @staticmethod
    def GetClockRate(mods: list) -> float:
        """Return the rate the beatmap is played at under a set of mods.

        Args:
            mods: The mods in effect.
        """
        rate = 1.0
        for mod in mods:
            apply = getattr(mod, "ApplyToRate", None)
            if callable(apply):
                rate = apply(0.0, rate)
        return rate
