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

from parsecore.Beatmaps.Formats.LegacyBeatmapDecoder import LegacyBeatmapDecoder
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Mania.Beatmaps.ManiaBeatmapConverter import (
    ManiaBeatmapConverter,
)
from parsecore.Rulesets.Mania.Difficulty.ManiaDifficultyCalculator import (
    ManiaDifficultyCalculator,
)
from parsecore.Rulesets.Mania.Difficulty.ManiaPerformanceCalculator import (
    ManiaPerformanceCalculator,
)
from parsecore.Rulesets.Mania.Mods.ManiaKeyMod import ManiaModKey4, ManiaModKey7
from parsecore.Rulesets.Mania.Mods.ManiaModDoubleTime import ManiaModDoubleTime
from parsecore.Rulesets.Mania.Mods.ManiaModEasy import ManiaModEasy
from parsecore.Rulesets.Mania.Mods.ManiaModHalfTime import ManiaModHalfTime
from parsecore.Rulesets.Mania.Objects.HoldNote import HoldNote
from parsecore.Rulesets.Mania.Objects.Note import Note
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Scoring.ScoreInfo import ScoreInfo
from tests.Rulesets.Mania.conftest import convert, decode_mania, hold, notes_in

MODS = {
    "DT": ManiaModDoubleTime,
    "HT": ManiaModHalfTime,
    "EZ": ManiaModEasy,
    "4K": ManiaModKey4,
    "7K": ManiaModKey7,
}

GOLDEN = [
    (
        "fripSide - only my railgun (TV Size) (DJPop) [4K NM].osu",
        "",
        4,
        (209, 8),
        403,
        1.2796036150956442,
        10.616794010194964,
    ),
    (
        "fripSide - only my railgun (TV Size) (DJPop) [4K NM].osu",
        "DT",
        4,
        (209, 8),
        403,
        1.6268548646905983,
        19.146933485165704,
    ),
    (
        "nayuta - Toki wo Kizamu Uta (Hanyuu) [7K MX].osu",
        "",
        7,
        (1209, 55),
        2147,
        3.4539453771097075,
        120.66034408521782,
    ),
    (
        "nayuta - Toki wo Kizamu Uta (Hanyuu) [7K MX].osu",
        "HT",
        7,
        (1209, 55),
        2147,
        2.775926512576752,
        72.79707339646171,
    ),
    (
        "Kenji Ninuma - DISCOPRINCE (peppy) [Normal].osu",
        "",
        7,
        (249, 46),
        761,
        1.94569349292187,
        29.659461210841453,
    ),
    (
        "Kenji Ninuma - DISCOPRINCE (peppy) [Normal].osu",
        "4K",
        4,
        (250, 41),
        735,
        1.8234245215362206,
        25.382302844395777,
    ),
    (
        "IOSYS - Endless Tewi-ma Park (Kurosanyan) [Drafura's Rain].osu",
        "",
        7,
        (1662, 62),
        1872,
        4.2975852402576065,
        201.20203865316552,
    ),
    (
        "IOSYS - Endless Tewi-ma Park (Kurosanyan) [Drafura's Rain].osu",
        "7K",
        7,
        (1662, 62),
        1872,
        4.2975852402576065,
        201.20203865316552,
    ),
    (
        "Chata - First Love (Laurier) [Insane].osu",
        "",
        7,
        (882, 463),
        2234,
        2.5296923102087066,
        59.26911576140199,
    ),
    (
        "Chata - First Love (Laurier) [Insane].osu",
        "EZ",
        7,
        (882, 463),
        2234,
        2.5296923102087066,
        29.634557880700996,
    ),
]


def _play(path, acronyms):
    """Return the object counts, difficulty and pp of a perfect play.

    Args:
        path: The beatmap file to play.
        acronyms: The mods to play it with.
    """
    mods = [MODS[a]() for a in acronyms]
    decoded = LegacyBeatmapDecoder.FromPath(str(path))
    playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
        ManiaBeatmapConverter, None, mods
    )
    attributes = ManiaDifficultyCalculator(playable).Calculate(mods)

    notes = sum(1 for h in playable.HitObjects if isinstance(h, Note))
    holds = sum(1 for h in playable.HitObjects if isinstance(h, HoldNote))

    score = ScoreInfo(
        Mods=mods,
        BeatmapDifficulty=decoded.Difficulty,
        MaxCombo=attributes.MaxCombo,
        Accuracy=1.0,
        Statistics={HitResult.Perfect: notes + holds * 2},
    )
    performance = ManiaPerformanceCalculator().Calculate(score, attributes)

    return playable, (notes, holds), attributes, performance


@pytest.mark.parametrize(
    "name,mods,columns,counts,max_combo,star_rating,pp",
    GOLDEN,
    ids=[f'{n.split(" - ")[0]}{"+" + m if m else ""}' for n, m, *_ in GOLDEN],
)
def test_a_beatmap_matches_osu(
    beatmap_files, name, mods, columns, counts, max_combo, star_rating, pp
):
    """A real beatmap rates and pays exactly what osu! says it does."""
    path = next(f for f in beatmap_files if f.name == name)

    playable, got_counts, attributes, performance = _play(
        path, mods.split(",") if mods else []
    )

    assert playable.TotalColumns == columns
    assert got_counts == counts
    assert attributes.MaxCombo == max_combo
    assert attributes.StarRating == star_rating
    assert performance.Total == pp


