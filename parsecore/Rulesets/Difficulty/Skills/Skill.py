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

from parsecore.Rulesets.Difficulty.Preprocessing.DifficultyHitObject import (
    DifficultyHitObject,
)


class Skill:
    """Measures one aspect of how hard a beatmap is."""

    def __init__(self, mods: list | None = None) -> None:
        """Create a skill.

        Args:
            mods: The mods the score was set with.
        """
        self.Mods = list(mods or [])
        self.ObjectDifficulties: list[float] = []

    def Process(self, current: DifficultyHitObject) -> None:
        """Take the next object into account, recording its difficulty.

        Args:
            current: The object to process.
        """
        self.ObjectDifficulties.append(self.ProcessInternal(current))

    def ProcessInternal(self, current: DifficultyHitObject) -> float:
        """Return this object's contribution to the skill.

        Args:
            current: The object to process.
        """
        raise NotImplementedError

    def DifficultyValue(self) -> float:
        """Return the difficulty of everything processed so far."""
        raise NotImplementedError

    def GetObjectDifficulties(self) -> list[float]:
        """Return what each processed object contributed."""
        return self.ObjectDifficulties
