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


class ManiaModDualStages(Mod, IApplicableToBeatmapConverter):
    """Double the stages, double the fun."""

    Name = "Dual Stages"
    Acronym = "DS"
    Description = "Double the stages, double the fun!"
    Type = ModType.Conversion

    def ApplyToBeatmapConverter(self, beatmap_converter: BeatmapConverter) -> None:
        """Tell the converter to lay the beatmap across two stages.

        Args:
            beatmap_converter: The converter about to run.
        """
        mania_beatmap = cast(ManiaBeatmapConverter, beatmap_converter)

        # A beatmap written for mania keeps the stage it was made for.
        if mania_beatmap.IsForCurrentRuleset:
            return

        mania_beatmap.Dual = True
