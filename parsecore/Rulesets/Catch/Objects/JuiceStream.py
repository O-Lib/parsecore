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

from parsecore.Audio.HitSampleInfo import HitSampleInfo
from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Beatmaps.ControlPoints.ControlPointInfo import ControlPointInfo
from parsecore.Rulesets.Catch.Objects.CatchHitObject import CatchHitObject
from parsecore.Rulesets.Catch.Objects.Droplet import Droplet, TinyDroplet
from parsecore.Rulesets.Catch.Objects.Fruit import Fruit
from parsecore.Rulesets.Objects import SliderEventGenerator
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    GetPrecisionAdjustedBeatLength,
)
from parsecore.Rulesets.Objects.PathControlPoint import PathControlPoint
from parsecore.Rulesets.Objects.SliderEventGenerator import SliderEventType
from parsecore.Rulesets.Objects.SliderPath import SliderPath
from parsecore.Rulesets.Objects.Types.IHasPathWithRepeats import IHasPathWithRepeats
from parsecore.Rulesets.Objects.Types.IHasRepeats import (
    GetNodeSamples,
    PopulateNodeSamples,
    SpanCount,
)
from parsecore.Rulesets.Objects.Types.IHasSliderVelocity import IHasSliderVelocity
from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows
from parsecore.Utils.Precision import Clamp

# The distance a stream covers per beat before the slider multiplier.
BASE_SCORING_DISTANCE = 100.0

# A gap longer than this is filled with tiny droplets.
TINY_DROPLET_THRESHOLD = 80.0

# How far apart those tiny droplets may sit.
MAX_TINY_DROPLET_SPACING = 100.0


class JuiceStream(CatchHitObject, IHasPathWithRepeats, IHasSliderVelocity):
    """A slider's path, dropping fruit and droplets along its length."""

    def __init__(self) -> None:
        """Create a juice stream."""
        super().__init__()
        self._path: SliderPath = SliderPath()
        self.RepeatCount: int = 0
        self.NodeSamples: list[list[HitSampleInfo]] = []

        self.Velocity: float = 0.0
        self.TickDistance: float = 0.0
        self.TickDistanceMultiplier: float = 1.0
        self.sliderVelocityMultiplier: float = 1.0

    @property
    def SliderVelocityMultiplier(self) -> float:
        """Return the slider velocity multiplier for this stream."""
        return self.sliderVelocityMultiplier
    
    @SliderVelocityMultiplier.setter
    def SliderVelocityMultiplier(self, value: float) -> None:
        self.sliderVelocityMultiplier = Clamp(value, 0.1, 10.0)

    @property
    def Path(self) -> SliderPath:
        """Return the path the stream traces."""
        return self._path

    @Path.setter
    def Path(self, value: SliderPath) -> None:
        """Copy another path's control points and length into this one.

        Args:
            value: The path to copy from.
        """
        self._path.ControlPoints.clear()
        self._path.ControlPoints = [
            PathControlPoint(cp.Position, cp.Type) for cp in value.ControlPoints
        ]
        self._path.ExpectedDistance = value.ExpectedDistance
        self._path.invalidate()

    @property
    def SpanCount(self) -> int:
        """Return how many times the path is traversed."""
        return self.RepeatCount + 1

    @property
    def Distance(self) -> float:
        """Return the length of one span of the path."""
        return self.Path.Distance

    @property
    def Duration(self) -> float:
        """Return how long the stream lasts."""
        return SpanCount(self) * self.Path.Distance / self.Velocity

    @property
    def SpanDuration(self) -> float:
        """Return how long one traversal of the path takes."""
        return self.Duration / SpanCount(self)

    @property
    def EndTime(self) -> float:
        """Return when the stream ends."""
        return self.StartTime + self.Duration

    @property
    def EndX(self) -> float:
        """Return where the stream finishes across the playfield."""
        return self.EffectiveX + self.CurvePositionAt(1).X

    def ApplyDefaultsToSelf(self, control_point_info: ControlPointInfo, difficulty: BeatmapDifficulty) -> None:
        """Derive the stream's velocity and tick spacing from the beatmap.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        super().ApplyDefaultsToSelf(control_point_info, difficulty)

        timing_point = control_point_info.TimingPointAt(self.StartTime)

        self.Velocity = (
            BASE_SCORING_DISTANCE
            * difficulty.SliderMultiplier
            / GetPrecisionAdjustedBeatLength(self, timing_point, "fruits")
        )
        # osu! rounds this trip through the beat length rather than keeping the
        # velocity it just computed, and the tick spacing follows.
        scoring_distance = self.Velocity * timing_point.BeatLength

        self.TickDistance = (
            scoring_distance / difficulty.SliderTickRate * self.TickDistanceMultiplier
        )

    def CreateNestedHitObjects(self) -> None:
        """Drop the fruit and droplets the stream is made of."""
        super().CreateNestedHitObjects()
        PopulateNodeSamples(self)

        droplet_samples = [s.With(Name="slidertick") for s in self.Samples]

        node_index = 0
        last_event: SliderEventGenerator.SliderEventDescriptor | None = None

        for event in SliderEventGenerator.Generate(
            self.StartTime,
            self.SpanDuration,
            self.Velocity,
            self.TickDistance,
            self.Path.Distance,
            SpanCount(self),
        ):
            if last_event is not None:
                # osu! measures this gap in whole milliseconds.
                since_last_tick = int(event.Time) - int(last_event.Time)

                if since_last_tick > TINY_DROPLET_THRESHOLD:
                    time_between_tiny = since_last_tick
                    while time_between_tiny > 100:
                        time_between_tiny /= 2

                    t = time_between_tiny
                    while t < since_last_tick:
                        tiny_droplet = TinyDroplet()
                        tiny_droplet.StartTime = t + last_event.Time
                        tiny_droplet.X = self.EffectiveX + self.Path.PositionAt(
                            last_event.PathProgress + (t / since_last_tick)
                            * (event.PathProgress - last_event.PathProgress)
                        ).X
                        self.AddNested(tiny_droplet)
                        t += time_between_tiny

            last_event = event

            if event.Type == SliderEventType.Tick:
                droplet = Droplet()
                droplet.StartTime = event.Time
                droplet.X = self.EffectiveX + self.Path.PositionAt(event.PathProgress).X
                droplet.Samples = droplet_samples
                self.AddNested(droplet)
            elif event.Type in (
                SliderEventType.Head,
                SliderEventType.Tail,
                SliderEventType.Repeat,
            ):
                fruit = Fruit()
                fruit.StartTime = event.Time
                fruit.X = self.EffectiveX + self.Path.PositionAt(event.PathProgress).X
                fruit.Samples = GetNodeSamples(self, node_index)
                node_index += 1
                self.AddNested(fruit)

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Catch.Judgements.CatchJudgement import (
            CatchIgnoreJudgement,
        )

        return CatchIgnoreJudgement()

    def CreateHitWindows(self):
        """Return no windows; a stream is judged through what it drops."""
        return EmptyHitWindows()
