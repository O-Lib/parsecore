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

# Beyond this many patterns back, a repeat is no longer worth remembering.
MAX_REPETITION_INTERVAL = 16


class RepeatingHitPatterns:
    """Alternating patterns grouped by how they repeat."""

    def __init__(self, previous: RepeatingHitPatterns | None = None) -> None:
        """Create a group following another.

        Args:
            previous: The group before this one, if any.
        """
        self.AlternatingMonoPatterns: list = []
        self.Previous = previous
        self.RepetitionInterval: int = MAX_REPETITION_INTERVAL + 1

    @property
    def FirstHitObject(self):
        """Return the note the group opens on."""
        return self.AlternatingMonoPatterns[0].FirstHitObject

    def _is_repetition_of(self, other: RepeatingHitPatterns) -> bool:
        """Return whether this group plays like another.

        Only the first two patterns are compared; that is enough to recognise
        a repeat without demanding the whole group match.

        Args:
            other: The group to compare against.
        """
        if len(self.AlternatingMonoPatterns) != len(other.AlternatingMonoPatterns):
            return False

        for i in range(min(len(self.AlternatingMonoPatterns), 2)):
            if not self.AlternatingMonoPatterns[i].HasIdenticalMonoLength(
                other.AlternatingMonoPatterns[i]
            ):
                return False

        return True

    def FindRepetitionInterval(self) -> None:
        """Record how many groups back this one last appeared.

        Groups that never repeat, or repeat too long ago to matter, are left
        one past the maximum.
        """
        if self.Previous is None:
            self.RepetitionInterval = MAX_REPETITION_INTERVAL + 1
            return

        other = self.Previous
        interval = 1

        while interval < MAX_REPETITION_INTERVAL:
            if self._is_repetition_of(other):
                self.RepetitionInterval = min(interval, MAX_REPETITION_INTERVAL)
                return

            other = other.Previous
            if other is None:
                break

            interval += 1

        self.RepetitionInterval = MAX_REPETITION_INTERVAL + 1
