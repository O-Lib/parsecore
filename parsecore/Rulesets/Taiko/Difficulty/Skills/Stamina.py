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
from parsecore.Rulesets.Difficulty.Skills.StrainSkill import StrainSkill
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Taiko.Difficulty.Evaluators import StaminaEvaluator

SKILL_MULTIPLIER = 1.1
STRAIN_DECAY_BASE = 0.4


def index_in_mono_streak(hit_object) -> int:
    """Return how deep into its colour run a note sits.

    Args:
        hit_object: The difficulty object to place.

    Returns:
        The note's position in its run, or ``0`` where it has none.
    """
    streak = getattr(hit_object, "ColourData", None)
    streak = streak.MonoStreak if streak is not None else None
    if streak is None:
        return 0

    for index, candidate in enumerate(streak.HitObjects):
        if candidate is hit_object:
            return index

    # osu! reads this off a list search that reports -1 when the note is
    # absent, and passes that on rather than treating it as the start.
    return -1


class Stamina(StrainSkill):
    """The strain of drumming a passage fast enough to keep up."""

    def __init__(
        self,
        mods: list | None = None,
        single_colour_stamina: bool = False,
        is_convert: bool = False,
    ) -> None:
        """Create the stamina skill.

        Args:
            mods: The mods the score was set with.
            single_colour_stamina: Whether to measure only what one colour
                demands, ignoring the relief of switching hands.
            is_convert: Whether the beatmap was written for another ruleset,
                in which case long colour runs are not the mapper's doing.
        """
        super().__init__(mods)
        self.SingleColourStamina = single_colour_stamina
        self._is_convert = is_convert
        self._current_strain = 0.0

    @staticmethod
    def _strain_decay(ms: float) -> float:
        """Return the decay factor over a time span.

        Args:
            ms: The elapsed time in milliseconds.
        """
        return DiffUtils.Pow(STRAIN_DECAY_BASE, ms / 1000)

    def StrainValueAt(self, current: DifficultyHitObject) -> float:
        """Return the stamina strain after this object.

        Args:
            current: The object being processed.
        """
        self._current_strain *= self._strain_decay(current.DeltaTime)
        stamina_difficulty = (
            StaminaEvaluator.EvaluateDifficultyOf(current) * SKILL_MULTIPLIER
        )

        index = index_in_mono_streak(current)

        # A long run of one colour is harder than the same notes alternating,
        # but only where the mapper chose it rather than a conversion.
        mono_length_bonus = (
            1.0
            if self._is_convert
            else 1.0 + 0.5 * DiffUtils.ReverseLerp(index, 5, 20)
        )

        if not self.SingleColourStamina:
            stamina_difficulty *= mono_length_bonus

        self._current_strain += stamina_difficulty

        if self.SingleColourStamina:
            return DiffUtils.LogisticExp(-(index - 10) / 2.0, self._current_strain)

        return self._current_strain

    def CalculateInitialStrain(
        self, time: float, current: DifficultyHitObject
    ) -> float:
        """Return the strain decayed to the start of a new section.

        Measuring a single colour has no strain to carry across a section, as
        the run it was measuring has ended.

        Args:
            time: The time the section starts.
            current: The object that triggered the new section.
        """
        if self.SingleColourStamina:
            return 0.0

        previous = current.Previous(0)
        if previous is None:
            return 0.0

        return self._current_strain * self._strain_decay(time - previous.StartTime)
