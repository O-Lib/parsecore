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

from dataclasses import dataclass

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Rulesets.Scoring.HitResult import HitResult


@dataclass(frozen=True, slots=True)
class DifficultyRange:
    """The window of one judgement at difficulty 0, 5 and 10."""

    Result: HitResult
    Min: float
    Average: float
    Max: float


BASE_RANGES = (
    DifficultyRange(HitResult.Perfect, 22.4, 19.4, 13.9),
    DifficultyRange(HitResult.Great, 64.0, 49.0, 34.0),
    DifficultyRange(HitResult.Good, 97.0, 82.0, 67.0),
    DifficultyRange(HitResult.Ok, 127.0, 112.0, 97.0),
    DifficultyRange(HitResult.Meh, 151.0, 136.0, 121.0),
    DifficultyRange(HitResult.Miss, 188.0, 173.0, 158.0),
)


class HitWindows:
    """Maps a timing offset onto the judgement it earns."""

    def __init__(self) -> None:
        """Create hit windows with every judgement at zero."""
        self._windows: dict[HitResult, float] = {}

    def GetRanges(self) -> tuple[DifficultyRange, ...]:
        """Return the ranges this ruleset uses."""
        return BASE_RANGES

    def IsHitResultAllowed(self, result: HitResult) -> bool:
        """Return whether this ruleset awards a given judgement.

        Args:
            result: The judgement to test.
        """
        return True

    def SetDifficulty(self, difficulty: float) -> None:
        """Compute every window from the beatmap's overall difficulty.

        Args:
            difficulty: The overall difficulty, ``0`` to ``10``.
        """
        self._windows = {}
        for rng in self.GetRanges():
            if not self.IsHitResultAllowed(rng.Result):
                continue
            self._windows[rng.Result] = BeatmapDifficulty.DifficultyRange(
                difficulty, rng.Min, rng.Average, rng.Max
            )

    def WindowFor(self, result: HitResult) -> float:
        """Return the half-window of a judgement in milliseconds.

        Args:
            result: The judgement to look up.
        """
        return self._windows.get(result, 0.0)

    def ResultFor(self, time_offset: float) -> HitResult:
        """Return the judgement earned by a hit at a timing offset.

        Args:
            time_offset: How far from perfect the hit was, in milliseconds.

        Returns:
            The judgement, or ``HitResult.None_`` if the hit was too early.
        """
        time_offset = abs(time_offset)

        for rng in self.GetRanges():
            if not self.IsHitResultAllowed(rng.Result):
                continue
            if time_offset <= self.WindowFor(rng.Result):
                return rng.Result

        return HitResult.None_

    def CanBeHit(self, time_offset: float) -> bool:
        """Return whether a hit at this offset registers at all.

        Args:
            time_offset: How far from perfect the hit was, in milliseconds.
        """
        return time_offset <= self.WindowFor(HitResult.Miss)
