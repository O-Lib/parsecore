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

from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows
from parsecore.Rulesets.Taiko.Objects.SwellTick import SwellTick
from parsecore.Rulesets.Taiko.Objects.TaikoHitObject import TaikoHitObject


class Swell(TaikoHitObject):
    """A shaker, completed by alternating hits rather than timing."""

    def __init__(self, start_time: float = 0.0, duration: float = 0.0) -> None:
        """Create a swell.

        Args:
            start_time: The swell's start in milliseconds.
            duration: How long the swell lasts.
        """
        super().__init__(start_time)
        self.Duration: float = duration
        self.RequiredHits: int = 10

    @property
    def EndTime(self) -> float:
        """Return when the swell ends."""
        return self.StartTime + self.Duration

    def CreateNestedHitObjects(self) -> None:
        """Add one tick for every hit the swell asks for."""
        super().CreateNestedHitObjects()

        for _ in range(self.RequiredHits):
            tick = SwellTick(self.StartTime)
            tick.Samples = list(self.Samples)
            self.AddNested(tick)

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Taiko.Judgements.TaikoJudgement import (
            TaikoSwellJudgement,
        )

        return TaikoSwellJudgement()

    def CreateHitWindows(self):
        """Return no windows; a swell is not judged on timing."""
        return EmptyHitWindows()
