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

from parsecore.Audio.HitSampleInfo import HIT_CLAP, HIT_WHISTLE, HitSampleInfo
from parsecore.Rulesets.Taiko.Objects.HitType import HitType
from parsecore.Rulesets.Taiko.Objects.StrongNestedHitObject import (
    StrongNestedHitObject,
)
from parsecore.Rulesets.Taiko.Objects.TaikoHitObject import TaikoHitObject
from parsecore.Rulesets.Taiko.Objects.TaikoStrongableHitObject import (
    TaikoStrongableHitObject,
)


class Hit(TaikoStrongableHitObject):
    """One note, struck on either side of the drum."""

    def __init__(self) -> None:
        """Create a note."""

        self._type: HitType = HitType.Centre
        self._samples: list[HitSampleInfo] = []
        super().__init__()

    @property
    def Samples(self) -> list[HitSampleInfo]:
        """Return the sample information for this hit.

        Returns:
            The list of hit sample info.
        """
        return self._samples

    @Samples.setter
    def Samples(self, value: list[HitSampleInfo]) -> None:
        """Set the sample information for this hit.

        Args:
            value: The list of hit sample info to set.
        """
        self._samples = value
        self._read_from_samples()

    @property
    def Type(self) -> HitType:
        """Return the type of hit (Centre or Rim).

        Returns:
            The hit type.
        """
        return self._type

    @Type.setter
    def Type(self, value: HitType) -> None:
        """Set the type of hit (Centre or Rim).

        Args:
            value: The hit type to set.
        """
        if value == self._type:
            return

        self._type = value
        self._write_type_to_samples()

    def CreateStrongNestedHit(self, start_time: float) -> StrongNestedHitObject:
        """Return the second hand's hit.

        Args:
            start_time: When the second hand lands.

        Returns:
            The nested strong hit object.
        """
        nested = _HitStrongNestedHit(self)
        nested.StartTime = start_time
        nested.Samples = self.Samples
        return nested

    def _write_type_to_samples(self) -> None:
        """Derive the drum side and strength from this note's samples."""
        rim_samples = [s for s in self.Samples if s.Name in (HIT_CLAP, HIT_WHISTLE)]

        is_rim_type = (self.Type == HitType.Rim)

        if is_rim_type != any(rim_samples):
            if is_rim_type:
                self.Samples.append(self.CreateHitSampleInfo(HIT_CLAP))
            else:
                for sample in rim_samples:
                    self.Samples.remove(sample)

    def _read_from_samples(self) -> None:
        super()._read_from_samples()
        self.Type = (
            HitType.Rim
            if any(s.Name in (HIT_CLAP, HIT_WHISTLE) for s in self.Samples)
            else HitType.Centre
        )


class _HitStrongNestedHit(StrongNestedHitObject):
    """The second hand of a strong note."""
    def __init__(self, parent: TaikoHitObject) -> None:
        """Create a strong nested hit for a note.

        Args:
            parent: The parent hit object.
        """
        super().__init__(parent)


class IgnoreHit(Hit):
    """A note that scores nothing, used where a hit must exist but not count."""

    def CreateJudgement(self):
        """Return the judgement this object is scored with.

        Returns:
            An ignore judgement instance.
        """
        from parsecore.Rulesets.Judgements.IgnoreJudgement import IgnoreJudgement

        return IgnoreJudgement()
