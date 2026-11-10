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
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle

if TYPE_CHECKING:
    from parsecore.Rulesets.Osu.Objects.Slider import Slider


class SliderEndCircle(HitCircle):
    """A circle marking the end of one span of a slider."""

    def __init__(self, slider: Slider) -> None:
        """Create a slider end circle.

        Args:
            slider: The slider this circle belongs to.
        """
        super().__init__()
        self.Slider = slider
        self.RepeatIndex: int = 0

    @property
    def SpanDuration(self) -> float:
        """Return the duration of a single span of the slider."""
        return self.Slider.SpanDuration

    def ApplyDefaultsToSelf(self, control_point_info: ControlPointInfo, difficulty: BeatmapDifficulty) -> None:
        """Give the circle the preempt time of its span.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        super().ApplyDefaultsToSelf(control_point_info, difficulty)

        if self.RepeatIndex > 0:
            self.TimeFadeIn = 0.0
            self.TimePreempt = self.SpanDuration * 2
        else:
            self.TimePreempt += self.StartTime - self.Slider.StartTime

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Osu.Judgements.OsuJudgement import SliderEndJudgement

        return SliderEndJudgement()

    def CreateHitWindows(self):
        """Return empty hit windows as slider end circles use custom timing."""
        from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows
        return EmptyHitWindows()
