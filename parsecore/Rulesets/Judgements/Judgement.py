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

from parsecore.Rulesets.Scoring.HitResult import HitResult

# The score awarded for each basic judgement, before combo and mod scaling.
SMALL_TICK_HIT_SCORE = 10
LARGE_TICK_HIT_SCORE = 30
SMALL_BONUS_SCORE = 10
LARGE_BONUS_SCORE = 50


class Judgement:
    """The maximum result an object can earn, and what results are worth."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.Great

    @property
    def MinResult(self) -> HitResult:
        """Return the judgement given when the object is missed."""
        match self.MaxResult:
            case HitResult.SmallBonus | HitResult.LargeBonus:
                return HitResult.IgnoreMiss
            case HitResult.SmallTickHit:
                return HitResult.SmallTickMiss
            case HitResult.LargeTickHit:
                return HitResult.LargeTickMiss
            case HitResult.IgnoreHit:
                return HitResult.IgnoreMiss
            case _:
                return HitResult.Miss

    @property
    def MaxNumericResult(self) -> int:
        """Return the score value of the best possible judgement."""
        return self.ToNumericResult(self.MaxResult)

    @staticmethod
    def ToNumericResult(result: HitResult) -> int:
        """Return the base score value of a judgement.

        Args:
            result: The judgement to score.
        """
        match result:
            case HitResult.SmallTickHit:
                return SMALL_TICK_HIT_SCORE
            case HitResult.LargeTickHit | HitResult.SliderTailHit:
                return LARGE_TICK_HIT_SCORE
            case HitResult.SmallBonus:
                return SMALL_BONUS_SCORE
            case HitResult.LargeBonus:
                return LARGE_BONUS_SCORE
            case HitResult.Meh:
                return 50
            case HitResult.Ok:
                return 100
            case HitResult.Good:
                return 200
            case HitResult.Great | HitResult.Perfect:
                return 300
            case _:
                return 0
