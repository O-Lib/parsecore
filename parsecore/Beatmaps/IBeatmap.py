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

from typing import Protocol, runtime_checkable

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Beatmaps.BeatmapInfo import BeatmapInfo as BInfo
from parsecore.Beatmaps.BeatmapMetadata import BeatmapMetadata
from parsecore.Beatmaps.ControlPoints.ControlPointInfo import ControlPointInfo
from parsecore.Beatmaps.Timing.BreakPeriod import BreakPeriod
from parsecore.Rulesets.Objects.HitObject import HitObject


@runtime_checkable
class IBeatmap(Protocol):
    """A parsed beatmap: its attributes, control points and hit objects."""

    ControlPointInfo: ControlPointInfo
    Breaks: list[BreakPeriod]
    HitObjects: list[HitObject]
    UnhandledEventLines: list[str]

    @property
    def BeatmapInfo(self) -> BInfo:
        """The beatmap's general information."""
        ...

    @property
    def Metadata(self) -> BeatmapMetadata:
        """The beatmap's metadata."""
        ...

    @property
    def Difficulty(self) -> BeatmapDifficulty:
        """The beatmap's difficulty attributes."""
        ...

    @property
    def TotalBreakTime(self) -> float:
        """Total amount of break time in the beatmap."""
        ...

    def GetMostCommonBeatLength(self) -> float:
        """Return the beat length most of the beatmap is played at."""
        ...
