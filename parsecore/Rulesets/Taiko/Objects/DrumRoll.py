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
from parsecore.Beatmaps.ControlPoints.ControlPointInfo import ControlPointInfo
from parsecore.Rulesets.Objects.SliderPath import SliderPath
from parsecore.Rulesets.Objects.Types.IHasPath import IHasPath
from parsecore.Rulesets.Objects.Types.PathType import LINEAR
from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows
from parsecore.Rulesets.Taiko.Objects.DrumRollTick import DrumRollTick
from parsecore.Rulesets.Taiko.Objects.StrongNestedHitObject import (
    StrongNestedHitObject,
)
from parsecore.Rulesets.Taiko.Objects.TaikoHitObject import TaikoHitObject
from parsecore.Rulesets.Taiko.Objects.TaikoStrongableHitObject import (
    TaikoStrongableHitObject,
)
from parsecore.Utils.Vector2 import Vector2

# The distance a roll covers per beat before any multipliers.
BASE_DISTANCE = 100.0


class DrumRoll(TaikoStrongableHitObject, IHasPath):
    """A roll, drummed along for its whole length."""

    def __init__(self) -> None:
        """Create a drum roll."""

        super().__init__()
        self.Duration: float = 0.0
        self.Velocity: float = 0.0
        self.TickRate: int = 1
        self._tick_spacing: float = 100.0

        self.Distance = self.Duration * self.Velocity
        self.Path = SliderPath.from_type(
            LINEAR,
            [Vector2(), Vector2(1, 1)]
        )

    @property
    def EndTime(self) -> float:
        """Return when the roll ends."""
        return self.StartTime + self.Duration

    @EndTime.setter
    def EndTime(self, value: float) -> None:
        self.Duration = value - self.StartTime

    def ApplyDefaultsToSelf(self, control_point_info: ControlPointInfo, difficulty: BeatmapDifficulty) -> None:
        """Derive the roll's velocity and tick spacing from the beatmap.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        super().ApplyDefaultsToSelf(control_point_info, difficulty)

        from parsecore.Rulesets.Taiko.Beatmaps.TaikoBeatmapConverter import (
            VELOCITY_MULTIPLIER,
        )

        timing_point = control_point_info.TimingPointAt(self.StartTime)
        effect_point = control_point_info.EffectPointAt(self.StartTime)

        scoring_distance = (
            BASE_DISTANCE
            * (difficulty.SliderMultiplier * VELOCITY_MULTIPLIER)
            * effect_point.ScrollSpeed
        )
        self.Velocity = scoring_distance / timing_point.BeatLength
        # Only a tick rate of exactly three is honoured; everything else rolls
        # at four ticks a beat.
        self.TickRate = 3 if difficulty.SliderTickRate == 3 else 4

        self._tick_spacing = timing_point.BeatLength / self.TickRate

    def CreateNestedHitObjects(self) -> None:
        """Add a tick for every beat subdivision the roll covers."""
        self._create_ticks()

        super().CreateNestedHitObjects()

    def CreateJudgement(self):
        """Return the judgement this object is scored with.

        Returns:
            The judgement instance used for scoring this object.
        """
        from parsecore.Rulesets.Judgements.IgnoreJudgement import IgnoreJudgement

        return IgnoreJudgement()

    def CreateHitWindows(self):
        """Return no windows; a roll is judged through its ticks.

        Returns:
            An empty hit windows instance.
        """
        return EmptyHitWindows()

    def CreateStrongNestedHit(self, start_time: float) -> StrongNestedHitObject:
        """Return the second hand's hit.

        Args:
            start_time: When the second hand lands.

        Returns:
            The nested strong hit object.
        """
        nested = _DrumRollStrongNestedHit(self)
        nested.StartTime = start_time
        nested.Samples = self.Samples
        return nested

    def _create_ticks(self) -> None:
        """Place ticks evenly across the roll."""
        if self._tick_spacing == 0:
            return

        first = True
        time = self.StartTime
        # The half-spacing slack lets a tick land on the roll's very end.
        while time < self.EndTime + self._tick_spacing / 2:
            tick = DrumRollTick(self)
            tick.FirstTick = first
            tick.TickSpacing = self._tick_spacing
            tick.StartTime = time
            tick.Samples = self.Samples
            tick.IsStrong = self.IsStrong
            self.AddNested(tick)

            first = False
            time += self._tick_spacing


class _DrumRollStrongNestedHit(StrongNestedHitObject):
    """The second hand of a strong drum roll, which scores nothing itself."""

    def __init__(self, parent: TaikoHitObject) -> None:
        """Create a strong nested hit for a drum roll.

        Args:
            parent: The parent drum roll object.
        """
        super().__init__(parent)

    def CreateJudgement(self):
        """Return the judgement this object is scored with.

        Returns:
            An ignore judgement instance.
        """
        from parsecore.Rulesets.Judgements.IgnoreJudgement import IgnoreJudgement

        # The strong hit of drum roll does not provide any score.
        return IgnoreJudgement()
