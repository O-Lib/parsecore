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
from parsecore.Beatmaps.BeatmapConverter import BeatmapConverter
from parsecore.Beatmaps.BeatmapProcessor import BeatmapProcessor
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Difficulty.DifficultyAttributes import DifficultyAttributes
from parsecore.Rulesets.Difficulty.Preprocessing.DifficultyHitObject import (
    DifficultyHitObject,
)
from parsecore.Rulesets.Difficulty.Skills.Skill import Skill
from parsecore.Rulesets.Mods.Mod import Mod


class DifficultyCalculator:
    """Calculates how hard a beatmap is for one ruleset."""

    def __init__(self, beatmap: WorkingBeatmap) -> None:
        """Create a calculator for a beatmap.

        Args:
            beatmap: The beatmap to calculate difficulty for, as the ruleset plays it.
        """
        self.WorkingBeatmap = beatmap
        self.Beatmap: Beatmap = Beatmap()

        self.playable_mods: list[Mod] = []

    @property
    def converter_type(self) -> type[BeatmapConverter]:
        """Return the ruleset's specific BeatmapConverter class."""
        raise NotImplementedError

    @property
    def processor_type(self) -> type[BeatmapProcessor] | None:
        """Return the ruleset's specific BeatmapProcessor class."""
        raise NotImplementedError

    def CreateSkills(self, beatmap: Beatmap, mods: list[Mod]) -> list[Skill]:
        """Return the skills this ruleset measures.

        Args:
            beatmap: The beatmap being calculated.
            mods: The mods in effect.
        """
        raise NotImplementedError

    def CreateDifficultyHitObjects(self, beatmap: Beatmap, mods: list[Mod]) -> list[DifficultyHitObject]:
        """Return the objects the skills walk, in time order.

        Args:
            beatmap: The beatmap being calculated.
            mods: The mods to create difficulty objects.
        """
        raise NotImplementedError

    def CreateDifficultyAttributes(self, beatmap: Beatmap, mods: list[Mod], skills: list[Skill]) -> DifficultyAttributes:
        """Reduce the processed skills to this ruleset's attributes.

        Args:
            beatmap: The beatmap being calculated.
            mods: The mods in effect.
            skills: The skills, already fed every object.
        """
        raise NotImplementedError

    def Calculate(self, mods: list[Mod]) -> DifficultyAttributes:
        """Calculate the difficulty of the beatmap.

        Args:
            mods: The mods to calculate for.

        Returns:
            The ruleset's difficulty attributes.
        """
        mods = mods

        self._pre_process(mods)

        skills = self.CreateSkills(self.Beatmap, mods)

        if not self.Beatmap.HitObjects:
            return self.CreateDifficultyAttributes(self.Beatmap, self.playable_mods, skills)

        for hit_object in self._get_difficulty_objects():
            for skill in skills:
                skill.Process(hit_object)

        return self.CreateDifficultyAttributes(
            self.Beatmap, mods, skills
        )

    def _pre_process(self, mods: list[Mod]) -> None:
        """Pre-process mods and prepare the playable beatmap instance for difficulty calculation.

        Args:
            mods: The list of mods in effect.
        """
        self.playable_mods = [m.DeepClone() for m in mods]
        self.Beatmap = self.WorkingBeatmap.GetPlayableBeatmap(
            self.converter_type, self.processor_type, self.playable_mods
        )

    def _get_difficulty_objects(self) -> list[DifficultyHitObject]:
        """Create and return the list of difficulty hit objects ordered by start time.

        Returns:
            A list of difficulty hit objects sorted chronologically.
        """
        difficulty_objects = self.CreateDifficultyHitObjects(self.Beatmap, self.playable_mods)
        return sorted(difficulty_objects, key=lambda h: h.BaseObject.StartTime)
