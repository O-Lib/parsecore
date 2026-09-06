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

from parsecore.Rulesets.Scoring.Legacy.ILegacyScoreSimulator import (
    ILegacyScoreSimulator,
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

    def Simulate(self, beatmap, playable_beatmap) -> LegacyScoreAttributes:
        """Return the highest osu!stable score a beatmap allows.

        Args:
            beatmap: The beatmap as it was decoded.
            playable_beatmap: The same beatmap as mania plays it.
        """
        return LegacyScoreAttributes(
            ComboScore=TOTAL_SCORE,
            # The maximum combo depends on the mods, so no value here would do.
            MaxCombo=0,
        )

    def GetLegacyScoreMultiplier(self, mods: list, difficulty) -> float:
        """Return what the mods multiply an osu!stable score by.

        Args:
            mods: The mods the score was set with.
            difficulty: The settings the beatmap was converted against, which
                decide how many columns it would otherwise have had.
        """
        acronyms = [getattr(mod, "Acronym", None) for mod in mods]
        score_v2 = "SV2" in acronyms

        multiplier = 1.0

        for acronym in acronyms:
            pair = MOD_MULTIPLIERS.get(acronym)
            if pair is not None:
                multiplier *= pair[1] if score_v2 else pair[0]

        # A beatmap written for mania has no key mods to account for.
        if difficulty.SourceRulesetID == MANIA_RULESET_ID:
            return multiplier

        from parsecore.Rulesets.Mania.Beatmaps.ManiaBeatmapConverter import (
            GetColumnCount,
        )

        original_columns = GetColumnCount(difficulty)
        actual_columns = GetColumnCount(difficulty, mods)

        if actual_columns > original_columns:
            multiplier *= 0.9
        elif actual_columns < original_columns:
            multiplier *= 0.9 - 0.04 * (original_columns - actual_columns)

        return multiplier
