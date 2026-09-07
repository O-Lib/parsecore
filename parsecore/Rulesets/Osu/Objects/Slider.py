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

from parsecore.Rulesets.Objects import SliderEventGenerator
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    GetPrecisionAdjustedBeatLength,
)
from parsecore.Rulesets.Objects.PathControlPoint import PathControlPoint
from parsecore.Rulesets.Objects.SliderEventGenerator import SliderEventType
from parsecore.Rulesets.Objects.SliderPath import SliderPath
from parsecore.Rulesets.Osu.Objects.OsuHitObject import (
    BASE_SCORING_DISTANCE,
    OsuHitObject,
)
from parsecore.Rulesets.Osu.Objects.SliderHeadCircle import SliderHeadCircle
from parsecore.Rulesets.Osu.Objects.SliderRepeat import SliderRepeat
from parsecore.Rulesets.Osu.Objects.SliderTailCircle import SliderTailCircle
from parsecore.Rulesets.Osu.Objects.SliderTick import SliderTick
from parsecore.Utils.Vector2 import Vector2


class Slider(OsuHitObject):
    """A curve the player traces, optionally repeating."""

    def __init__(self, start_time: float = 0.0, position: Vector2 | None = None) -> None:
        """Create a slider.

        Args:
            start_time: The slider's time in milliseconds.
            position: The slider head's position.
        """
        super().__init__(start_time, position)

        # osu! keeps one path instance with catmull optimisation enabled and
        # copies incoming control points into it.
        self._path = SliderPath()
        self._path.OptimiseCatmull = True
        self.RepeatCount: int = 0
        self.NodeSamples: list[list] = []

        self.Velocity: float = 1.0
        self.TickDistance: float = 0.0
        self.TickDistanceMultiplier: float = 1.0
        self.GenerateTicks: bool = True
        self.SliderVelocityMultiplier: float = 1.0

        self.HeadCircle: SliderHeadCircle | None = None
        self.TailCircle: SliderTailCircle | None = None

    @property
    def Path(self) -> SliderPath:
        """Return the slider's path."""
        return self._path

    @Path.setter
    def Path(self, value: SliderPath) -> None:
        """Copy another path's control points and length into this one.

        Args:
            value: The path to copy from.
        """
        self._path.ControlPoints = [
            PathControlPoint(cp.Position, cp.Type) for cp in value.ControlPoints
        ]
        self._path.ExpectedDistance = value.ExpectedDistance
        self._path.invalidate()

        # osu! watches the path's version and moves the nested objects with it.
        self._update_nested_positions()

    @property
    def Position(self) -> Vector2:
        """Return the slider head's position."""
        return self._position

    @Position.setter
    def Position(self, value: Vector2) -> None:
        """Move the slider, taking its nested objects along.

        Args:
            value: The new head position.
        """
        self._position = value
        self._update_nested_positions()

    def _update_nested_positions(self) -> None:
        """Place every nested object again from the current path."""
        for nested in self.NestedHitObjects:
            if isinstance(nested, SliderHeadCircle):
                nested.Position = self.Position
            elif isinstance(nested, SliderTailCircle):
                nested.Position = self.EndPosition
            elif isinstance(nested, (SliderRepeat, SliderTick)):
                nested.Position = self.Position + self.Path.PositionAt(
                    nested.PathProgress
                )

    @property
    def SpanCount(self) -> int:
        """Return how many times the path is traversed."""
        return self.RepeatCount + 1

    @property
    def Distance(self) -> float:
        """Return the length of one span of the path."""
        return self.Path.Distance

    @property
    def EndTime(self) -> float:
        """Return when the slider ends."""
        if self.Velocity == 0:
            return self.StartTime
        return self.StartTime + self.SpanCount * self.Path.Distance / self.Velocity

    @property
    def Duration(self) -> float:
        """Return how long the slider lasts.

        Derived by subtracting the start time from the end time, as osu! does.
        Computing the span directly would keep a little more precision than the
        game does, and slider timing feeds the difficulty calculation.
        """
        return self.EndTime - self.StartTime

    @property
    def SpanDuration(self) -> float:
        """Return how long one traversal of the path takes."""
        return self.Duration / self.SpanCount

    def ProgressAt(self, progress: float) -> float:
        """Return the path progress at a fraction of the slider's duration.

        Args:
            progress: The fraction of the slider elapsed, ``0`` to ``1``.
        """
        p = (progress * self.SpanCount) % 1
        if self.SpanAt(progress) % 2 == 1:
            p = 1 - p
        return p

    def SpanAt(self, progress: float) -> int:
        """Return which span is being traversed at a fraction of the duration.

        Args:
            progress: The fraction of the slider elapsed, ``0`` to ``1``.
        """
        return int(progress * self.SpanCount)

    def CurvePositionAt(self, progress: float) -> Vector2:
        """Return the offset from the slider head at a fraction of the duration.

        Args:
            progress: The fraction of the slider elapsed, ``0`` to ``1``.
        """
        return self.Path.PositionAt(self.ProgressAt(progress))

    @property
    def EndPosition(self) -> Vector2:
        """Return where the slider's path finishes."""
        return self.Position + self.CurvePositionAt(1.0)

    def PositionAt(self, progress: float) -> Vector2:
        """Return the absolute position at a fraction of the duration.

        Args:
            progress: The fraction of the slider elapsed, ``0`` to ``1``.
        """
        return self.Position + self.CurvePositionAt(progress)

    def StackedPositionAt(self, progress: float) -> Vector2:
        """Return the stacked position at a fraction of the duration.

        Args:
            progress: The fraction of the slider elapsed, ``0`` to ``1``.
        """
        return self.StackedPosition + self.CurvePositionAt(progress)

    def ApplyDefaultsToSelf(self, control_point_info, difficulty) -> None:
        """Derive velocity and tick spacing from the beatmap.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        super().ApplyDefaultsToSelf(control_point_info, difficulty)

        timing_point = control_point_info.TimingPointAt(self.StartTime)

        self.Velocity = (
            BASE_SCORING_DISTANCE
            * difficulty.SliderMultiplier
            / GetPrecisionAdjustedBeatLength(self, timing_point, "osu")
        )

        scoring_distance = self.Velocity * timing_point.BeatLength

        self.TickDistance = (
            scoring_distance / difficulty.SliderTickRate * self.TickDistanceMultiplier
            if self.GenerateTicks
            else math.inf
        )

    def CreateJudgement(self):
        """Return the judgement this object is scored with.

        Under lazer slider behaviour the final combo comes from the tail
        circle, so the slider itself is never judged.
        """
        from parsecore.Rulesets.Osu.Judgements.OsuJudgement import OsuIgnoreJudgement

        return OsuIgnoreJudgement()

    def CreateHitWindows(self):
        """Return empty windows; the nested objects carry the real ones."""
        from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows

        return EmptyHitWindows()

    def CreateNestedHitObjects(self) -> None:
        """Generate the head, ticks, repeats and tail of this slider."""
        events = SliderEventGenerator.Generate(
            self.StartTime,
            self.SpanDuration,
            self.Velocity,
            self.TickDistance,
            self.Path.Distance,
            self.SpanCount,
        )

        for event in events:
            match event.Type:
                case SliderEventType.Tick:
                    tick = SliderTick(
                        event.Time,
                        self.Position + self.Path.PositionAt(event.PathProgress),
                    )
                    tick.SpanIndex = event.SpanIndex
                    tick.SpanStartTime = event.SpanStartTime
                    tick.PathProgress = event.PathProgress
                    tick.StackHeight = self.StackHeight
                    tick.Scale = self.Scale
                    self.AddNested(tick)

                case SliderEventType.Head:
                    self.HeadCircle = SliderHeadCircle(event.Time, self.Position)
                    self.HeadCircle.StackHeight = self.StackHeight
                    self.AddNested(self.HeadCircle)

                case SliderEventType.Repeat:
                    repeat = SliderRepeat(
                        self,
                        self.StartTime + (event.SpanIndex + 1) * self.SpanDuration,
                        self.Position + self.Path.PositionAt(event.PathProgress),
                    )
                    repeat.SpanIndex = event.SpanIndex
                    repeat.SpanStartTime = event.SpanStartTime
                    repeat.PathProgress = event.PathProgress
                    repeat.StackHeight = self.StackHeight
                    repeat.Scale = self.Scale
                    self.AddNested(repeat)

                case SliderEventType.Tail:
                    self.TailCircle = SliderTailCircle(
                        self, event.Time, self.EndPosition
                    )
                    self.TailCircle.SpanIndex = event.SpanIndex
                    self.TailCircle.SpanStartTime = event.SpanStartTime
                    self.TailCircle.StackHeight = self.StackHeight
                    self.AddNested(self.TailCircle)
