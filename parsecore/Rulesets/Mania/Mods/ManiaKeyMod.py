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

from typing import cast

from parsecore.Beatmaps.BeatmapConverter import BeatmapConverter
from parsecore.Rulesets.Mania.Beatmaps.ManiaBeatmapConverter import (
    ManiaBeatmapConverter,
)
from parsecore.Rulesets.Mods.IApplicableToBeatmapConverter import (
    IApplicableToBeatmapConverter,
)
from parsecore.Rulesets.Mods.Mod import Mod
from parsecore.Rulesets.Mods.ModType import ModType


class ManiaKeyMod(Mod, IApplicableToBeatmapConverter):
    """Converts a beatmap onto a fixed number of columns."""

    KeyCount = 0
    Type = ModType.Conversion
    Ranked = True

    @property
    def Acronym(self) -> str:
        """Return the acronym of the key mod."""
        return self.Name

    @property
    def IncompatibleMods(self) -> list[type]:
        """Return the mods this one cannot be played with."""
        return KEY_MODS

    def ApplyToBeatmapConverter(self, beatmap_converter: BeatmapConverter) -> None:
        """Tell the converter how many columns to aim for.

        Args:
            beatmap_converter: The converter about to run.
        """
        mania_beatmap = cast(ManiaBeatmapConverter, beatmap_converter)

        # A beatmap written for mania keeps the columns it was made with.
        if mania_beatmap.IsForCurrentRuleset:
            return

        mania_beatmap.TargetColumns = self.KeyCount


class ManiaModKey1(ManiaKeyMod):
    """Play with one key."""

    Name = "One Key"
    Acronym = "1K"
    Description = "Play with one key."
    KeyCount = 1


class ManiaModKey2(ManiaKeyMod):
    """Play with two keys."""

    Name = "Two Keys"
    Acronym = "2K"
    Description = "Play with two keys."
    KeyCount = 2


class ManiaModKey3(ManiaKeyMod):
    """Play with three keys."""

    Name = "Three Keys"
    Acronym = "3K"
    Description = "Play with three keys."
    KeyCount = 3


class ManiaModKey4(ManiaKeyMod):
    """Play with four keys."""

    Name = "Four Keys"
    Acronym = "4K"
    Description = "Play with four keys."
    KeyCount = 4


class ManiaModKey5(ManiaKeyMod):
    """Play with five keys."""

    Name = "Five Keys"
    Acronym = "5K"
    Description = "Play with five keys."
    KeyCount = 5


class ManiaModKey6(ManiaKeyMod):
    """Play with six keys."""

    Name = "Six Keys"
    Acronym = "6K"
    Description = "Play with six keys."
    KeyCount = 6


class ManiaModKey7(ManiaKeyMod):
    """Play with seven keys."""

    Name = "Seven Keys"
    Acronym = "7K"
    Description = "Play with seven keys."
    KeyCount = 7


class ManiaModKey8(ManiaKeyMod):
    """Play with eight keys."""

    Name = "Eight Keys"
    Acronym = "8K"
    Description = "Play with eight keys."
    KeyCount = 8


class ManiaModKey9(ManiaKeyMod):
    """Play with nine keys."""

    Name = "Nine Keys"
    Acronym = "9K"
    Description = "Play with nine keys."
    KeyCount = 9


class ManiaModKey10(ManiaKeyMod):
    """Play with ten keys."""

    Name = "Ten Keys"
    Acronym = "10K"
    Description = "Play with ten keys."
    KeyCount = 10


KEY_MODS = [
    ManiaModKey1,
    ManiaModKey2,
    ManiaModKey3,
    ManiaModKey4,
    ManiaModKey5,
    ManiaModKey6,
    ManiaModKey7,
    ManiaModKey8,
    ManiaModKey9,
    ManiaModKey10
]
