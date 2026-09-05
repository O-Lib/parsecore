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

# The window of each judgement at difficulty 0, 5 and 10.
PERFECT_WINDOW_RANGE = DifficultyRange(HitResult.Perfect, 22.4, 19.4, 13.9)
GREAT_WINDOW_RANGE = DifficultyRange(HitResult.Great, 64.0, 49.0, 34.0)
GOOD_WINDOW_RANGE = DifficultyRange(HitResult.Good, 97.0, 82.0, 67.0)
OK_WINDOW_RANGE = DifficultyRange(HitResult.Ok, 127.0, 112.0, 97.0)
MEH_WINDOW_RANGE = DifficultyRange(HitResult.Meh, 151.0, 136.0, 121.0)
MISS_WINDOW_RANGE = DifficultyRange(HitResult.Miss, 188.0, 173.0, 158.0)

RANGES = (
    PERFECT_WINDOW_RANGE,
    GREAT_WINDOW_RANGE,
    GOOD_WINDOW_RANGE,
    OK_WINDOW_RANGE,
    MEH_WINDOW_RANGE,
    MISS_WINDOW_RANGE,
)

ALLOWED_RESULTS = (
    HitResult.Perfect,
    HitResult.Great,
    HitResult.Good,
    HitResult.Ok,
    HitResult.Meh,
    HitResult.Miss,
)


class ManiaHitWindows(HitWindows):
    """Maps a timing offset onto the judgement it earns on a mania stage."""

    def __init__(self) -> None:
        """Create windows at difficulty zero, unmodified."""
        super().__init__()
        self._speed_multiplier = 1.0
        self._difficulty_multiplier = 1.0
        self._overall_difficulty = 0.0
        self._classic_mod_active = False
        self._score_v2_active = False
        self._is_convert = False
        self._update()

    @property
    def SpeedMultiplier(self) -> float:
        """Return what the playback rate does to these windows."""
        return self._speed_multiplier

    @SpeedMultiplier.setter
    def SpeedMultiplier(self, value: float) -> None:
        """Scale the windows with the playback rate.

        Both speeding up and slowing down multiply, because the point is to
        leave the window the same length in real time.

        Args:
            value: The rate the beatmap is played at.
        """
        self._speed_multiplier = value
        self._update()

    @property
    def DifficultyMultiplier(self) -> float:
        """Return what the mods do to these windows."""
        return self._difficulty_multiplier

    @DifficultyMultiplier.setter
    def DifficultyMultiplier(self, value: float) -> None:
        """Tighten or loosen the windows.

        Args:
            value: Above one tightens the windows, below one loosens them.
        """
        self._difficulty_multiplier = value
        self._update()

    @property
    def ClassicModActive(self) -> bool:
        """Return whether osu!stable's own window table is in use."""
        return self._classic_mod_active

    @ClassicModActive.setter
    def ClassicModActive(self, value: bool) -> None:
        """Switch to osu!stable's window table.

        Args:
            value: Whether the classic mod is active.
        """
        self._classic_mod_active = value
        self._update()

    @property
    def ScoreV2Active(self) -> bool:
        """Return whether the second scoring version is in use."""
        return self._score_v2_active

    @ScoreV2Active.setter
    def ScoreV2Active(self, value: bool) -> None:
        """Switch the second scoring version on, which undoes the classic table.

        Args:
            value: Whether the score v2 mod is active.
        """
        self._score_v2_active = value
        self._update()

    @property
    def IsConvert(self) -> bool:
        """Return whether the beatmap was written for another ruleset."""
        return self._is_convert

    @IsConvert.setter
    def IsConvert(self, value: bool) -> None:
        """Set whether the beatmap was written for another ruleset.

        Args:
            value: Whether this is a converted beatmap.
        """
        self._is_convert = value
        self._update()

    def IsHitResultAllowed(self, result: HitResult) -> bool:
        """Return whether mania awards a given judgement.

        Args:
            result: The judgement to test.
        """
        return result in ALLOWED_RESULTS

    def SetDifficulty(self, difficulty: float) -> None:
        """Compute every window from the beatmap's overall difficulty.

        Args:
            difficulty: The overall difficulty, ``0`` to ``10``.
        """
        self._overall_difficulty = difficulty
        self._update()

    def _total_multiplier(self) -> float:
        """Return the single factor every window is scaled by."""
        return self._speed_multiplier / self._difficulty_multiplier

    def _update(self) -> None:
        """Recompute every window from the difficulty and the mods."""
        multiplier = self._total_multiplier()

        if self._classic_mod_active and not self._score_v2_active:
            if self._is_convert:
                # A converted beatmap only ever had two window tables in
                # osu!stable, chosen by a single threshold.
                lenient = round(self._overall_difficulty) <= 4
                windows = [
                    (HitResult.Perfect, 16.0),
                    (HitResult.Great, 47.0 if lenient else 34.0),
                    (HitResult.Good, 77.0 if lenient else 67.0),
                    (HitResult.Ok, 97.0),
                    (HitResult.Meh, 121.0),
                    (HitResult.Miss, 158.0),
                ]
            else:
                inverted_od = min(max(10.0 - self._overall_difficulty, 0.0), 10.0)
                windows = [
                    (HitResult.Perfect, 16.0),
                    (HitResult.Great, 34.0 + 3 * inverted_od),
                    (HitResult.Good, 67.0 + 3 * inverted_od),
                    (HitResult.Ok, 97.0 + 3 * inverted_od),
                    (HitResult.Meh, 121.0 + 3 * inverted_od),
                    (HitResult.Miss, 158.0 + 3 * inverted_od),
                ]
        else:
            windows = [
                (
                    rng.Result,
                    BeatmapDifficulty.DifficultyRange(
                        self._overall_difficulty, rng.Min, rng.Average, rng.Max
                    ),
                )
                for rng in RANGES
            ]

        # osu! rounds each window down to a whole millisecond and then adds
        # half of one, so a hit exactly on the boundary falls inside.
        self._windows = {
            result: math.floor(window * multiplier) + 0.5
            for result, window in windows
        }

    def GetRanges(self) -> tuple[DifficultyRange, ...]:
        """Return the ranges mania uses."""
        return RANGES
