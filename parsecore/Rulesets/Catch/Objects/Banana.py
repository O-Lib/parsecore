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

from parsecore.Rulesets.Catch.Objects.CatchHitObject import CatchHitObject
from parsecore.Rulesets.Catch.Objects.PalpableCatchHitObject import (
    PalpableCatchHitObject,
)
from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows
from parsecore.Utils.Vector2 import f32

# The longest a shower waits between bananas.
MAX_BANANA_SPACING = 100.0


class Banana(PalpableCatchHitObject):
    """One banana from a shower."""

    def __init__(self, start_time: float = 0.0, x: float = 0.0) -> None:
        """Create a banana.

        Args:
            start_time: The banana's time in milliseconds.
            x: Where it falls across the playfield.
        """
        super().__init__(start_time, x)
        self.BananaIndex: int = 0

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Catch.Judgements.CatchJudgement import (
            CatchBananaJudgement,
        )

        return CatchBananaJudgement()


class BananaShower(CatchHitObject):
    """A burst of bananas raining across the playfield."""

    def __init__(self, start_time: float = 0.0, duration: float = 0.0) -> None:
        """Create a banana shower.

        Args:
            start_time: The shower's start in milliseconds.
            duration: How long it lasts.
        """
        super().__init__(start_time)
        self.Duration: float = duration

    @property
    def EndTime(self) -> float:
        """Return when the shower ends."""
        return self.StartTime + self.Duration

    @property
    def LastInCombo(self) -> bool:
        """Return that a shower always closes its combo."""
        return True

    @LastInCombo.setter
    def LastInCombo(self, value: bool) -> None:
        """Ignore attempts to change this; a shower always closes its combo.

        Args:
            value: Ignored.
        """

    def CreateNestedHitObjects(self) -> None:
        """Drop bananas evenly across the shower."""
        super().CreateNestedHitObjects()
        self._create_bananas()

    def _create_bananas(self) -> None:
        """Place bananas at an interval short enough to feel like a shower."""
        start_time = int(self.StartTime)
        end_time = int(self.EndTime)

        spacing = f32(self.EndTime - self.StartTime)
        while spacing > MAX_BANANA_SPACING:
            spacing = f32(spacing / 2)

        if spacing <= 0:
            return

        count = 0
        time = f32(start_time)
        while time <= end_time:
            banana = Banana(time)
            banana.BananaIndex = count
            self.AddNested(banana)

            count += 1
            time = f32(time + spacing)

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Catch.Judgements.CatchJudgement import (
            CatchIgnoreJudgement,
        )

        return CatchIgnoreJudgement()

    def CreateHitWindows(self):
        """Return no windows; a shower is judged through its bananas."""
        return EmptyHitWindows()
