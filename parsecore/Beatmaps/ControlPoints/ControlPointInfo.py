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
from collections.abc import Callable
from typing import TypeVar

from parsecore.Beatmaps.ControlPoints import EffectControlPoint as _effect
from parsecore.Beatmaps.ControlPoints import TimingControlPoint as _timing
from parsecore.Beatmaps.ControlPoints.ControlPoint import ControlPoint
from parsecore.Beatmaps.ControlPoints.EffectControlPoint import EffectControlPoint
from parsecore.Beatmaps.ControlPoints.IControlPoint import IControlPoint
from parsecore.Beatmaps.ControlPoints.TimingControlPoint import TimingControlPoint

T = TypeVar("T", bound=IControlPoint)


def _binary_search(points: list[T], time: float) -> T | None:
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


def _binary_search_with_fallback(points: list[T], time: float, fallback: T) -> T:
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

        self._item_added: list[Callable[[ControlPoint], None]] = []
        self._item_removed: list[Callable[[ControlPoint], None]] = []

    def Add(self, control_point: ControlPoint) -> None:
        """Add a point, replacing any of the same kind already in the group.

        Args:
            control_point: The point to add.
        """
        for existing in self.ControlPoints:
            if type(existing) is type(control_point):
                self.ControlPoints.remove(existing)
                break

        control_point.AttachGroup(self)
        self.ControlPoints.append(control_point)

        for handler in self._item_added:
            handler(control_point)

    def Remove(self, control_point: ControlPoint) -> None:
        """Remove a control point from this group and notify listeners.

        Args:
            control_point: The control point to remove.
        """
        self.ControlPoints.remove(control_point)

        for handler in self._item_removed:
            handler(control_point)

    def __lt__(self, other: ControlPointGroup) -> bool:
        """Order groups by time."""
        return self.Time < other.Time


class ControlPointInfo:
    """The timing and effect points of a beatmap."""

    def __init__(self) -> None:
        """Create an empty set of control points."""
        self.timingPoints: list[TimingControlPoint] = []
        self.effectPoints: list[EffectControlPoint] = []
        self.groups: list[ControlPointGroup] = []

    @property
    def TimingPoints(self) -> list[TimingControlPoint]:
        """Return all timing control points sorted by time."""
        return sorted(self.timingPoints, key=lambda tp: tp.Time)

    @property
    def EffectPoints(self) -> list[EffectControlPoint]:
        """Return all effect control points sorted by time."""
        return sorted(self.effectPoints, key=lambda ep: ep.Time)

    @property
    def AllControlPoints(self) -> list[ControlPoint]:
        """Return every control point, in no particular order."""
        return [cp for group in self.Groups for cp in group.ControlPoints]

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
        return self.groups

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

    def Add(self, time: float, control_point: ControlPoint) -> bool:
        """Insert a control point at ``time``, keeping the list sorted.

        Args:
            time: The point's time in milliseconds.
            control_point: The point to add.

        Returns:
            ``True`` if the point was added.
        """
        control_point.Time = time

        if self._check_already_existing(time, control_point):
            return False

        self.GroupAt(time, True).Add(control_point)
        return True

    def RemoveGroup(self, group: ControlPointGroup) -> None:
        """Remove a control point group and clear its contained points.

        Args:
            group: The control point group to remove.
        """
        for control_point in group.ControlPoints:
            group.Remove(control_point)

        self.groups.remove(group)

    def Clear(self) -> None:
        """Remove every control point."""
        self.groups.clear()
        self.timingPoints.clear()
        self.effectPoints.clear()

    def GroupAt(self, time: float, add_if_no_existing: bool = False) -> ControlPointGroup | None:
        """Return the control point group at the specified time.

        Args:
            time: The lookup time in milliseconds.
            add_if_no_existing: Whether to create and insert a new group if none exists.

        Returns:
            The existing or newly created group, or ``None`` if not found and not created.
        """
        new_group = ControlPointGroup(time)
        index = bisect.bisect_left(self.groups, new_group)

        if index < len(self.groups) and self.groups[index].Time == time:
            return self.groups[index]

        if add_if_no_existing:
            new_group._item_added.append(self.GroupItemAdded)
            new_group._item_removed.append(self.GroupItemRemoved)

            self.groups.insert(index, new_group)
            return new_group

        return None

    def DeepClone(self) -> ControlPointInfo:
        """Return a deep copy of this control point info structure."""
        control_point_info = ControlPointInfo()
        for point in self.AllControlPoints:
            control_point_info.Add(point.Time, point.DeepClone())
        return control_point_info

    def GroupItemAdded(self, control_point: ControlPoint) -> None:
        """Handle internal list updates when a control point is added to a group.

        Args:
            control_point: The added control point.
        """
        if isinstance(control_point, TimingControlPoint):
            self.timingPoints.append(control_point)
        elif isinstance(control_point, EffectControlPoint):
            self.effectPoints.append(control_point)

    def GroupItemRemoved(self, control_point: ControlPoint) -> None:
        """Handle internal list updates when a control point is removed from a group.

        Args:
            control_point: The removed control point.
        """
        if isinstance(control_point, TimingControlPoint):
            self.timingPoints.remove(control_point)
        elif isinstance(control_point, EffectControlPoint):
            self.effectPoints.remove(control_point)

    def _check_already_existing(self, time: float, new_point: ControlPoint) -> bool:
        """Return whether ``new_point`` would be redundant at ``time``.

        Args:
            time: The point's time in milliseconds.
            new_point: The point about to be added.
        """
        existing: ControlPoint | None = None

        if isinstance(new_point, TimingControlPoint):
            # Timing points compare against an exact predecessor only.
            existing = _binary_search(self.TimingPoints, time)
        elif isinstance(new_point, EffectControlPoint):
            existing = self.EffectPointAt(time)

        return new_point.IsRedundant(existing)
