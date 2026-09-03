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

import bisect

from parsecore.Beatmaps.ControlPoints import EffectControlPoint as _effect
from parsecore.Beatmaps.ControlPoints import TimingControlPoint as _timing
from parsecore.Beatmaps.ControlPoints.ControlPoint import ControlPoint
from parsecore.Beatmaps.ControlPoints.EffectControlPoint import EffectControlPoint
from parsecore.Beatmaps.ControlPoints.TimingControlPoint import TimingControlPoint


def _binary_search(points: list, time: float):
    """Return the last point at or before ``time``, or ``None``.

    Args:
        points: A time-sorted list of control points.
        time: The lookup time in milliseconds.
    """
    if not points:
        return None
    idx = bisect.bisect_right([p.Time for p in points], time)
    if idx == 0:
        return None
    return points[idx - 1]


def _binary_search_with_fallback(points: list, time: float, fallback):
    """Return the point in effect at ``time``, or ``fallback``.

    Args:
        points: A time-sorted list of control points.
        time: The lookup time in milliseconds.
        fallback: The value to use when no point precedes ``time``.
    """
    found = _binary_search(points, time)
    return found if found is not None else fallback


class ControlPointGroup:
    """Every control point that takes effect at one moment."""

    def __init__(self, time: float) -> None:
        """Create an empty group.

        Args:
            time: When the group takes effect.
        """
        self.Time = time
        self.ControlPoints: list[ControlPoint] = []

    def Add(self, control_point: ControlPoint) -> None:
        """Add a point, replacing any of the same kind already in the group.

        Args:
            control_point: The point to add.
        """
        for existing in self.ControlPoints:
            if type(existing) is type(control_point):
                self.ControlPoints.remove(existing)
                break

        self.ControlPoints.append(control_point)

    def __lt__(self, other: ControlPointGroup) -> bool:
        """Order groups by time."""
        return self.Time < other.Time


class ControlPointInfo:
    """The timing and effect points of a beatmap."""

    def __init__(self) -> None:
        """Create an empty set of control points."""
        self.TimingPoints: list[TimingControlPoint] = []
        self.EffectPoints: list[EffectControlPoint] = []

    @property
    def AllControlPoints(self) -> list[ControlPoint]:
        """Return every control point, in no particular order."""
        return [*self.TimingPoints, *self.EffectPoints]

    def TimingPointAt(self, time: float) -> TimingControlPoint:
        """Return the timing point in effect at ``time``.

        Args:
            time: The time in milliseconds.

        Returns:
            The active timing point; the first one if ``time`` precedes all of
            them, or the global default when there are none.
        """
        fallback = self.TimingPoints[0] if self.TimingPoints else _timing.DEFAULT
        return _binary_search_with_fallback(self.TimingPoints, time, fallback)

    def EffectPointAt(self, time: float) -> EffectControlPoint:
        """Return the effect point in effect at ``time``.

        Args:
            time: The time in milliseconds.
        """
        return _binary_search_with_fallback(self.EffectPoints, time, _effect.DEFAULT)

    @property
    def Groups(self) -> list[ControlPointGroup]:
        """Return every control point grouped by the time it takes effect.

        osu! stores its points this way round and the encoder walks them in
        that shape, so the groups are built here on demand.
        """
        by_time: dict[float, ControlPointGroup] = {}

        for control_point in self.AllControlPoints:
            group = by_time.get(control_point.Time)
            if group is None:
                group = ControlPointGroup(control_point.Time)
                by_time[control_point.Time] = group
            group.Add(control_point)

        return [by_time[time] for time in sorted(by_time)]

    @property
    def BPMMaximum(self) -> float:
        """Return the highest tempo in the beatmap."""
        if not self.TimingPoints:
            return 60000.0 / _timing.DEFAULT_BEAT_LENGTH
        return 60000.0 / min(p.BeatLength for p in self.TimingPoints)

    @property
    def BPMMinimum(self) -> float:
        """Return the lowest tempo in the beatmap."""
        if not self.TimingPoints:
            return 60000.0 / _timing.DEFAULT_BEAT_LENGTH
        return 60000.0 / max(p.BeatLength for p in self.TimingPoints)

    def Add(
        self, time: float, control_point: ControlPoint, skip_if_redundant: bool = True
    ) -> bool:
        """Insert a control point at ``time``, keeping the list sorted.

        Args:
            time: The point's time in milliseconds.
            control_point: The point to add.
            skip_if_redundant: Whether to drop points that change nothing.

        Returns:
            ``True`` if the point was added.
        """
        control_point.Time = time

        if skip_if_redundant and self._check_already_existing(time, control_point):
            return False

        self._insert(control_point)
        return True

    def Clear(self) -> None:
        """Remove every control point."""
        self.TimingPoints.clear()
        self.EffectPoints.clear()

    def _list_for(self, control_point: ControlPoint) -> list | None:
        """Return the list a control point belongs in, if any.

        Args:
            control_point: The point to place.
        """
        if isinstance(control_point, TimingControlPoint):
            return self.TimingPoints
        if isinstance(control_point, EffectControlPoint):
            return self.EffectPoints
        return None

    def _insert(self, control_point: ControlPoint) -> None:
        """Insert a point into its list at the correct time position.

        Args:
            control_point: The point to insert.
        """
        target = self._list_for(control_point)
        if target is None:
            return
        idx = bisect.bisect_right([p.Time for p in target], control_point.Time)
        target.insert(idx, control_point)

    def _check_already_existing(self, time: float, new_point: ControlPoint) -> bool:
        """Return whether ``new_point`` would be redundant at ``time``.

        Args:
            time: The point's time in milliseconds.
            new_point: The point about to be added.
        """
        existing = None

        if isinstance(new_point, TimingControlPoint):
            # Timing points compare against an exact predecessor only.
            existing = _binary_search(self.TimingPoints, time)
        elif isinstance(new_point, EffectControlPoint):
            existing = self.EffectPointAt(time)

        if existing is None:
            return False
        return new_point.IsRedundant(existing)
