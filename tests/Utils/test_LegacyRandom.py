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

from parsecore.Utils.LegacyRandom import LegacyRandom

SEED = 1337


def test_the_raw_sequence_matches_osu():
    """Successive draws follow osu!'s sequence for a known seed."""
    rng = LegacyRandom(SEED)

    assert [rng.Next() for _ in range(10)] == [
        274941776,
        514112300,
        938046240,
        1928063929,
        2025352051,
        1132384915,
        1072880047,
        317283275,
        691095830,
        477031657,
    ]


def test_a_zero_seed_is_not_a_special_case():
    """Seeding with zero still walks the generator's own starting state."""
    rng = LegacyRandom(0)

    assert [rng.Next() for _ in range(5)] == [
        273327012,
        512581597,
        935368660,
        1925320520,
        936428855,
    ]


def test_fractions_match_osu():
    """Draws between zero and one match osu! to the last bit."""
    rng = LegacyRandom(SEED)

    assert [rng.NextDouble() for _ in range(5)] == [
        0.1280297413468361,
        0.23940219543874264,
        0.43681181967258453,
        0.8978247311897576,
        0.94312804332003,
    ]


def test_a_bounded_draw_matches_osu():
    """Draws within a range match osu!, negative bounds included."""
    rng = LegacyRandom(SEED)

    assert [rng.Next(-20, 20) for _ in range(10)] == [
        -14,
        -10,
        -2,
        15,
        17,
        1,
        0,
        -14,
        -7,
        -11,
    ]


def test_a_single_bound_counts_from_zero():
    """One bound is read as an upper bound, not a lower one."""
    rng = LegacyRandom(SEED)

    assert [rng.Next(100) for _ in range(5)] == [12, 23, 43, 89, 94]


def test_bits_come_from_one_draw_at_a_time():
    """Boolean draws spend a single number's bits before drawing again.

    This is why a beatmap's hard rock offsets depend on how many booleans were
    drawn earlier, not just on how many numbers were.
    """
    rng = LegacyRandom(SEED)

    assert [rng.NextBool() for _ in range(16)] == [
        False, False, False, False, True, False, True, False,
        True, True, True, False, False, False, True, False,
    ]


def test_the_same_seed_replays_the_same_beatmap():
    """Two generators from one seed stay in step."""
    first = LegacyRandom(SEED)
    second = LegacyRandom(SEED)

    assert [first.Next() for _ in range(20)] == [second.Next() for _ in range(20)]
