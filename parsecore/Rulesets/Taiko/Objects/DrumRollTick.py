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

from typing import TYPE_CHECKING

from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows
from parsecore.Rulesets.Taiko.Objects.StrongNestedHitObject import (
    StrongNestedHitObject,
)
from parsecore.Rulesets.Taiko.Objects.TaikoHitObject import TaikoHitObject
from parsecore.Rulesets.Taiko.Objects.TaikoStrongableHitObject import (
    TaikoStrongableHitObject,
)

if TYPE_CHECKING:
    from parsecore.Rulesets.Taiko.Objects.DrumRoll import DrumRoll


class DrumRollTick(TaikoStrongableHitObject):
    """One hit the player must land while rolling."""

    def __init__(self, parent: DrumRoll) -> None:
        """Create a drum roll tick.

        Args:
            parent: The drum roll this tick belongs to.
        """
        super().__init__()
        self.Parent = parent
        self.FirstTick: bool = False
        self.TickSpacing: float = 0.0

    @property
    def HitWindow(self) -> float:
        """Return how far either side of the tick a hit still counts."""
        return self.TickSpacing / 2

    def CreateJudgement(self):
        """Return the judgement this object is scored with.

        Returns:
            The taiko drum roll tick judgement instance.
        """
        from parsecore.Rulesets.Taiko.Judgements.TaikoJudgement import (
            TaikoDrumRollTickJudgement,
        )

        return TaikoDrumRollTickJudgement()

    def CreateHitWindows(self):
        """Return no windows; a tick is judged on its own spacing.

        Returns:
            An empty hit windows instance.
        """
        return EmptyHitWindows()

    def CreateStrongNestedHit(self, start_time: float) -> StrongNestedHitObject:
        """Return the second hand's hit.

        Args:
            start_time: When the second hand lands.

        Returns:
            The nested strong hit object for the tick.
        """
        nested = _DrumRollTickStrongNestedHit(self)
        nested.StartTime = start_time
        nested.Samples = self.Samples
        return nested


class _DrumRollTickStrongNestedHit(StrongNestedHitObject):
    """The second hand of a strong drum roll tick."""
    
    def __init__(self, parent: TaikoHitObject) -> None:
        """Create a strong nested hit for a drum roll tick.

        Args:
            parent: The parent hit object.
        """
        super().__init__(parent)
