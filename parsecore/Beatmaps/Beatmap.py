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
from parsecore.Beatmaps.BeatmapInfo import BeatmapInfo as BInfo
from parsecore.Beatmaps.BeatmapMetadata import BeatmapMetadata
from parsecore.Beatmaps.ControlPoints.ControlPointInfo import ControlPointInfo
from parsecore.Beatmaps.ControlPoints.TimingControlPoint import DEFAULT_BEAT_LENGTH
from parsecore.Beatmaps.IBeatmap import IBeatmap
from parsecore.Beatmaps.Timing.BreakPeriod import BreakPeriod
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Scoring.HitResult import AffectsCombo
from parsecore.Utils.Precision import Clamp


class Beatmap(IBeatmap):
    """A beatmap with its attributes, control points, breaks and hit objects."""

    def __init__(self) -> None:
        """Create an empty beatmap with default attributes."""
        self._difficulty: BeatmapDifficulty = BeatmapDifficulty()
        self._beatmap_info: BeatmapInfo = BeatmapInfo(
            Metadata=BeatmapMetadata(
                Artist="Unknown",
                Title="Unknown",
                Author="Unknown Creator"
            ),
            DifficultyName="Normal",
            Difficulty=self.Difficulty
        )

        self.ControlPointInfo: ControlPointInfo = ControlPointInfo()
        self.Breaks: list[BreakPeriod] = []
        self.HitObjects: list[HitObject] = []
        self.UnhandledEventLines: list[str] = []

    @property
    def BeatmapInfo(self) -> BInfo:
        """Return basic information about the beatmap."""
        return self._beatmap_info

    @BeatmapInfo.setter
    def BeatmapInfo(self, value: BInfo):
        """Replace the beatmap info and sync its difficulty settings.

        Args:
            value: The new beatmap info.
        """
        self._beatmap_info = value
        self.Difficulty = self._beatmap_info.Difficulty.Clone()

    @property
    def Metadata(self) -> BeatmapMetadata:
        """Return the beatmap's metadata."""
        return self.BeatmapInfo.Metadata

    @property
    def Difficulty(self) -> BeatmapDifficulty:
        """Return the beatmap's difficulty settings."""
        return self._difficulty

    @Difficulty.setter
    def Difficulty(self, value: BeatmapDifficulty) -> None:
        """Replace the beatmap's difficulty settings.

        Args:
            value: The new difficulty settings.
        """
        self._difficulty = value
        self.BeatmapInfo.Difficulty = self._difficulty.Clone()

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

        def add_combo(hit_object: HitObject) -> None:
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
        last_time: float
        timing_points = self.ControlPointInfo.TimingPoints
        if not timing_points:
            return 0.0

        if not self.HitObjects:
            last_time = timing_points[-1].Time
        else:
            last_time = max(h.GetEndTime() for h in self.HitObjects)

        # Sum how long each beat length is in effect for, then take the longest.
        durations: dict[float, float] = defaultdict(float)
        for i, point in enumerate(timing_points):
            if point.Time > last_time:
                duration = 0.0
            else:
                current_time = 0.0 if i == 0 else point.Time
                next_time = last_time if i == len(timing_points) else timing_points[i + 1].Time
                duration = next_time - current_time

            beat_length = round(point.BeatLength, 3)
            durations[beat_length] += duration

        if not durations:
            return DEFAULT_BEAT_LENGTH

        most_common_beat_length = max(durations, key=lambda k: durations[k])
        if most_common_beat_length == 0.0:
            return DEFAULT_BEAT_LENGTH

        min_beat_length = min(point.BeatLength for point in timing_points)
        max_beat_length = max(point.BeatLength for point in timing_points)
        return Clamp(most_common_beat_length, min_beat_length, max_beat_length)

    def __repr__(self) -> str:
        """Return an unambiguous representation."""
        return f"Beatmap({self.BeatmapInfo!s}, {len(self.HitObjects)} objects)"
