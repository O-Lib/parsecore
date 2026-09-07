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

from dataclasses import dataclass, replace

from parsecore.Audio.HitSampleInfo import BANK_NORMAL, HitSampleInfo
from parsecore.Beatmaps.ControlPoints.ControlPoint import ControlPoint

DEFAULT_BANK = BANK_NORMAL


@dataclass(slots=True)
class SampleControlPoint(ControlPoint):
    """Sets the sample bank and volume used from a point onward."""

    SampleBank: str = DEFAULT_BANK
    SampleVolume: int = 100
    CustomSampleBank: int = 0

    def ApplyTo(self, hit_sample_info: HitSampleInfo) -> HitSampleInfo:
        """Return ``hit_sample_info`` with this point's bank and volume filled in.

        Fields the hit object specified itself are left untouched.

        Args:
            hit_sample_info: The sample to complete.

        Returns:
            The completed sample.
        """
        from parsecore.Audio.HitSampleInfo import FileHitSampleInfo
        from parsecore.Rulesets.Objects.Legacy.ConvertHitObjectParser import (
            LegacyHitSampleInfo,
        )

        if isinstance(hit_sample_info, FileHitSampleInfo):
            # A sample named by file is identified by that file, so only its
            # volume is still open to a control point.
            return replace(
                hit_sample_info,
                Volume=(
                    hit_sample_info.Volume
                    if hit_sample_info.Volume > 0
                    else self.SampleVolume
                ),
            )

        if isinstance(hit_sample_info, LegacyHitSampleInfo):
            # A sample keeps whatever the beatmap stated about it and takes
            # the rest from here.
            custom = (
                hit_sample_info.CustomSampleBank
                if hit_sample_info.CustomSampleBank > 0
                else self.CustomSampleBank
            )
            return replace(
                hit_sample_info,
                CustomSampleBank=custom,
                Suffix=str(custom) if custom >= 2 else None,
                Volume=(
                    hit_sample_info.Volume
                    if hit_sample_info.Volume > 0
                    else self.SampleVolume
                ),
                Bank=(
                    hit_sample_info.Bank
                    if hit_sample_info.BankSpecified
                    else self.SampleBank
                ),
            )

        return hit_sample_info.With(
            Bank=hit_sample_info.Bank,
            Volume=(
                hit_sample_info.Volume
                if hit_sample_info.Volume > 0
                else self.SampleVolume
            ),
        )

    def IsRedundant(self, existing: ControlPoint) -> bool:
        """Return whether this point matches ``existing``.

        Args:
            existing: The point already in effect at this time.
        """
        return (
            isinstance(existing, SampleControlPoint)
            and self.SampleBank == existing.SampleBank
            and self.SampleVolume == existing.SampleVolume
            and self.CustomSampleBank == existing.CustomSampleBank
        )


DEFAULT = SampleControlPoint()
