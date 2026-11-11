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

from typing import TYPE_CHECKING

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Beatmaps.ControlPoints.ControlPointInfo import ControlPointInfo
from parsecore.Beatmaps.Legacy.LegacyHitObjectType import LegacyHitObjectType
from parsecore.Rulesets.Objects.Legacy.ConvertHitObject import ConvertHitObject
from parsecore.Rulesets.Objects.SliderPath import SliderPath
from parsecore.Rulesets.Objects.Types.IHasGenerateTicks import IHasGenerateTicks
from parsecore.Rulesets.Objects.Types.IHasPathWithRepeats import IHasPathWithRepeats
from parsecore.Rulesets.Objects.Types.IHasRepeats import SpanCount
from parsecore.Rulesets.Objects.Types.IHasSliderVelocity import IHasSliderVelocity

if TYPE_CHECKING:
    from parsecore.Audio.HitSampleInfo import HitSampleInfo

# The distance a slider covers per beat before the slider multiplier.
BASE_SCORING_DISTANCE = 100.0


class ConvertSlider(ConvertHitObject, IHasPathWithRepeats, IHasSliderVelocity, IHasGenerateTicks):
    """A path the player follows, possibly repeating."""

    def __init__(self) -> None:
        """Create a slider."""

        super().__init__()
        self.Path: SliderPath = SliderPath()
        self.RepeatCount: int = 0
        self.NodeSamples: list[list[HitSampleInfo]] = []
        self.SliderVelocityMultiplier: float = 1.0
        self.GenerateTicks: bool = True
        self.Velocity: float = 1.0
        self.LegacyType = LegacyHitObjectType.Slider

    def ApplyDefaultsToSelf(self, control_point_info: ControlPointInfo, difficulty: BeatmapDifficulty) -> None:
        """Read slider velocity and tick generation from the difficulty point.

        Legacy beatmaps carry both as control points rather than on the object.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        super().ApplyDefaultsToSelf(control_point_info, difficulty)

        timing_point = control_point_info.TimingPointAt(self.StartTime)
        scoring_distance = (
            BASE_SCORING_DISTANCE
            * difficulty.SliderMultiplier
            * self.SliderVelocityMultiplier
        )
        self.Velocity = scoring_distance / timing_point.BeatLength

    @property
    def Distance(self) -> float:
        """Return the length of one span of the slider."""
        return self.Path.Distance

    @property
    def Duration(self) -> float:
        """Return how long the slider takes to follow."""
        return SpanCount(self) * self.Distance / self.Velocity

    @property
    def EndTime(self) -> float:
        """Return when the slider is finished with."""
        return self.StartTime + self.Duration
