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

from parsecore.Rulesets.Osu.Objects.OsuHitObject import OsuHitObject


class SpinnerTick(OsuHitObject):
    """One of the rotations required to complete a spinner."""

    def __init__(self, start_time: float = 0.0, position=None) -> None:
        """Create a spinner tick.

        Args:
            start_time: The tick's time in milliseconds.
            position: The tick's position.
        """
        super().__init__(start_time, position)
        self.SpinnerDuration: float = 0.0

    @property
    def MaximumJudgementOffset(self) -> float:
        """Return how late a spin still counts: anywhere in the spinner."""
        return self.SpinnerDuration

    def CreateHitWindows(self):
        """Return empty windows; a spin is not judged on its timing."""
        from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows

        return EmptyHitWindows()

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Osu.Judgements.OsuJudgement import (
            OsuSpinnerTickJudgement,
        )

        return OsuSpinnerTickJudgement()


class SpinnerBonusTick(SpinnerTick):
    """A rotation beyond what the spinner required."""

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Osu.Judgements.OsuJudgement import (
            OsuSpinnerBonusTickJudgement,
        )

        return OsuSpinnerBonusTickJudgement()
