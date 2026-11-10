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

from parsecore.Beatmaps.Beatmap import Beatmap
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Mania.Beatmaps.ManiaBeatmapConverter import (
    GetColumnCount,
    ManiaBeatmapConverter,
)
from parsecore.Rulesets.Mania.Mods.ManiaModDaycore import ManiaModDaycore
from parsecore.Rulesets.Mania.Mods.ManiaModEasy import ManiaModEasy
from parsecore.Rulesets.Mania.Mods.ManiaModHalfTime import ManiaModHalfTime
from parsecore.Rulesets.Mania.Mods.ManiaModNoFail import ManiaModNoFail
from parsecore.Rulesets.Mods.Mod import Mod
from parsecore.Rulesets.Mods.ModScoreV2 import ModScoreV2
from parsecore.Rulesets.Scoring.Legacy.ILegacyScoreSimulator import (
    ILegacyScoreSimulator,
)
from parsecore.Rulesets.Scoring.Legacy.LegacyBeatmapConversionDifficultyInfo import (
    LegacyBeatmapConversionDifficultyInfo,
)
from parsecore.Rulesets.Scoring.Legacy.LegacyScoreAttributes import (
    LegacyScoreAttributes,
)

MANIA_RULESET_ID = 3

# What every mania beatmap was worth before the mods were applied.
TOTAL_SCORE = 1000000

# What the mods multiply an osu!stable score by, and what they multiply it by
# once the second scoring version is in play.
MOD_MULTIPLIERS = {
    "NF": (0.5, 1.0),
    "EZ": (0.5, 0.5),
    "HT": (0.5, 0.5),
    "DC": (0.5, 0.5),
}


class ManiaLegacyScoreSimulator(ILegacyScoreSimulator):
    """Simulates a perfect mania play under osu!stable's first scoring system."""

    def Simulate(self, workingBeatmap: WorkingBeatmap, playable_beatmap: Beatmap) -> LegacyScoreAttributes:
        """Return the highest osu!stable score a beatmap allows.

        Args:
            workingBeatmap: The beatmap as it was decoded.
            playable_beatmap: The same beatmap as mania plays it.
        """
        return LegacyScoreAttributes(
            ComboScore=TOTAL_SCORE,
            # The maximum combo depends on the mods, so no value here would do.
            MaxCombo=0,
        )

    @staticmethod
    def _GetLegacyScoreMultiplier(mods: list[Mod], difficulty: LegacyBeatmapConversionDifficultyInfo) -> float:
        """Return what the mods multiply an osu!stable score by.

        Args:
            mods: The mods the score was set with.
        """
        score_v2 = any(m for m in mods if isinstance(m, ModScoreV2))
        multiplier = 1.0

        for mod in mods:
            if isinstance(mod, ManiaModNoFail):
                multiplier *= 1.0 if score_v2 else 0.5

            elif isinstance(mod, (ManiaModHalfTime, ManiaModDaycore, ManiaModEasy)):
                multiplier *= 0.5

        original_columns = GetColumnCount(difficulty)
        actual_columns = GetColumnCount(difficulty, mods)

        if actual_columns > original_columns:
            multiplier *= 0.9
        elif actual_columns < original_columns:
            multiplier *= 0.9 - 0.04 * (original_columns - actual_columns)

        return multiplier
