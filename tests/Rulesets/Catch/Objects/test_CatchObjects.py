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

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Rulesets.Catch.Objects.Banana import Banana, BananaShower
from parsecore.Rulesets.Catch.Objects.Droplet import Droplet, TinyDroplet
from parsecore.Rulesets.Catch.Objects.Fruit import Fruit
from parsecore.Rulesets.Catch.Objects.JuiceStream import JuiceStream
from parsecore.Rulesets.Catch.UI.Catcher import (
    CalculateCatchWidth,
    CalculateScale,
)
from parsecore.Rulesets.Catch.UI.CatchPlayfield import WIDTH as PLAYFIELD_WIDTH
from parsecore.Utils.Vector2 import f32
from tests.Rulesets.Catch.conftest import convert, fruits_at


def test_a_position_is_kept_at_the_precision_osu_stores_it_in():
    """A position is narrowed to single precision when it is set."""
    fruit = Fruit(0.0, 1.0 / 3.0)

    assert fruit.OriginalX == f32(1.0 / 3.0)
    assert fruit.OriginalX != 1.0 / 3.0


def test_an_offset_position_stays_on_the_playfield():
    """An object nudged past either edge is pulled back onto the playfield."""
    fruit = Fruit(0.0, 10.0)
    fruit.XOffset = -100.0

    assert fruit.EffectiveX == 0.0

    fruit.OriginalX = PLAYFIELD_WIDTH - 10.0
    fruit.XOffset = 100.0

    assert fruit.EffectiveX == PLAYFIELD_WIDTH


def test_the_offset_is_added_at_single_precision():
    """Position and offset are added before the result is widened."""
    fruit = Fruit(0.0, 1.0)
    fruit.XOffset = 1.0 / 3.0

    assert fruit.EffectiveX == f32(f32(1.0) + f32(1.0 / 3.0))


def test_the_plate_is_drawn_at_twice_an_object_s_scale():
    """The plate's scale is twice what a circle of the same size would be.

    Halving this silently doubles how many dashes look reachable, so it is
    worth pinning down on its own.
    """
    difficulty = BeatmapDifficulty()
    difficulty.CircleSize = 4.0

    midpoint = BeatmapDifficulty()
    midpoint.CircleSize = 5.0

    assert CalculateScale(midpoint) == 1.0
    assert CalculateScale(difficulty) > CalculateScale(midpoint)


@pytest.mark.parametrize("circle_size", [0.0, 2.0, 4.0, 5.0, 7.0, 10.0])
def test_the_catch_width_narrows_as_the_circle_size_grows(circle_size):
    """A larger circle size leaves a narrower stretch of playfield caught."""
    difficulty = BeatmapDifficulty()
    difficulty.CircleSize = circle_size
    narrower = BeatmapDifficulty()
    narrower.CircleSize = circle_size + 0.5

    assert CalculateCatchWidth(difficulty) > CalculateCatchWidth(narrower)


def test_a_juice_stream_drops_fruit_at_both_ends():
    """A stream that is only long enough for its ends drops exactly two."""
    beatmap = convert("0,192,1000,2,0,L|100:192,1,100\n")
    stream = beatmap.HitObjects[0]

    assert isinstance(stream, JuiceStream)

    fruit = [n for n in stream.NestedHitObjects if isinstance(n, Fruit)]
    assert len(fruit) == 2
    assert fruit[0].StartTime == stream.StartTime
    assert fruit[1].StartTime == pytest.approx(stream.EndTime)


def test_a_juice_stream_fills_a_long_gap_with_tiny_droplets():
    """A gap wider than eighty milliseconds is filled with tiny droplets."""
    beatmap = convert("0,192,1000,2,0,L|400:192,1,400\n")
    stream = beatmap.HitObjects[0]

    tiny = [n for n in stream.NestedHitObjects if isinstance(n, TinyDroplet)]

    assert tiny
    for droplet in tiny:
        assert stream.StartTime < droplet.StartTime < stream.EndTime


def test_a_repeated_juice_stream_drops_fruit_at_every_node():
    """Each end and repeat of a stream drops a fruit."""
    beatmap = convert("0,192,1000,2,0,L|100:192,3,100\n")
    stream = beatmap.HitObjects[0]

    fruit = [n for n in stream.NestedHitObjects if isinstance(n, Fruit)]

    assert stream.SpanCount == 3
    assert len(fruit) == 4


def test_a_banana_shower_drops_bananas_across_the_playfield():
    """A shower fills its duration with bananas at scattered positions."""
    beatmap = convert("256,192,1000,12,0,3000\n")
    shower = beatmap.HitObjects[0]

    assert isinstance(shower, BananaShower)

    bananas = [n for n in shower.NestedHitObjects if isinstance(n, Banana)]
    assert len(bananas) > 1
    assert len({banana.EffectiveX for banana in bananas}) > 1


def test_a_tiny_droplet_is_still_a_droplet():
    """The scoring code tells the two apart by type, not by a flag."""
    assert issubclass(TinyDroplet, Droplet)


def test_a_fruit_falls_where_the_beatmap_put_it():
    """A plain circle becomes a fruit at the same position."""
    beatmap = convert(fruits_at(100.0, 200.0, 300.0))

    assert [h.EffectiveX for h in beatmap.HitObjects] == [100.0, 200.0, 300.0]
    assert all(isinstance(h, Fruit) for h in beatmap.HitObjects)
