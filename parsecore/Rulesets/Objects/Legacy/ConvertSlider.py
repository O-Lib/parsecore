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

from parsecore.Rulesets.Objects.Legacy.ConvertHitObject import ConvertHitObject
from parsecore.Rulesets.Objects.SliderPath import SliderPath
from parsecore.Utils.Vector2 import Vector2

# The distance a slider covers per beat before the slider multiplier.
BASE_SCORING_DISTANCE = 100.0


class ConvertSlider(ConvertHitObject):
    """A path the player follows, possibly repeating."""

    def __init__(self, start_time: float = 0.0, position: Vector2 | None = None) -> None:
        """Create a slider.

        Args:
            start_time: The object's time in milliseconds.
            position: The slider head's position.
        """
        super().__init__(start_time)
        self.Position: Vector2 = position or Vector2()
        self.Path: SliderPath = SliderPath()
        self.RepeatCount: int = 0
        self.NodeSamples: list[list] = []
        self.SliderVelocityMultiplier: float = 1.0
        self.GenerateTicks: bool = True
        self.Velocity: float = 1.0

    def ApplyDefaultsToSelf(self, control_point_info, difficulty) -> None:
        """Read slider velocity and tick generation from the difficulty point.

        Legacy beatmaps carry both as control points rather than on the object.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        super().ApplyDefaultsToSelf(control_point_info, difficulty)

        difficulty_point_at = getattr(control_point_info, "DifficultyPointAt", None)
        if difficulty_point_at is None:
            return

        point = difficulty_point_at(self.StartTime)
        self.SliderVelocityMultiplier = point.SliderVelocity
        self.GenerateTicks = point.GenerateTicks

        timing_point = control_point_info.TimingPointAt(self.StartTime)
        scoring_distance = (
            BASE_SCORING_DISTANCE
            * difficulty.SliderMultiplier
            * self.SliderVelocityMultiplier
        )
        self.Velocity = scoring_distance / timing_point.BeatLength

    @property
    def X(self) -> float:
        """Return the slider head's x position."""
        return self.Position.X

    @property
    def Y(self) -> float:
        """Return the slider head's y position."""
        return self.Position.Y

    @property
    def Distance(self) -> float:
        """Return the length of one span of the slider."""
        return self.Path.Distance

    @property
    def SpanCount(self) -> int:
        """Return how many times the slider is traversed."""
        return self.RepeatCount + 1

    @property
    def Duration(self) -> float:
        """Return how long the slider takes to follow."""
        return self.SpanCount * self.Distance / self.Velocity

    @property
    def EndTime(self) -> float:
        """Return when the slider is finished with."""
        return self.StartTime + self.Duration
