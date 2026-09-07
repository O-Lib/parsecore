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

from parsecore.Audio.HitSampleInfo import HIT_CLAP, HIT_WHISTLE
from parsecore.Rulesets.Taiko.Objects.HitType import HitType
from parsecore.Rulesets.Taiko.Objects.StrongNestedHitObject import (
    StrongNestedHitObject,
)
from parsecore.Rulesets.Taiko.Objects.TaikoStrongableHitObject import (
    TaikoStrongableHitObject,
)


class Hit(TaikoStrongableHitObject):
    """One note, struck on either side of the drum."""

    def __init__(self, start_time: float = 0.0) -> None:
        """Create a note.

        Args:
            start_time: The note's time in milliseconds.
        """
        super().__init__(start_time)
        self.Type: HitType = HitType.Centre

    def _read_from_samples(self) -> None:
        """Derive the drum side and strength from this note's samples."""
        super()._read_from_samples()
        self.Type = (
            HitType.Rim
            if any(s.Name in (HIT_CLAP, HIT_WHISTLE) for s in self._samples)
            else HitType.Centre
        )

    def CreateStrongNestedHit(self, start_time: float) -> StrongNestedHitObject:
        """Return the second hand's hit.

        Args:
            start_time: When the second hand lands.
        """
        nested = StrongNestedHitObject(self, start_time)
        nested.Samples = list(self.Samples)
        return nested


class IgnoreHit(Hit):
    """A note that scores nothing, used where a hit must exist but not count."""

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Taiko.Judgements.TaikoJudgement import (
            TaikoIgnoreJudgement,
        )

        return TaikoIgnoreJudgement()
