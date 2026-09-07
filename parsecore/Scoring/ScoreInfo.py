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
from parsecore.Rulesets.Scoring.HitResult import HitResult


@dataclass(slots=True)
class ScoreInfo:
    """What the player achieved on a beatmap."""

    Accuracy: float = 1.0
    MaxCombo: int = 0
    RulesetID: int = 0
    TotalScore: int = 0
    # The total an osu!stable score recorded. A score set on osu!lazer has
    # none, and its absence is what tells the two apart.
    LegacyTotalScore: int | None = None
    Mods: list = field(default_factory=list)
    BeatmapDifficulty: BeatmapDifficulty = field(default_factory=BeatmapDifficulty)
    Statistics: dict[HitResult, int] = field(default_factory=dict)
    MaximumStatistics: dict[HitResult, int] = field(default_factory=dict)

    def GetCount(self, result: HitResult) -> int:
        """Return how many times a judgement was earned.

        Args:
            result: The judgement to count.
        """
        return self.Statistics.get(result, 0)
