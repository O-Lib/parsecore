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

from parsecore.Rulesets.Judgements.Judgement import Judgement
from parsecore.Rulesets.Scoring.HitResult import HitResult


class OsuJudgement(Judgement):
    """A normal osu! object: a circle, slider head or spinner."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.Great


class OsuIgnoreJudgement(OsuJudgement):
    """An object that is never judged itself, only through its children."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.IgnoreHit


class SliderTickJudgement(OsuJudgement):
    """A tick along a slider's path."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.LargeTickHit


class SliderEndJudgement(OsuJudgement):
    """The end of one span of a slider, such as a repeat."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.LargeTickHit


class TailJudgement(SliderEndJudgement):
    """A slider's tail under lazer slider behaviour."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.SliderTailHit


class LegacyTailJudgement(OsuJudgement):
    """A slider's tail under classic slider behaviour."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.SmallTickHit


class OsuSpinnerTickJudgement(OsuJudgement):
    """One of the rotations a spinner requires."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.SmallBonus


class OsuSpinnerBonusTickJudgement(OsuSpinnerTickJudgement):
    """A rotation beyond what a spinner required."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.LargeBonus
