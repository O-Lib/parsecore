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

from parsecore.Rulesets.Difficulty.PerformanceCalculator import PerformanceCalculator
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Mania.Difficulty.ManiaPerformanceAttributes import (
    ManiaPerformanceAttributes,
)
from parsecore.Rulesets.Scoring.HitResult import HitResult

# What each judgement is worth when weighing a score's accuracy.
JUDGEMENT_VALUES = {
    HitResult.Perfect: 320,
    HitResult.Great: 300,
    HitResult.Good: 200,
    HitResult.Ok: 100,
    HitResult.Meh: 50,
}


class ManiaPerformanceCalculator(PerformanceCalculator):
    """Calculates what a mania score is worth."""

    def __init__(self) -> None:
        """Create the calculator."""
        self._count_perfect = 0
        self._count_great = 0
        self._count_good = 0
        self._count_ok = 0
        self._count_meh = 0
        self._count_miss = 0
        self._score_accuracy = 0.0

    def CreatePerformanceAttributes(self, score, attributes):
        """Return what a mania score is worth.

        Args:
            score: The score to evaluate.
            attributes: The difficulty of the beatmap it was set on.

        Returns:
            The performance breakdown.
        """
        mods = list(score.Mods)

        self._count_perfect = score.GetCount(HitResult.Perfect)
        self._count_great = score.GetCount(HitResult.Great)
        self._count_good = score.GetCount(HitResult.Good)
        self._count_ok = score.GetCount(HitResult.Ok)
        self._count_meh = score.GetCount(HitResult.Meh)
        self._count_miss = max(0, score.GetCount(HitResult.Miss))
        self._score_accuracy = min(max(self._custom_accuracy(), 0.0), 1.0)

        multiplier = 1.0

        if _has_mod(mods, "NF"):
            multiplier *= 0.75
        if _has_mod(mods, "EZ"):
            multiplier *= 0.5

        difficulty_value = self._compute_difficulty_value(attributes)

        return ManiaPerformanceAttributes(
            Total=difficulty_value * multiplier,
            Difficulty=difficulty_value,
        )

    def _compute_difficulty_value(self, attributes) -> float:
        """Return what the beatmap's difficulty is worth to this score.

        Nothing is awarded below eighty per cent; above it a twentieth of the
        total is added for each further per cent.

        Args:
            attributes: The beatmap's difficulty.
        """
        return (
            8.0
            * DiffUtils.Pow(max(attributes.StarRating - 0.15, 0.05), 2.2)
            * max(0.0, 5 * self._score_accuracy - 4)
            # A length bonus, which stops counting past fifteen hundred notes.
            * (1 + 0.1 * min(1.0, self._total_hits / 1500))
        )

    @property
    def _total_hits(self) -> float:
        """Return how many notes the player was judged on."""
        return (
            self._count_perfect
            + self._count_ok
            + self._count_great
            + self._count_good
            + self._count_meh
            + self._count_miss
        )

    def _custom_accuracy(self) -> float:
        """Return the accuracy mania weighs its judgements by."""
        total = self._total_hits
        if total == 0:
            return 0.0

        return (
            self._count_perfect * JUDGEMENT_VALUES[HitResult.Perfect]
            + self._count_great * JUDGEMENT_VALUES[HitResult.Great]
            + self._count_good * JUDGEMENT_VALUES[HitResult.Good]
            + self._count_ok * JUDGEMENT_VALUES[HitResult.Ok]
            + self._count_meh * JUDGEMENT_VALUES[HitResult.Meh]
        ) / (total * JUDGEMENT_VALUES[HitResult.Perfect])


def _has_mod(mods: list, acronym: str) -> bool:
    """Return whether a mod is among those the score was set with.

    Args:
        mods: The mods the score was set with.
        acronym: The mod to look for.
    """
    return any(getattr(mod, "Acronym", None) == acronym for mod in mods)
