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


class TaikoColourData:
    """The colour groupings one note belongs to."""

    def __init__(self) -> None:
        """Create colour data with nothing assigned yet."""
        self.MonoStreak = None
        self.AlternatingMonoPattern = None
        self.RepeatingHitPattern = None

    @property
    def PreviousColourChange(self):
        """Return the note before this one's streak, whatever colour it was."""
        if self.MonoStreak is None:
            return None
        return self.MonoStreak.FirstHitObject.PreviousNote(0)

    @property
    def NextColourChange(self):
        """Return the note after this one's streak, whatever colour it is."""
        if self.MonoStreak is None:
            return None
        return self.MonoStreak.LastHitObject.NextNote(0)
