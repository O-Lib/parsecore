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

from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Scoring.HitResult import HitResult

# The shortest delta time a difficulty calculator will consider, guarding
# against division by (near-)zero on stacked objects.
MIN_DELTA_TIME = 25.0


class DifficultyHitObject:
    """One object in the sequence a difficulty calculator walks."""

    def __init__(
        self,
        hit_object: HitObject,
        last_object: HitObject,
        clock_rate: float,
        objects: list[DifficultyHitObject],
        index: int,
    ) -> None:
        """Wrap a hit object for difficulty calculation.

        Args:
            hit_object: The object being wrapped.
            last_object: The object immediately before it.
            clock_rate: The rate the beatmap is played at.
            objects: The list this object is part of.
            index: This object's position in that list.
        """
        self._objects = objects
        self.Index = index
        self.ClockRate = clock_rate
        self.BaseObject = hit_object
        self.LastObject = last_object

        self.DeltaTime = (hit_object.StartTime - last_object.StartTime) / clock_rate
        self.StartTime = hit_object.StartTime / clock_rate
        self.EndTime = hit_object.GetEndTime() / clock_rate
        self.HitWindowGreat = self.HitWindow(HitResult.Great)

    def Previous(self, backwards_index: int = 0) -> DifficultyHitObject | None:
        """Return an earlier object, or ``None`` if there is none.

        Args:
            backwards_index: ``0`` for the immediately preceding object.
        """
        index = self.Index - (backwards_index + 1)
        return self._objects[index] if 0 <= index < len(self._objects) else None

    def Next(self, forwards_index: int = 0) -> DifficultyHitObject | None:
        """Return a later object, or ``None`` if there is none.

        Args:
            forwards_index: ``0`` for the immediately following object.
        """
        index = self.Index + (forwards_index + 1)
        return self._objects[index] if 0 <= index < len(self._objects) else None

    def HitWindow(self, hit_result: HitResult) -> float:
        """Return the full width of a judgement window, at the clock rate.

        Args:
            hit_result: The judgement to look up.
        """
        return 2 * self._raw_hit_window(hit_result) / self.ClockRate

    def _raw_hit_window(self, hit_result: HitResult) -> float:
        """Return a judgement window before the clock rate is applied.

        An object with no windows of its own (an osu! slider, say) defers to
        the first nested object that has them.

        Args:
            hit_result: The judgement to look up.
        """
        windows = self.BaseObject.HitWindows
        if windows is not None and windows.GetRanges():
            return windows.WindowFor(hit_result)

        for nested in self.BaseObject.NestedHitObjects:
            nested_windows = nested.HitWindows
            if nested_windows is not None and nested_windows.GetRanges():
                return nested_windows.WindowFor(hit_result)

        return 0.0

    def __repr__(self) -> str:
        """Return an unambiguous representation."""
        return (
            f"{type(self).__name__}(Index={self.Index}, "
            f"StartTime={self.StartTime:.2f}, DeltaTime={self.DeltaTime:.2f})"
        )
