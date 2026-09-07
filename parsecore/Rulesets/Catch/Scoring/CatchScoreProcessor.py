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

from parsecore.Rulesets.Scoring import ScoreProcessor
from parsecore.Rulesets.Scoring.HitResult import HitResult

# Catch counts every caught object equally towards accuracy, which is what
# osu!stable did, so a droplet is worth what a fruit is.
BASE_SCORES = {
    HitResult.Great: 300,
    HitResult.LargeTickHit: 300,
    HitResult.SmallTickHit: 300,
    HitResult.LargeBonus: 200,
}


def GetBaseScoreForResult(result: HitResult) -> int:
    """Return the base score of a judgement in catch.

    Args:
        result: The judgement to score.
    """
    if result in BASE_SCORES:
        return BASE_SCORES[result]

    return ScoreProcessor.GetBaseScoreForResult(result)
