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

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Rulesets.Osu.Objects.OsuHitObject import OsuHitObject
from parsecore.Rulesets.Osu.Objects.SpinnerTick import SpinnerBonusTick, SpinnerTick
from parsecore.Utils.Vector2 import Vector2, f32

# Spins per minute needed, on average, to clear a spinner at OD 0, 5 and 10.
CLEAR_RPM_RANGE = (90.0, 150.0, 225.0)

# Spins per minute needed to earn every tick a spinner has, at the same odds.
COMPLETE_RPM_RANGE = (250.0, 380.0, 430.0)

# Spins between clearing a spinner and the first one that pays a bonus.
BONUS_SPINS_GAP = 2

# A tenth of a millisecond of slack in the duration, so a spinner that should
# come out even is not robbed of its last spin by a rounding error.
DURATION_ERROR = 0.0001


class Spinner(OsuHitObject):
    """An object spun for a duration."""

    def __init__(self, start_time: float = 0.0, end_time: float = 0.0, position=None) -> None:
        """Create a spinner.

        Args:
            start_time: The spinner's start in milliseconds.
            end_time: The spinner's end in milliseconds.
            position: The spinner's centre.
        """
        super().__init__(start_time, position)
        self.EndTime: float = end_time
        self.SpinsRequired: int = 1
        self.MaximumBonusSpins: int = 1

    @property
    def SpinsRequiredForBonus(self) -> int:
        """Return the spin from which a spinner starts paying a bonus."""
        return self.SpinsRequired + BONUS_SPINS_GAP

    @property
    def Duration(self) -> float:
        """Return how long the spinner lasts."""
        return self.EndTime - self.StartTime

    @property
    def StackOffset(self) -> Vector2:
        """Return no offset at all; a spinner is never moved by stacking.

        The pre-v6 stacking algorithm does raise a spinner's stack height, so
        without this a converted beatmap would drag its spinners off centre.
        """
        return Vector2()

    def ApplyDefaultsToSelf(self, control_point_info, difficulty) -> None:
        """Derive the required and bonus spin counts from the beatmap.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        super().ApplyDefaultsToSelf(control_point_info, difficulty)

        # The average rate needed over the spinner's length to clear it, and
        # the rate needed to earn every tick it has.
        minimum_rotations_per_second = (
            BeatmapDifficulty.DifficultyRange(
                difficulty.OverallDifficulty, *CLEAR_RPM_RANGE
            )
            / 60
        )
        maximum_rotations_per_second = (
            BeatmapDifficulty.DifficultyRange(
                difficulty.OverallDifficulty, *COMPLETE_RPM_RANGE
            )
            / 60
        )

        seconds_duration = self.Duration / 1000

        self.SpinsRequired = int(
            minimum_rotations_per_second * seconds_duration + DURATION_ERROR
        )
        self.MaximumBonusSpins = max(
            0,
            int(maximum_rotations_per_second * seconds_duration + DURATION_ERROR)
            - self.SpinsRequired
            - BONUS_SPINS_GAP,
        )

    def CreateHitWindows(self):
        """Return empty windows; the nested objects carry the real ones."""
        from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows

        return EmptyHitWindows()

    def CreateNestedHitObjects(self) -> None:
        """Generate one nested tick for every spin of this spinner."""
        total_spins = self.MaximumBonusSpins + self.SpinsRequired + BONUS_SPINS_GAP

        for i in range(total_spins):
            # The fraction of the way through is single precision, so the tick
            # times are not quite the even division they look like.
            start_time = self.StartTime + f32((i + 1) / total_spins) * self.Duration

            tick = (
                SpinnerTick(start_time)
                if i < self.SpinsRequiredForBonus
                else SpinnerBonusTick(start_time)
            )
            tick.SpinnerDuration = self.Duration
            self.AddNested(tick)
