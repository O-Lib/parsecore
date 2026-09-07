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

from parsecore.Rulesets.Mods.Mod import Mod
from parsecore.Rulesets.Mods.ModType import ModType

DIFFICULTY_RATIO = 0.5


class ModEasy(Mod):
    """Larger circles, more forgiving HP drain, less accuracy required."""

    Name = "Easy"
    Acronym = "EZ"
    Description = "Larger circles, more forgiving HP drain, less accuracy required."
    Type = ModType.DifficultyReduction
    ScoreMultiplier = 0.5
    Ranked = True
    IncompatibleMods = ("HR", "DA")

    def ApplyToDifficulty(self, difficulty) -> None:
        """Halve the settings every ruleset shares.

        The overall difficulty is left alone here; each ruleset halves it
        itself, because not all of them read it the same way.

        Args:
            difficulty: The difficulty to modify.
        """
        difficulty.CircleSize *= DIFFICULTY_RATIO
        difficulty.ApproachRate *= DIFFICULTY_RATIO
        difficulty.DrainRate *= DIFFICULTY_RATIO
