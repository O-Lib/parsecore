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
from parsecore.Rulesets.Objects.Legacy.IHasLegacyHitObjectType import (
    IHasLegacyHitObjectType,
)
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
from parsecore.Rulesets.Objects.Types.IHasPath import IHasPath
from parsecore.Rulesets.Objects.Types.IHasRepeats import IHasRepeats
from parsecore.Rulesets.Objects.Types.IHasXPosition import IHasXPosition


class PassThroughPatternGenerator(LegacyPatternGenerator):
    """Turns one object into one note, in the column the beatmap named."""

    def Generate(self) -> list[Pattern]:
        """Return the single pattern for this object."""
        position = self.HitObject.X if isinstance(self.HitObject, IHasXPosition) else 0.0
        column = self.GetColumn(position)

        pattern = Pattern()
        if isinstance(self.HitObject, IHasDuration):
            duration = self.HitObject.Duration
            legacy_type = isinstance(self.HitObject, IHasLegacyHitObjectType)
            play_sliding_samples = (
                legacy_type and legacy_type & LegacyHitObjectType.Slider
            ) or isinstance(self.HitObject, IHasPath)

            node_samples = (
                self.HitObject.NodeSamples
                if isinstance(self.HitObject, IHasRepeats)
                else CreateDefaultNodeSamples(self.HitObject)
            )

            hold = HoldNote()
            hold.StartTime = self.HitObject.StartTime
            hold.Duration = duration
            hold.Column = column
            hold.Samples = self.HitObject.Samples
            hold.PlaySlidingSamples = play_sliding_samples
            hold.NodeSamples = node_samples
            pattern.Add(hold)
        else:
            note = Note()
            note.StartTime = self.HitObject.StartTime
            note.Column = column
            note.Samples = self.HitObject.Samples
            pattern.Add(note)

        return [pattern]
