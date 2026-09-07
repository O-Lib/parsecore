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

# Slider ticks appear at a fraction of a normal object's preempt time.
ANIM_DURATION = 150.0


class SliderTick(OsuHitObject):
    """A point along a slider the player must pass through."""

    def __init__(self, start_time: float = 0.0, position=None) -> None:
        """Create a slider tick.

        Args:
            start_time: The tick's time in milliseconds.
            position: The tick's position along the path.
        """
        super().__init__(start_time, position)
        self.SpanIndex: int = 0
        self.SpanStartTime: float = 0.0
        # Kept so the tick can be placed again if the slider's path moves.
        self.PathProgress: float = 0.0

    def ApplyDefaultsToSelf(self, control_point_info, difficulty) -> None:
        """Give the tick a shortened preempt time.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        super().ApplyDefaultsToSelf(control_point_info, difficulty)

        if self.SpanIndex > 0:
            # The offset osu!stable used, so ticks on repeats do not appear
            # too late for the player to process them.
            offset = 200.0
        else:
            offset = self.TimePreempt * 0.66

        self.TimePreempt = (self.StartTime - self.SpanStartTime) / 2 + offset

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Osu.Judgements.OsuJudgement import SliderTickJudgement

        return SliderTickJudgement()

    def CreateHitWindows(self):
        """Return empty windows; a tick is not judged on timing."""
        from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows

        return EmptyHitWindows()
