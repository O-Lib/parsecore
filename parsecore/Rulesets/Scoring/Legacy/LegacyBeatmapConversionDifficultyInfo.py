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

from dataclasses import dataclass

from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration


@dataclass
class LegacyBeatmapConversionDifficultyInfo:
    """What a beatmap looked like before it was converted."""

    SourceRulesetID: int = 0
    DrainRate: float = 0.0
    ApproachRate: float = 0.0
    CircleSize: float = 0.0
    OverallDifficulty: float = 0.0
    EndTimeObjectCount: int = 0
    TotalObjectCount: int = 0

    @staticmethod
    def FromBeatmap(beatmap) -> LegacyBeatmapConversionDifficultyInfo:
        """Return the settings of a decoded beatmap.

        Args:
            beatmap: The beatmap to read.
        """
        difficulty = beatmap.Difficulty

        return LegacyBeatmapConversionDifficultyInfo(
            SourceRulesetID=beatmap.BeatmapInfo.RulesetID,
            DrainRate=difficulty.DrainRate,
            ApproachRate=difficulty.ApproachRate,
            CircleSize=difficulty.CircleSize,
            OverallDifficulty=difficulty.OverallDifficulty,
            EndTimeObjectCount=sum(
                1 for h in beatmap.HitObjects if isinstance(h, IHasDuration)
            ),
            TotalObjectCount=len(beatmap.HitObjects),
        )
