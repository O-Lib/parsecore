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


class CatchJudgement(Judgement):
    """A fruit, the thing catch is actually about."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.Great


class CatchDropletJudgement(CatchJudgement):
    """A droplet along a juice stream."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.LargeTickHit


class CatchTinyDropletJudgement(CatchJudgement):
    """One of the fine droplets filling the gaps of a juice stream."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.SmallTickHit


class CatchBananaJudgement(CatchJudgement):
    """A banana from a shower, worth a bonus rather than combo."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.LargeBonus


class CatchIgnoreJudgement(CatchJudgement):
    """An object that is never caught itself, only through its children."""

    @property
    def MaxResult(self) -> HitResult:
        """Return the best judgement this object can receive."""
        return HitResult.IgnoreHit
