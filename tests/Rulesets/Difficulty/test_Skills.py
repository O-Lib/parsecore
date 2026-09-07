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

import pytest

from parsecore.Rulesets.Difficulty.Preprocessing.DifficultyHitObject import (
    DifficultyHitObject,
)
from parsecore.Rulesets.Difficulty.Skills.StrainDecaySkill import StrainDecaySkill
from parsecore.Rulesets.Objects.HitObject import HitObject


class ConstantStrainSkill(StrainDecaySkill):
    """A skill where every object contributes the same strain."""

    SkillMultiplier = 1.0
    StrainDecayBase = 0.3

    def StrainValueOf(self, current):
        """Return a fixed strain for any object."""
        return 1.0


def _make_objects(times: list[float], clock_rate: float = 1.0):
    """Build a difficulty hit object list from a list of start times."""
    objects: list[DifficultyHitObject] = []
    hit_objects = [HitObject(t) for t in times]
    for i in range(1, len(hit_objects)):
        objects.append(
            DifficultyHitObject(
                hit_objects[i], hit_objects[i - 1], clock_rate, objects, i - 1
            )
        )
    return objects


def test_difficulty_hit_object_navigation():
    """An object can reach its neighbours in both directions."""
    objects = _make_objects([0, 100, 200, 300])
    assert objects[1].Previous(0) is objects[0]
    assert objects[1].Next(0) is objects[2]
    assert objects[0].Previous(0) is None
    assert objects[-1].Next(0) is None


def test_clock_rate_scales_times():
    """A faster clock rate shortens delta times proportionally."""
    normal = _make_objects([0, 100])
    fast = _make_objects([0, 100], clock_rate=1.5)
    assert normal[0].DeltaTime == pytest.approx(100)
    assert fast[0].DeltaTime == pytest.approx(100 / 1.5)


def test_denser_rhythm_is_harder_over_the_same_span():
    """Over one span of time, more closely spaced objects build more strain."""
    span = 4000
    dense = ConstantStrainSkill()
    for obj in _make_objects(list(range(0, span, 100))):
        dense.Process(obj)

    sparse = ConstantStrainSkill()
    for obj in _make_objects(list(range(0, span, 500))):
        sparse.Process(obj)

    assert dense.DifficultyValue() > sparse.DifficultyValue()


def test_difficulty_is_summed_over_sections():
    """A longer beatmap contributes more sections to the weighted sum.

    Sections are the unit of a strain skill, so the same rhythm played for
    longer is worth more -- this is what makes star rating length-dependent.
    """
    short = ConstantStrainSkill()
    for obj in _make_objects(list(range(0, 2000, 100))):
        short.Process(obj)

    long = ConstantStrainSkill()
    for obj in _make_objects(list(range(0, 8000, 100))):
        long.Process(obj)

    assert long.DifficultyValue() > short.DifficultyValue()


def test_no_objects_gives_no_difficulty():
    """A skill that saw nothing reports zero difficulty."""
    assert ConstantStrainSkill().DifficultyValue() == 0.0
