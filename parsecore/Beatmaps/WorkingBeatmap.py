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

from parsecore.Beatmaps.BeatmapProcessor import BeatmapProcessor
from parsecore.Rulesets.Mods.IApplicableToBeatmap import IApplicableToBeatmap
from parsecore.Rulesets.Mods.IApplicableToBeatmapConverter import (
    IApplicableToBeatmapConverter,
)
from parsecore.Rulesets.Mods.IApplicableToBeatmapProcessor import (
    IApplicableToBeatmapProcessor,
)
from parsecore.Rulesets.Mods.IApplicableToDifficulty import IApplicableToDifficulty
from parsecore.Rulesets.Mods.IApplicableToHitObject import IApplicableToHitObject


class WorkingBeatmap:
    """A decoded beatmap, ready to be converted for a ruleset."""

    def __init__(self, beatmap) -> None:
        """Wrap a decoded beatmap.

        Args:
            beatmap: The beatmap as read from the file.
        """
        self.Beatmap = beatmap

    def GetPlayableBeatmap(
        self,
        converter_type: type,
        processor_type: type | None = None,
        mods: list | None = None,
    ):
        """Return the beatmap as the given ruleset plays it.

        Args:
            converter_type: The ruleset's beatmap converter.
            processor_type: The ruleset's beatmap processor, if it has one.
            mods: The mods to apply.

        Returns:
            The converted, processed beatmap.
        """
        mods = list(mods or [])

        converter = converter_type(self.Beatmap)

        # Conversion mods run first: the shape of the converted beatmap, such
        # as how many mania columns it gets, cannot be changed afterwards.
        for mod in mods:
            if isinstance(mod, IApplicableToBeatmapConverter):
                mod.ApplyToBeatmapConverter(converter)

        converted = converter.Convert()

        difficulty_mods = [
            mod for mod in mods if isinstance(mod, IApplicableToDifficulty)
        ]
        if difficulty_mods:
            # The difficulty is copied first, so a mod never writes back into
            # the beatmap this was built from.
            converted.Difficulty = converted.Difficulty.Clone()
            for mod in difficulty_mods:
                mod.ApplyToDifficulty(converted.Difficulty)

        processor: BeatmapProcessor | None = (
            processor_type(converted) if processor_type else None
        )

        if processor is not None:
            for mod in mods:
                if isinstance(mod, IApplicableToBeatmapProcessor):
                    mod.ApplyToBeatmapProcessor(processor)

            processor.PreProcess()

        for hit_object in converted.HitObjects:
            hit_object.ApplyDefaults(converted.ControlPointInfo, converted.Difficulty)

        # Objects are rewritten once they know their size and timing, but
        # before the processor stacks them, so stacking sees the new positions.
        for mod in mods:
            if isinstance(mod, IApplicableToHitObject):
                for hit_object in converted.HitObjects:
                    mod.ApplyToHitObject(hit_object)

        if processor is not None:
            processor.PostProcess()

        for mod in mods:
            if isinstance(mod, IApplicableToBeatmap):
                mod.ApplyToBeatmap(converted)

        return converted
