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

from parsecore.Rulesets.Difficulty.Preprocessing.DifficultyHitObject import (
    DifficultyHitObject,
)
from parsecore.Rulesets.Difficulty.Skills.StrainDecaySkill import StrainDecaySkill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Taiko.Difficulty.Evaluators import (
    RhythmEvaluator,
    StaminaEvaluator,
)


class Rhythm(StrainDecaySkill):
    """The strain of reading and landing changing rhythms."""

    SkillMultiplier = 1.0
    StrainDecayBase = 0.4

    def StrainValueOf(self, current: DifficultyHitObject) -> float:
        """Return how much rhythm strain an object adds.

        Args:
            current: The object being processed.
        """
        difficulty = RhythmEvaluator.EvaluateDifficultyOf(current)

        # The base strain every note carries is taken back out, so only the
        # speed the passage actually demands gates the rhythm.
        stamina_difficulty = StaminaEvaluator.EvaluateDifficultyOf(current) - 0.5
        return difficulty * DiffUtils.Logistic(stamina_difficulty, 1 / 15.0, 50.0)
