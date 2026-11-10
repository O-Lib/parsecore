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

from dataclasses import dataclass
from typing import TYPE_CHECKING

from parsecore.Beatmaps.ControlPoints.ControlPoint import ControlPoint
from parsecore.Utils.Precision import Clamp

if TYPE_CHECKING:
    from parsecore.Audio.HitSampleInfo import HitSampleInfo

DEFAULT_BANK = "normal"


@dataclass(slots=True)
class SampleControlPoint(ControlPoint):
    """Sets the sample bank and volume used from a point onward."""

    SampleBank: str = DEFAULT_BANK
    SampleVolume: int = 100

    def __post_init__(self) -> None:
        """Clamp the sample volume to the range osu! accepts (0 to 100)."""
        self.SampleVolume = Clamp(self.SampleVolume, 0, 100)

    def ApplyTo(self, hit_sample_info: HitSampleInfo) -> HitSampleInfo:
        """Return ``hit_sample_info`` with this point's bank and volume filled in.

        Fields the hit object specified itself are left untouched.

        Args:
            hit_sample_info: The sample to complete.

        Returns:
            The completed sample.
        """
        return hit_sample_info.With(
            Bank=hit_sample_info.Bank,
            Volume=hit_sample_info.Volume if hit_sample_info.Volume > 0 else self.SampleVolume
        )

    def IsRedundant(self, existing: ControlPoint | None) -> bool:
        """Return whether this point matches ``existing``.

        Args:
            existing: The point already in effect at this time.
        """
        return (
            isinstance(existing, SampleControlPoint)
            and self.SampleBank == existing.SampleBank
            and self.SampleVolume == existing.SampleVolume
        )

    def __eq__(self, value: object) -> bool:
        """Check equality with another sample control point.

        Args:
            value: The object to compare with.

        Returns:
            ``True`` if sample bank, volume, and time match.
        """
        if not isinstance(value, SampleControlPoint):
            raise NotImplementedError
        return (
            super().__eq__(value)
            and self.SampleBank == value.SampleBank
            and self.SampleVolume == value.SampleVolume
        )


DEFAULT = SampleControlPoint()
