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

from dataclasses import dataclass, field

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Beatmaps.BeatmapMetadata import BeatmapMetadata
from parsecore.Beatmaps.CountdownType import CountdownType


@dataclass(slots=True)
class BeatmapInfo:
    """The settings of a single difficulty, as read from ``[General]`` and friends."""

    Metadata: BeatmapMetadata = field(default_factory=BeatmapMetadata)
    Difficulty: BeatmapDifficulty = field(default_factory=BeatmapDifficulty)

    DifficultyName: str = ""
    RulesetID: int = 0
    OnlineID: int = -1
    BeatmapSetID: int = -1
    # The ``osu file format v..`` the beatmap was decoded from; several
    # conversion quirks are gated on it.
    BeatmapVersion: int = 14

    StarRating: float = 0.0
    Length: float = 0.0
    BPM: float = 0.0

    AudioLeadIn: float = 0.0
    StackLeniency: float = 0.7
    SpecialStyle: bool = False
    LetterboxInBreaks: bool = False
    WidescreenStoryboard: bool = False
    EpilepsyWarning: bool = False
    SamplesMatchPlaybackRate: bool = False
    Countdown: CountdownType = CountdownType.None_
    CountdownOffset: int = 0

    # Editor settings.
    Bookmarks: list[int] = field(default_factory=list)
    SliderVelocityPresets: list[float] = field(
        default_factory=lambda: [0.75, 1.0, 1.5]
    )
    DistanceSpacing: float = 1.0
    BeatDivisor: int = 4
    GridSize: int = 0
    TimelineZoom: float = 1.0

    def __str__(self) -> str:
        """Return ``artist - title [difficulty]`` for display."""
        return f"{self.Metadata} [{self.DifficultyName}]".strip()
