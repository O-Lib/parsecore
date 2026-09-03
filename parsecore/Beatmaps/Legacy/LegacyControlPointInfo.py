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
        self.DifficultyPoints: list[DifficultyControlPoint] = []
        self.SamplePoints: list[SampleControlPoint] = []

    @property
    def AllControlPoints(self) -> list[ControlPoint]:
        """Return every control point, in no particular order."""
        return [
            *self.TimingPoints,
            *self.EffectPoints,
            *self.DifficultyPoints,
            *self.SamplePoints,
        ]

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

    def _list_for(self, control_point: ControlPoint) -> list | None:
        """Return the list a control point belongs in, if any.

        Args:
            control_point: The point to place.
        """
        if isinstance(control_point, DifficultyControlPoint):
            return self.DifficultyPoints
        if isinstance(control_point, SampleControlPoint):
            return self.SamplePoints
        return super()._list_for(control_point)

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
            if existing is None:
                return False
            return new_point.IsRedundant(existing)
        return super()._check_already_existing(time, new_point)
