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

from parsecore.Rulesets.Difficulty.DifficultyAttributes import DifficultyAttributes
from parsecore.Rulesets.Difficulty.PerformanceAttributes import PerformanceAttributes
from parsecore.Scoring.ScoreInfo import ScoreInfo


class PerformanceCalculator:
    """Calculates what a score is worth for one ruleset."""

    def Calculate(
        self, score: ScoreInfo, attributes: DifficultyAttributes
    ) -> PerformanceAttributes:
        """Return the performance attributes of a score.

        Args:
            score: The score to evaluate.
            attributes: The difficulty of the beatmap it was set on.
        """
        return self.CreatePerformanceAttributes(score, attributes)

    def CreatePerformanceAttributes(
        self, score: ScoreInfo, attributes: DifficultyAttributes
    ) -> PerformanceAttributes:
        """Build this ruleset's performance breakdown.

        Args:
            score: The score to evaluate.
            attributes: The difficulty of the beatmap it was set on.
        """
        raise NotImplementedError
