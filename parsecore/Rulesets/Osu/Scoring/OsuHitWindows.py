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
GREAT_WINDOW_RANGE = (80.0, 50.0, 20.0)
OK_WINDOW_RANGE = (140.0, 100.0, 60.0)
MEH_WINDOW_RANGE = (200.0, 150.0, 100.0)

# A miss is registered at a fixed distance from the object in osu!.
MISS_WINDOW = 400.0

OSU_RANGES = (
    DifficultyRange(HitResult.Great, *GREAT_WINDOW_RANGE),
    DifficultyRange(HitResult.Ok, *OK_WINDOW_RANGE),
    DifficultyRange(HitResult.Meh, *MEH_WINDOW_RANGE),
    DifficultyRange(HitResult.Miss, MISS_WINDOW, MISS_WINDOW, MISS_WINDOW),
)


class OsuHitWindows(HitWindows):
    """The great, ok, meh and miss windows of osu!."""

    def __init__(self) -> None:
        """Create osu! hit windows with every judgement at zero."""
        super().__init__()
        self._great = 0.0
        self._ok = 0.0
        self._meh = 0.0

    def IsHitResultAllowed(self, result: HitResult) -> bool:
        """Return whether a judgement is awarded in osu!.

        Args:
            result: The judgement to test.
        """
        return result in (
            HitResult.Great,
            HitResult.Ok,
            HitResult.Meh,
            HitResult.Miss,
        )

    def GetRanges(self) -> tuple[DifficultyRange, ...]:
        """Return osu!'s hit window ranges."""
        return OSU_RANGES

    def SetDifficulty(self, difficulty: float) -> None:
        """Compute every window from the beatmap's overall difficulty.

        Each window is floored and then narrowed by half a millisecond, which
        is how osu! matches the behaviour of its stable client.

        Args:
            difficulty: The overall difficulty, ``0`` to ``10``.
        """
        self._great = (
            math.floor(BeatmapDifficulty.DifficultyRange(difficulty, *GREAT_WINDOW_RANGE))
            - 0.5
        )
        self._ok = (
            math.floor(BeatmapDifficulty.DifficultyRange(difficulty, *OK_WINDOW_RANGE))
            - 0.5
        )
        self._meh = (
            math.floor(BeatmapDifficulty.DifficultyRange(difficulty, *MEH_WINDOW_RANGE))
            - 0.5
        )

    def WindowFor(self, result: HitResult) -> float:
        """Return the half-window of a judgement in milliseconds.

        Args:
            result: The judgement to look up.

        Returns:
            The window, or ``0`` for judgements osu! does not award.
        """
        match result:
            case HitResult.Great:
                return self._great
            case HitResult.Ok:
                return self._ok
            case HitResult.Meh:
                return self._meh
            case HitResult.Miss:
                return MISS_WINDOW
            case _:
                return 0.0
