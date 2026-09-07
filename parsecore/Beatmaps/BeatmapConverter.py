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

import copy

from parsecore.Beatmaps.Beatmap import Beatmap
from parsecore.Rulesets.Objects.HitObject import HitObject


class BeatmapConverter:
    """Turns a decoded beatmap into the objects one ruleset plays."""

    def __init__(self, beatmap) -> None:
        """Create a converter for a beatmap.

        Args:
            beatmap: The decoded beatmap to convert.
        """
        self.Beatmap = beatmap

    def CanConvert(self) -> bool:
        """Return whether this ruleset can play the beatmap."""
        raise NotImplementedError

    def CreateBeatmap(self) -> Beatmap:
        """Return an empty beatmap of the ruleset's own type."""
        return Beatmap()

    def ConvertHitObject(self, original: HitObject, beatmap) -> list[HitObject]:
        """Convert one object into the ruleset's own objects.

        Args:
            original: The decoded object.
            beatmap: The beatmap being converted.

        Returns:
            Zero or more objects for the target ruleset.
        """
        raise NotImplementedError

    def Convert(self) -> Beatmap:
        """Convert the whole beatmap.

        Returns:
            A beatmap holding this ruleset's objects, in time order.

        Raises:
            ValueError: If the beatmap cannot be converted to this ruleset.
        """
        if not self.CanConvert():
            raise ValueError("this beatmap cannot be converted to that ruleset")

        return self.ConvertBeatmap(copy.deepcopy(self.Beatmap))

    def ConvertBeatmap(self, original: Beatmap) -> Beatmap:
        """Convert every object of a beatmap into this ruleset's own.

        Rulesets that need to look at the beatmap as a whole override this,
        call it, and adjust what it returns.

        Args:
            original: A private copy of the decoded beatmap.

        Returns:
            A beatmap holding this ruleset's objects, in time order.
        """
        converted = self.CreateBeatmap()
        converted.BeatmapInfo = original.BeatmapInfo
        converted.ControlPointInfo = original.ControlPointInfo
        converted.Breaks = original.Breaks
        converted.UnhandledEventLines = original.UnhandledEventLines

        objects: list[HitObject] = []
        for obj in original.HitObjects:
            objects.extend(self.ConvertHitObject(obj, original))

        objects.sort(key=lambda h: h.StartTime)
        converted.HitObjects = objects

        # Defaults are deliberately not applied here: the processor runs
        # between conversion and defaults, exactly as it does in osu!.
        return converted
