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

BASE_SCORES = {
    HitResult.SmallTickHit: 10,
    HitResult.LargeTickHit: 30,
    HitResult.SliderTailHit: 150,
    HitResult.Meh: 50,
    HitResult.Ok: 100,
    HitResult.Good: 200,
    # Perfect earns no more score or accuracy than great.
    HitResult.Great: 300,
    HitResult.Perfect: 300,
    HitResult.SmallBonus: 10,
    HitResult.LargeBonus: 50,
}


def GetBaseScoreForResult(result: HitResult) -> int:
    """Return the base score of a judgement.

    Args:
        result: The judgement to score.
    """
    return BASE_SCORES.get(result, 0)
