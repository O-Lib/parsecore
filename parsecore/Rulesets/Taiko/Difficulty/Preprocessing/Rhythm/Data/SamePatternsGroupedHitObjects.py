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


class SamePatternsGroupedHitObjects:
    """Rhythm groups that repeat at a steady spacing."""

    def __init__(self, previous, groups: list) -> None:
        """Group rhythm groups that recur evenly.

        Args:
            previous: The pattern group before this one, if any.
            groups: The rhythm groups of this pattern, in time order.
        """
        self.Previous = previous
        self.Groups = groups

    @property
    def GroupInterval(self) -> float:
        """Return how far apart this pattern's rhythm groups sit.

        The first group's own interval measures back to the previous pattern,
        so where a second group exists its interval is the one that describes
        this pattern.
        """
        return self.Groups[1].Interval if len(self.Groups) > 1 else self.Groups[0].Interval

    @property
    def IntervalRatio(self) -> float:
        """Return how this pattern's spacing compares to the one before it."""
        if self.Previous is None:
            return 1.0
        return self.GroupInterval / self.Previous.GroupInterval

    @property
    def FirstHitObject(self):
        """Return the note the pattern opens on."""
        return self.Groups[0].FirstHitObject

    @property
    def AllHitObjects(self) -> list:
        """Return every note across this pattern's rhythm groups."""
        return [h for group in self.Groups for h in group.HitObjects]
