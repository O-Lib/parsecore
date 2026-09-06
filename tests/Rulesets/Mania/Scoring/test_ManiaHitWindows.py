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

from parsecore.Rulesets.Mania.Mods.ManiaModDoubleTime import ManiaModDoubleTime
from parsecore.Rulesets.Mania.Mods.ManiaModEasy import ManiaModEasy
from parsecore.Rulesets.Mania.Mods.ManiaModHalfTime import ManiaModHalfTime
from parsecore.Rulesets.Mania.Mods.ManiaModHardRock import ManiaModHardRock
from parsecore.Rulesets.Mania.Objects.HoldNote import HoldNote
from parsecore.Rulesets.Mania.Scoring.ManiaHitWindows import ManiaHitWindows
from parsecore.Rulesets.Scoring.HitResult import HitResult
from tests.Rulesets.Mania.conftest import convert, decode_mania, hold, notes_in

RESULTS = (
    HitResult.Perfect,
    HitResult.Great,
    HitResult.Good,
    HitResult.Ok,
    HitResult.Meh,
    HitResult.Miss,
)


def _windows(**settings) -> list[float]:
    """Return every window for a set of conditions.

    Args:
        settings: Any of ``od``, ``speed``, ``difficulty``, ``classic``,
            ``score_v2`` and ``convert``.
    """
    hit_windows = ManiaHitWindows()
    hit_windows.SetDifficulty(settings.get("od", 5.0))
    hit_windows.SpeedMultiplier = settings.get("speed", 1.0)
    hit_windows.DifficultyMultiplier = settings.get("difficulty", 1.0)
    hit_windows.ClassicModActive = settings.get("classic", False)
    hit_windows.ScoreV2Active = settings.get("score_v2", False)
    hit_windows.IsConvert = settings.get("convert", False)

    return [hit_windows.WindowFor(r) for r in RESULTS]


def test_the_windows_at_the_middle_difficulty_match_osu():
    """At difficulty five the windows are osu!'s own middle values."""
    assert _windows(od=5.0) == [19.5, 49.5, 82.5, 112.5, 136.5, 173.5]


def test_the_windows_tighten_as_the_difficulty_rises():
    """Every window is narrower at ten than at zero."""
    lenient = _windows(od=0.0)
    strict = _windows(od=10.0)

    assert lenient == [22.5, 64.5, 97.5, 127.5, 151.5, 188.5]
    assert strict == [13.5, 34.5, 67.5, 97.5, 121.5, 158.5]
    assert all(a < b for a, b in zip(strict, lenient, strict=True))


def test_a_faster_rate_widens_the_windows():
    """Scaling with the rate keeps the window the same length in real time."""
    assert _windows(od=5.0, speed=1.5) == [29.5, 73.5, 123.5, 168.5, 204.5, 259.5]


def test_a_slower_rate_widens_them_too():
    """A slower rate multiplies as well, because the time elapses slower."""
    assert _windows(od=5.0, speed=0.75) == [14.5, 36.5, 61.5, 84.5, 102.5, 129.5]


def test_hard_rock_tightens_the_windows_directly():
    """Mania's hard rock scales the windows rather than the difficulty."""
    assert _windows(od=5.0, difficulty=1.4) == [13.5, 35.5, 58.5, 80.5, 97.5, 123.5]


def test_easy_widens_them_directly():
    """Mania's easy scales the windows rather than the difficulty."""
    assert _windows(od=5.0, difficulty=1 / 1.4) == [
        27.5,
        68.5,
        114.5,
        156.5,
        190.5,
        242.5,
    ]


def test_the_classic_mod_replaces_the_whole_table():
    """The classic mod uses osu!stable's windows, not osu!lazer's."""
    assert _windows(od=5.0, classic=True) == [16.5, 49.5, 82.5, 112.5, 136.5, 173.5]
    assert _windows(od=8.0, classic=True) == [16.5, 40.5, 73.5, 103.5, 127.5, 164.5]


def test_a_converted_beatmap_has_only_two_classic_tables():
    """osu!stable picked between two window sets by a single threshold."""
    lenient = _windows(od=4.0, classic=True, convert=True)
    strict = _windows(od=5.0, classic=True, convert=True)

    assert lenient == [16.5, 47.5, 77.5, 97.5, 121.5, 158.5]
    assert strict == [16.5, 34.5, 67.5, 97.5, 121.5, 158.5]
    assert _windows(od=0.0, classic=True, convert=True) == lenient
    assert _windows(od=10.0, classic=True, convert=True) == strict


def test_the_classic_threshold_rounds_a_half_to_the_even_number():
    """A difficulty of four and a half rounds down, so it stays lenient.

    osu! rounds a half to the nearest even number rather than upwards, which
    puts this one on the lenient side of a threshold it looks like it should
    clear.
    """
    assert _windows(od=4.5, classic=True, convert=True) == _windows(
        od=4.0, classic=True, convert=True
    )


def test_the_second_scoring_version_undoes_the_classic_table():
    """With score v2 on, the classic mod stops replacing the windows."""
    assert _windows(od=5.0, classic=True, score_v2=True) == _windows(od=5.0)


def test_only_the_six_mania_judgements_are_awarded():
    """Mania has no ticks or bonuses to judge."""
    hit_windows = ManiaHitWindows()

    assert all(hit_windows.IsHitResultAllowed(r) for r in RESULTS)
    assert not hit_windows.IsHitResultAllowed(HitResult.LargeTickHit)
    assert not hit_windows.IsHitResultAllowed(HitResult.SmallBonus)


@pytest.mark.parametrize(
    "mod,expected",
    [
        (None, 49.5),
        (ManiaModDoubleTime, 73.5),
        (ManiaModHalfTime, 36.5),
        (ManiaModHardRock, 35.5),
        (ManiaModEasy, 68.5),
    ],
    ids=["NM", "DT", "HT", "HR", "EZ"],
)
def test_a_mod_reaches_the_notes_of_a_beatmap(mod, expected):
    """The mods are applied to every note the beatmap ends up with."""
    beatmap = convert(
        decode_mania(notes_in(0, 1, keys=4), keys=4, od=5.0),
        [] if mod is None else [mod()],
    )

    assert beatmap.HitObjects[0].HitWindows.WindowFor(HitResult.Great) == expected


@pytest.mark.parametrize(
    "mod,expected",
    [(None, 49.5), (ManiaModDoubleTime, 73.5), (ManiaModHardRock, 35.5)],
    ids=["NM", "DT", "HR"],
)
def test_a_mod_reaches_both_ends_of_a_hold(mod, expected):
    """A hold is judged through its head and tail, so both must be adjusted."""
    beatmap = convert(
        decode_mania(hold(1, 1000, 2000, keys=4), keys=4, od=5.0),
        [] if mod is None else [mod()],
    )
    held = beatmap.HitObjects[0]

    assert isinstance(held, HoldNote)
    assert held.Head.HitWindows.WindowFor(HitResult.Great) == expected
    assert held.Tail.HitWindows.WindowFor(HitResult.Great) == expected
