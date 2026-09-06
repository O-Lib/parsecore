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

from collections import defaultdict

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Beatmaps.BeatmapInfo import BeatmapInfo
from parsecore.Beatmaps.BeatmapMetadata import BeatmapMetadata
from parsecore.Beatmaps.ControlPoints.ControlPointInfo import ControlPointInfo
from parsecore.Beatmaps.Timing.BreakPeriod import BreakPeriod
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Scoring.HitResult import AffectsCombo


class Beatmap:
    """A beatmap with its settings, control points, breaks and hit objects."""

    def __init__(self) -> None:
        """Create an empty beatmap with default settings."""
        self.BeatmapInfo: BeatmapInfo = BeatmapInfo()
        self.ControlPointInfo: ControlPointInfo = ControlPointInfo()
        self.Breaks: list[BreakPeriod] = []
        self.UnhandledEventLines: list[str] = []
        self.HitObjects: list[HitObject] = []

    @property
    def Metadata(self) -> BeatmapMetadata:
        """Return the beatmap's metadata."""
        return self.BeatmapInfo.Metadata

    @property
    def Difficulty(self) -> BeatmapDifficulty:
        """Return the beatmap's difficulty settings."""
        return self.BeatmapInfo.Difficulty

    @Difficulty.setter
    def Difficulty(self, value: BeatmapDifficulty) -> None:
        """Replace the beatmap's difficulty settings.

        Args:
            value: The new difficulty settings.
        """
        self.BeatmapInfo.Difficulty = value

    @property
    def TotalBreakTime(self) -> float:
        """Return the total time spent in breaks."""
        return sum(b.Duration for b in self.Breaks)

    def GetMaxCombo(self) -> int:
        """Return the highest combo achievable on this beatmap.

        Every object whose best judgement affects combo counts, including the
        nested objects a slider or spinner generates.
        """
        combo = 0

        def add_combo(hit_object) -> None:
            """Count an object and everything nested inside it."""
            nonlocal combo
            if AffectsCombo(hit_object.Judgement.MaxResult):
                combo += 1
            for nested in hit_object.NestedHitObjects:
                add_combo(nested)

        for hit_object in self.HitObjects:
            add_combo(hit_object)

        return combo

    def GetMostCommonBeatLength(self) -> float:
        """Return the beat length that the most playable time is spent at.

        Returns:
            The most common beat length, or ``0`` if the beatmap is empty.
        """
        timing_points = self.ControlPointInfo.TimingPoints
        if not timing_points:
            return 0.0

        if not self.HitObjects:
            return timing_points[0].BeatLength

        last_time = max(h.GetEndTime() for h in self.HitObjects)

        # Sum how long each beat length is in effect for, then take the longest.
        durations: dict[float, float] = defaultdict(float)
        for i, point in enumerate(timing_points):
            if point.Time > last_time:
                break
            start = max(point.Time, self.HitObjects[0].StartTime)
            end = (
                timing_points[i + 1].Time
                if i + 1 < len(timing_points)
                else last_time
            )
            durations[point.BeatLength] += max(0.0, end - start)

        if not durations:
            return timing_points[0].BeatLength

        # Ties go to the earlier beat length, matching osu!.
        best = max(durations.values())
        for point in timing_points:
            if durations.get(point.BeatLength, -1.0) == best:
                return point.BeatLength
        return timing_points[0].BeatLength

    def __repr__(self) -> str:
        """Return an unambiguous representation."""
        return f"Beatmap({self.BeatmapInfo!s}, {len(self.HitObjects)} objects)"
