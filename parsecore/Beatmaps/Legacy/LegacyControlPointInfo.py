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

from parsecore.Audio.HitSampleInfo import HitSampleInfo, LegacyHitSampleInfo
from parsecore.Beatmaps.ControlPoints import DifficultyControlPoint as _difficulty
from parsecore.Beatmaps.ControlPoints import SampleControlPoint as _sample
from parsecore.Beatmaps.ControlPoints.ControlPoint import ControlPoint
from parsecore.Beatmaps.ControlPoints.ControlPointInfo import (
    ControlPointInfo,
    _binary_search,
    _binary_search_with_fallback,
)
from parsecore.Beatmaps.ControlPoints.DifficultyControlPoint import (
    DifficultyControlPoint,
)
from parsecore.Beatmaps.ControlPoints.SampleControlPoint import SampleControlPoint


class LegacyControlPointInfo(ControlPointInfo):
    """Control points including the legacy difficulty and sample points."""

    def __init__(self) -> None:
        """Create an empty set of legacy control points."""
        super().__init__()
        self.difficultyPoints: list[DifficultyControlPoint] = []
        self.samplePoints: list[SampleControlPoint] = []

    @property
    def DifficultyPoints(self) -> list[DifficultyControlPoint]:
        """Return all difficulty control points sorted by time."""
        return sorted(self.difficultyPoints, key=lambda dp: dp.Time)

    @property
    def SamplePoints(self) -> list[SampleControlPoint]:
        """Return all sample control points sorted by time."""
        return sorted(self.samplePoints, key=lambda sp: sp.Time)

    def DifficultyPointAt(self, time: float) -> DifficultyControlPoint:
        """Return the difficulty point in effect at ``time``.

        Args:
            time: The time in milliseconds.
        """
        return _binary_search_with_fallback(
            self.DifficultyPoints, time, _difficulty.DEFAULT
        )

    def SamplePointAt(self, time: float) -> SampleControlPoint:
        """Return the sample point in effect at ``time``.

        Args:
            time: The time in milliseconds.
        """
        fallback = self.SamplePoints[0] if self.SamplePoints else _sample.DEFAULT
        return _binary_search_with_fallback(self.SamplePoints, time, fallback)

    def Clear(self) -> None:
        """Remove every control point."""
        super().Clear()
        self.DifficultyPoints.clear()
        self.SamplePoints.clear()

    def GroupItemAdded(self, control_point: ControlPoint) -> None:
        """Handle internal list updates when a control point is added to a group.

        Args:
            control_point: The added control point.
        """
        if isinstance(control_point, DifficultyControlPoint):
            self.difficultyPoints.append(control_point)
        elif isinstance(control_point, SampleControlPoint):
            self.samplePoints.append(control_point)
        super().GroupItemAdded(control_point)

    def GroupItemRemoved(self, control_point: ControlPoint) -> None:
        """Handle internal list updates when a control point is removed from a group.

        Args:
            control_point: The removed control point.
        """
        if isinstance(control_point, DifficultyControlPoint):
            self.difficultyPoints.remove(control_point)
        elif isinstance(control_point, SampleControlPoint):
            self.samplePoints.remove(control_point)
        super().GroupItemRemoved(control_point)

    def _check_already_existing(self, time: float, new_point: ControlPoint) -> bool:
        """Return whether ``new_point`` would be redundant at ``time``.

        Args:
            time: The point's time in milliseconds.
            new_point: The point about to be added.
        """
        if isinstance(new_point, DifficultyControlPoint):
            existing = self.DifficultyPointAt(time)
            return new_point.IsRedundant(existing)
        if isinstance(new_point, SampleControlPoint):
            existing = _binary_search(self.SamplePoints, time)
            return new_point.IsRedundant(existing)

        return super()._check_already_existing(time, new_point)


class LegacySampleControlPoint(SampleControlPoint):
    """A sample control point supporting legacy custom sample banks and volume overrides."""
    
    def __init__(self) -> None:
        """Create a legacy sample control point with default attributes."""
        self.CustomSampleBank = 0

    def ApplyTo(self, hit_sample_info: HitSampleInfo) -> HitSampleInfo:
        """Apply sample settings to a hit sample info instance.

        Args:
            hit_sample_info: The hit sample info to modify.

        Returns:
            The updated hit sample info with custom sample bank and volume applied.
        """
        if isinstance(hit_sample_info, LegacyHitSampleInfo):
            custom_sample_bank = self.CustomSampleBank
            if hit_sample_info.CustomSampleBank > 0:
                custom_sample_bank = hit_sample_info.CustomSampleBank

            volume = self.SampleVolume
            if hit_sample_info.Volume > 0:
                volume = hit_sample_info.Volume

            bank = self.SampleBank
            if hit_sample_info.BankSpecified:
                bank = hit_sample_info.Bank

            return hit_sample_info.WithCustomBank(
                CustomSampleBank=custom_sample_bank,
                Volume=volume,
                Bank=bank
            )

        return super().ApplyTo(hit_sample_info)
    
    def IsRedundant(self, existing: ControlPoint | None) -> bool:
        """Check whether this control point is redundant compared to an existing one.

        Args:
            existing: The active control point to compare against.

        Returns:
            ``True`` if properties match the existing control point.
        """
        return (
            super().IsRedundant(existing)
            and isinstance(existing, LegacySampleControlPoint)
            and self.CustomSampleBank == existing.CustomSampleBank
        )

    def __eq__(self, value: object) -> bool:
        """Check equality with another legacy sample control point.

        Args:
            value: The object to compare with.

        Returns:
            ``True`` if base sample properties and custom sample bank match.
        """
        if not isinstance(value, LegacySampleControlPoint):
            raise NotImplementedError
        return super().__eq__(value) and self.CustomSampleBank == value.CustomSampleBank
