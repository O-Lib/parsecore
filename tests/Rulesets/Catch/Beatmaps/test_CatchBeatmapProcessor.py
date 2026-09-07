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

from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmap import GetPalpableObjects
from parsecore.Rulesets.Catch.Mods.CatchModHardRock import CatchModHardRock
from parsecore.Rulesets.Catch.Objects.Banana import Banana
from parsecore.Rulesets.Catch.Objects.Fruit import Fruit
from parsecore.Rulesets.Catch.UI.CatchPlayfield import WIDTH as PLAYFIELD_WIDTH
from tests.Rulesets.Catch.conftest import convert, fruits_at


def _fruit(beatmap):
    """Return the beatmap's fruit, in the order they fall."""
    return [h for h in GetPalpableObjects(beatmap.HitObjects) if isinstance(h, Fruit)]


def test_a_reachable_fruit_is_not_a_hyper_dash():
    """Two fruit half a second and a few pixels apart need no hyper-dash."""
    beatmap = convert(fruits_at(200.0, 240.0), cs=4.0)

    assert [f.HyperDash for f in _fruit(beatmap)] == [False, False]


def test_an_unreachable_fruit_becomes_a_hyper_dash():
    """A dash across the playfield in a fraction of a second cannot be run."""
    beatmap = convert(fruits_at(0.0, PLAYFIELD_WIDTH, gap=100.0), cs=4.0)

    assert _fruit(beatmap)[0].HyperDash is True


def test_a_hyper_dash_points_at_what_it_reaches_for():
    """A hyper-dash names the object the plate has to get to."""
    beatmap = convert(fruits_at(0.0, PLAYFIELD_WIDTH, gap=100.0), cs=4.0)
    fruit = _fruit(beatmap)

    assert fruit[0].HyperDashTarget is fruit[1]
    assert fruit[0].DistanceToHyperDash == 0.0


def test_a_reachable_fruit_remembers_how_much_room_was_to_spare():
    """A dash that works records what was left, because only just is hard."""
    beatmap = convert(fruits_at(200.0, 260.0), cs=4.0)
    first = _fruit(beatmap)[0]

    assert first.HyperDash is False
    assert first.DistanceToHyperDash > 0.0


def test_the_last_fruit_is_never_a_hyper_dash():
    """There is nothing after the last fruit to dash towards."""
    beatmap = convert(fruits_at(0.0, PLAYFIELD_WIDTH, 0.0, gap=100.0), cs=4.0)

    assert _fruit(beatmap)[-1].HyperDash is False


def test_a_narrower_plate_turns_dashes_into_hyper_dashes():
    """The same beatmap at a higher circle size needs more hyper-dashes."""
    objects = fruits_at(0.0, 200.0, 0.0, 200.0, gap=150.0)

    wide = sum(f.HyperDash for f in _fruit(convert(objects, cs=0.0)))
    narrow = sum(f.HyperDash for f in _fruit(convert(objects, cs=9.0)))

    assert wide == 0
    assert narrow == 3


def test_bananas_are_scattered_the_same_way_every_time():
    """The scatter comes from a fixed seed, so a beatmap always replays."""
    objects = "256,192,1000,12,0,3000\n"

    first = [
        h.EffectiveX
        for h in GetPalpableObjects(convert(objects).HitObjects)
        if isinstance(h, Banana)
    ]
    second = [
        h.EffectiveX
        for h in GetPalpableObjects(convert(objects).HitObjects)
        if isinstance(h, Banana)
    ]

    assert first == second
    assert all(0.0 <= x <= PLAYFIELD_WIDTH for x in first)


def test_hard_rock_moves_the_fruit():
    """Hard rock nudges fruit sideways as well as raising the settings."""
    objects = fruits_at(100.0, 100.0, 140.0, 180.0, gap=200.0)

    plain = [f.EffectiveX for f in _fruit(convert(objects))]
    hard = [f.EffectiveX for f in _fruit(convert(objects, mods=[CatchModHardRock()]))]

    assert plain != hard
    assert all(0.0 <= x <= PLAYFIELD_WIDTH for x in hard)


def test_hard_rock_leaves_a_distant_fruit_alone():
    """A fruit more than a second after the last one is not nudged."""
    objects = fruits_at(100.0, 260.0, gap=2000.0)

    plain = [f.EffectiveX for f in _fruit(convert(objects))]
    hard = [f.EffectiveX for f in _fruit(convert(objects, mods=[CatchModHardRock()]))]

    assert plain == hard


def test_a_banana_shower_starts_a_new_combo_after_it():
    """The fruit following a shower opens a combo of its own."""
    beatmap = convert(
        "100,192,1000,1,0\n256,192,1500,12,0,2500\n100,192,3000,1,0\n"
    )
    after = [h for h in beatmap.HitObjects if isinstance(h, Fruit)][-1]

    assert after.NewCombo is True


def test_every_object_knows_where_it_sits_in_the_beatmap():
    """Nested objects carry the index of the object they came from."""
    beatmap = convert(fruits_at(100.0, 200.0) + "0,192,2500,2,0,L|100:192,1,100\n")

    assert [h.IndexInBeatmap for h in beatmap.HitObjects] == [0, 1, 2]
    stream = beatmap.HitObjects[2]
    assert all(n.IndexInBeatmap == 2 for n in stream.NestedHitObjects)