def test_an_empty_beatmap_rates_at_zero():
    """A beatmap with nothing to play is worth no stars."""
    attributes = ManiaDifficultyCalculator(convert(decode_mania(""))).Calculate([])

    assert attributes.StarRating == 0.0
    assert attributes.MaxCombo == 0


def test_a_hold_is_worth_combo_for_every_tenth_of_a_second():
    """A hold is worth its head plus one for each tick it would award."""
    beatmap = convert(decode_mania(hold(0, 1000, 1550, keys=4), keys=4))

    attributes = ManiaDifficultyCalculator(beatmap).Calculate([])

    assert attributes.MaxCombo == 1 + 5


def test_a_faster_beatmap_is_harder():
    """The same notes at double speed leave less time between them.

    A beatmap has to be long enough for this to show. Rating sums a peak per
    four hundred milliseconds, so speeding a very short beatmap up removes
    sections faster than it raises the peaks -- osu! rates the sixty note run
    below at 1.2219 without the mod and 1.5191 with it, but an eight note one
    lower with the mod than without.
    """
    objects = notes_in(*[i % 4 for i in range(60)], keys=4, gap=200.0)
    decoded = decode_mania(objects, keys=4)

    plain = ManiaDifficultyCalculator(convert(decoded)).Calculate([])
    fast = ManiaDifficultyCalculator(
        convert(decoded, [ManiaModDoubleTime()])
    ).Calculate([ManiaModDoubleTime()])

    assert plain.StarRating == 1.2219015455650597
    assert fast.StarRating == 1.5191211086119376


CHORD_ORDERS = [
    ((0, 1, 2, 3), 0.19737090736447316),
    ((3, 2, 1, 0), 0.19737090736447316),
    ((2, 0, 3, 1), 0.19737090736447316),
    ((1, 3, 0, 2), 0.1880664506889972),
]


@pytest.mark.parametrize("order,star_rating", CHORD_ORDERS, ids=lambda v: str(v))
def test_the_order_a_chord_is_written_in_can_change_the_rating(order, star_rating):
    """Which note of a chord is read first is decided by osu!'s own sort.

    Notes struck together compare equal, so the order they end up in is
    whatever the unstable sort osu! inherited from .NET 4.0 happens to leave --
    and that order decides which note the strain is measured from. Three of the
    four orders below rate alike and the fourth does not; these are osu!'s own
    numbers, and reproducing them is the whole reason that sort is ported
    rather than replaced.
    """
    objects = "".join(_note_line(column, 1000) for column in order)
    objects += _note_line(0, 1600)

    attributes = ManiaDifficultyCalculator(
        convert(decode_mania(objects, keys=4))
    ).Calculate([])

    assert attributes.StarRating == star_rating


def _note_line(column: int, time: int) -> str:
    """Return one hit object line for a mania note.

    Args:
        column: The column to place it in.
        time: When it is, in milliseconds.
    """
    return f"{int((column + 0.5) * 512 / 4)},192,{time},1,0\n"


def test_easy_halves_what_a_score_is_worth():
    """The easy mod does not change the rating, only the reward."""
    path_name = "Chata - First Love (Laurier) [Insane].osu"
    from tests.conftest import BEATMAPS_DIR

    _, _, plain_attributes, plain = _play(BEATMAPS_DIR / path_name, [])
    _, _, easy_attributes, easy = _play(BEATMAPS_DIR / path_name, ["EZ"])

    assert easy_attributes.StarRating == plain_attributes.StarRating
    assert easy.Total == pytest.approx(plain.Total * 0.5)


def test_nothing_is_awarded_below_eighty_per_cent():
    """The pp curve starts at eighty per cent accuracy and not before."""
    beatmap = convert(decode_mania(notes_in(*range(4), keys=4) * 1, keys=4))
    attributes = ManiaDifficultyCalculator(beatmap).Calculate([])

    poor = ScoreInfo(
        Mods=[],
        BeatmapDifficulty=beatmap.Difficulty,
        MaxCombo=0,
        Accuracy=0.0,
        Statistics={HitResult.Meh: 4},
    )

    assert ManiaPerformanceCalculator().Calculate(poor, attributes).Total == 0.0


def test_a_three_hundred_and_twenty_is_worth_more_than_a_three_hundred():
    """Mania weighs its two best judgements apart, unlike the accuracy shown."""
    beatmap = convert(decode_mania(notes_in(*range(4), keys=4), keys=4))
    attributes = ManiaDifficultyCalculator(beatmap).Calculate([])

    def worth(result):
        score = ScoreInfo(
            Mods=[],
            BeatmapDifficulty=beatmap.Difficulty,
            MaxCombo=attributes.MaxCombo,
            Accuracy=1.0,
            Statistics={result: 4},
        )
        return ManiaPerformanceCalculator().Calculate(score, attributes).Total

    assert worth(HitResult.Perfect) > worth(HitResult.Great) > 0
