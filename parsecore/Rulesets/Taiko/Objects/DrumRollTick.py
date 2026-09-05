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
from parsecore.Rulesets.Taiko.Objects.StrongNestedHitObject import (
    StrongNestedHitObject,
)
from parsecore.Rulesets.Taiko.Objects.TaikoStrongableHitObject import (
    TaikoStrongableHitObject,
)


class DrumRollTick(TaikoStrongableHitObject):
    """One hit the player must land while rolling."""

    def __init__(self, parent=None, start_time: float = 0.0) -> None:
        """Create a drum roll tick.

        Args:
            parent: The drum roll this tick belongs to.
            start_time: The tick's time in milliseconds.
        """
        super().__init__(start_time)
        self.Parent = parent
        self.FirstTick: bool = False
        self.TickSpacing: float = 0.0

    @property
    def HitWindow(self) -> float:
        """Return how far either side of the tick a hit still counts."""
        return self.TickSpacing / 2

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Taiko.Judgements.TaikoJudgement import (
            TaikoDrumRollTickJudgement,
        )

        return TaikoDrumRollTickJudgement()

    def CreateHitWindows(self):
        """Return no windows; a tick is judged on its own spacing."""
        return EmptyHitWindows()

    def CreateStrongNestedHit(self, start_time: float) -> StrongNestedHitObject:
        """Return the second hand's hit.

        Args:
            start_time: When the second hand lands.
        """
        nested = StrongNestedHitObject(self, start_time)
        nested.Samples = list(self.Samples)
        return nested
