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

from parsecore.Rulesets.Mania.Objects.ManiaHitObject import ManiaHitObject
from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows


class HoldNoteBody(ManiaHitObject):
    """The held part of a hold note."""

    def __init__(
        self, start_time: float = 0.0, column: int = 0, duration: float = 0.0
    ) -> None:
        """Create a hold note body.

        Args:
            start_time: When the hold begins.
            column: The column it is played in.
            duration: How long it must be held.
        """
        super().__init__(start_time, column)
        self.Duration = duration

    @property
    def EndTime(self) -> float:
        """Return when the hold ends."""
        return self.StartTime + self.Duration

    def CreateHitWindows(self):
        """Return no windows; the body is judged by holding, not by timing."""
        return EmptyHitWindows()

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Mania.Judgements.ManiaJudgement import (
            HoldNoteBodyJudgement,
        )

        return HoldNoteBodyJudgement()
