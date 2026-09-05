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

from parsecore.Rulesets.Catch.Difficulty.CatchDifficultyCalculator import (
    CatchDifficultyCalculator,
)
from parsecore.Rulesets.Catch.Difficulty.Evaluators import MovementEvaluator
from tests.Rulesets.Catch.conftest import convert, fruits_at


def _objects(objects: str, cs: float = 4.0) -> list:
    """Return the difficulty objects of a beatmap.

    Args:
        objects: The ``[HitObjects]`` lines to rate.
        cs: The circle size, which decides how wide the plate is.
    """
    beatmap = convert(objects, cs)
    return CatchDifficultyCalculator(beatmap).CreateDifficultyHitObjects(beatmap, 1.0)


def _difficulties(objects: str, cs: float = 4.0) -> list[float]:
    """Return how hard each movement in a beatmap is on its own.

    Args:
        objects: The ``[HitObjects]`` lines to rate.
        cs: The circle size, which decides how wide the plate is.
    """
    return [MovementEvaluator.EvaluateDifficultyOf(o) for o in _objects(objects, cs)]


def test_standing_still_is_worth_nothing():
    """Fruit falling on the same spot need no movement at all."""
    assert _difficulties(fruits_at(*[200.0] * 6, gap=200.0)) == [0.0] * 5


def test_moving_further_is_harder():
    """The same rhythm over a longer stretch is harder."""
    short = _difficulties(fruits_at(200.0, 230.0, 200.0, 230.0, gap=200.0))
    long = _difficulties(fruits_at(120.0, 320.0, 120.0, 320.0, gap=200.0))

    assert sum(long) > sum(short)


def test_turning_around_is_harder_than_carrying_on():
    """A movement that reverses costs more than one of the same length."""
    onwards = _difficulties(fruits_at(100.0, 200.0, 300.0, 400.0, gap=200.0))
    back_and_forth = _difficulties(fruits_at(100.0, 200.0, 100.0, 200.0, gap=200.0))

    assert sum(back_and_forth) > sum(onwards)


def test_a_steady_run_settles_into_a_rhythm():
    """Each further movement at one spacing is worth less than the last.

    A long run of evenly spaced fruit is caught by settling into a speed, so
    the evaluator stops paying for it.
    """
    run = _difficulties(fruits_at(*[80.0 + i * 40.0 for i in range(12)], gap=200.0))

    assert run[9] < run[1]
    assert run[1:10] == sorted(run[1:10], reverse=True)


def test_a_dash_that_only_just_reaches_is_the_hardest_thing_in_catch():
    """A movement just short of needing a hyper-dash is paid a large bonus.

    The bonus is what the edge-dash threshold exists for, so a beatmap sitting
    just inside it must rate above one sitting comfortably clear.
    """
    objects = _objects(fruits_at(20.0, 220.0, 20.0, 220.0, gap=150.0))

    on_the_edge = [
        o
        for o in objects
        if 0 < o.LastObject.DistanceToHyperDash <= MovementEvaluator.EDGE_DASH_THRESHOLD
    ]
    assert on_the_edge, "die beatmap sollte einen randdash enthalten"

    for difficulty_object in on_the_edge:
        with_bonus = MovementEvaluator.EvaluateDifficultyOf(difficulty_object)

        spare = difficulty_object.LastObject.DistanceToHyperDash
        difficulty_object.LastObject.DistanceToHyperDash = (
            MovementEvaluator.EDGE_DASH_THRESHOLD + 1.0
        )
        without_bonus = MovementEvaluator.EvaluateDifficultyOf(difficulty_object)
        difficulty_object.LastObject.DistanceToHyperDash = spare

        assert with_bonus > without_bonus


def test_a_hyper_dash_gets_no_edge_bonus():
    """Once the plate cannot reach at all, the bonus for nearly reaching stops."""
    objects = _objects(fruits_at(20.0, 400.0, 20.0, 400.0, gap=150.0))

    assert any(o.LastObject.HyperDash for o in objects)

    for difficulty_object in objects:
        if not difficulty_object.LastObject.HyperDash:
            continue

        assert difficulty_object.LastObject.DistanceToHyperDash == 0.0
