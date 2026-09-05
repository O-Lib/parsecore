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

from parsecore.Rulesets.Osu.Objects.OsuHitObject import OsuHitObject


class SliderEndCircle(OsuHitObject):
    """A circle marking the end of one span of a slider."""

    def __init__(self, slider=None, start_time: float = 0.0, position=None) -> None:
        """Create a slider end circle.

        Args:
            slider: The slider this circle belongs to.
            start_time: The circle's time in milliseconds.
            position: The circle's position.
        """
        super().__init__(start_time, position)
        self.Slider = slider
        self.SpanIndex: int = 0
        self.SpanStartTime: float = 0.0

    def ApplyDefaultsToSelf(self, control_point_info, difficulty) -> None:
        """Give the circle the preempt time of its span.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        super().ApplyDefaultsToSelf(control_point_info, difficulty)

        if self.SpanIndex > 0:
            self.TimePreempt = self.StartTime - self.SpanStartTime + 200.0

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Osu.Judgements.OsuJudgement import SliderEndJudgement

        return SliderEndJudgement()
