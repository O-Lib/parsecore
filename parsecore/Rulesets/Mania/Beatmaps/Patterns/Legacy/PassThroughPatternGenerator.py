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

from parsecore.Beatmaps.Legacy.LegacyHitObjectType import LegacyHitObjectType
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.LegacyPatternGenerator import (
    LegacyPatternGenerator,
)
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Pattern import Pattern
from parsecore.Rulesets.Mania.Objects.HoldNote import (
    CreateDefaultNodeSamples,
    HoldNote,
)
from parsecore.Rulesets.Mania.Objects.Note import Note


class PassThroughPatternGenerator(LegacyPatternGenerator):
    """Turns one object into one note, in the column the beatmap named."""

    def Generate(self) -> list:
        """Return the single pattern for this object."""
        column = self.GetColumn(getattr(self.HitObject, "X", 0.0))

        pattern = Pattern()
        duration = getattr(self.HitObject, "Duration", None)

        if duration is None and hasattr(self.HitObject, "EndTime"):
            duration = self.HitObject.EndTime - self.HitObject.StartTime

        if duration is not None:
            legacy_type = getattr(self.HitObject, "LegacyType", None)
            play_sliding_samples = (
                legacy_type is not None
                and legacy_type & LegacyHitObjectType.Slider
            ) or hasattr(self.HitObject, "Path")

            node_samples = getattr(self.HitObject, "NodeSamples", None)
            if not node_samples:
                node_samples = CreateDefaultNodeSamples(self.HitObject)

            hold = HoldNote(
                self.HitObject.StartTime,
                column,
                duration,
                play_sliding_samples=bool(play_sliding_samples),
                node_samples=node_samples,
            )
            hold.Samples = self.HitObject.Samples
            pattern.Add(hold)
        else:
            note = Note(self.HitObject.StartTime, column)
            note.Samples = self.HitObject.Samples
            pattern.Add(note)

        return [pattern]
