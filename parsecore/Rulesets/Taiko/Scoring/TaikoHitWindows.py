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

import math

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Rulesets.Scoring.HitWindows import DifficultyRange, HitWindows

# The windows at difficulty 0, 5 and 10.
GREAT_WINDOW_RANGE = (50.0, 35.0, 20.0)
OK_WINDOW_RANGE = (120.0, 80.0, 50.0)
MISS_WINDOW_RANGE = (135.0, 95.0, 70.0)

TAIKO_RANGES = (
    DifficultyRange(HitResult.Great, *GREAT_WINDOW_RANGE),
    DifficultyRange(HitResult.Ok, *OK_WINDOW_RANGE),
    DifficultyRange(HitResult.Miss, *MISS_WINDOW_RANGE),
)


class TaikoHitWindows(HitWindows):
    """The great, ok and miss windows of taiko."""

    def __init__(self) -> None:
        """Create taiko hit windows with every judgement at zero."""
        super().__init__()
        self._great = 0.0
        self._ok = 0.0
        self._miss = 0.0

    def IsHitResultAllowed(self, result: HitResult) -> bool:
        """Return whether a judgement is awarded in taiko.

        Args:
            result: The judgement to test.
        """
        return result in (HitResult.Great, HitResult.Ok, HitResult.Miss)

    def GetRanges(self) -> tuple[DifficultyRange, ...]:
        """Return taiko's hit window ranges."""
        return TAIKO_RANGES

    def SetDifficulty(self, difficulty: float) -> None:
        """Derive every window from the beatmap's overall difficulty.

        Each window is floored and then reduced by half a millisecond, which is
        what makes an overall difficulty read back out of a window exact.

        Args:
            difficulty: The beatmap's overall difficulty.
        """
        self._great = (
            math.floor(BeatmapDifficulty.DifficultyRange(difficulty, *GREAT_WINDOW_RANGE))
            - 0.5
        )
        self._ok = (
            math.floor(BeatmapDifficulty.DifficultyRange(difficulty, *OK_WINDOW_RANGE))
            - 0.5
        )
        self._miss = (
            math.floor(BeatmapDifficulty.DifficultyRange(difficulty, *MISS_WINDOW_RANGE))
            - 0.5
        )

    def WindowFor(self, result: HitResult) -> float:
        """Return the window a judgement is earned within.

        Args:
            result: The judgement to look up.

        Raises:
            ValueError: If taiko does not award that judgement.
        """
        match result:
            case HitResult.Great:
                return self._great
            case HitResult.Ok:
                return self._ok
            case HitResult.Miss:
                return self._miss
        raise ValueError(f"taiko has no window for {result!r}")
