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


class AlternatingMonoPattern:
    """Colour streaks of one length, alternating sides."""

    def __init__(self) -> None:
        """Create an empty pattern."""
        self.MonoStreaks: list = []
        self.Parent = None
        self.Index: int = 0

    @property
    def FirstHitObject(self):
        """Return the note the pattern opens on."""
        return self.MonoStreaks[0].FirstHitObject

    def IsRepetitionOf(self, other: AlternatingMonoPattern) -> bool:
        """Return whether this pattern plays exactly like another.

        Args:
            other: The pattern to compare against.
        """
        return (
            self.HasIdenticalMonoLength(other)
            and len(other.MonoStreaks) == len(self.MonoStreaks)
            and other.MonoStreaks[0].HitType == self.MonoStreaks[0].HitType
        )

    def HasIdenticalMonoLength(self, other: AlternatingMonoPattern) -> bool:
        """Return whether both patterns open on streaks of the same length.

        Args:
            other: The pattern to compare against.
        """
        return other.MonoStreaks[0].RunLength == self.MonoStreaks[0].RunLength
