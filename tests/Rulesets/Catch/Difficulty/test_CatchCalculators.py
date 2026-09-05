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
from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmap import GetPalpableObjects
from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmapConverter import (
    CatchBeatmapConverter,
)
from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmapProcessor import (
    CatchBeatmapProcessor,
)
from parsecore.Rulesets.Catch.Difficulty.CatchDifficultyCalculator import (
    CatchDifficultyCalculator,
)
from parsecore.Rulesets.Catch.Difficulty.CatchPerformanceCalculator import (
    CatchPerformanceCalculator,
)
from parsecore.Rulesets.Catch.Mods.CatchModEasy import CatchModEasy
from parsecore.Rulesets.Catch.Mods.CatchModHardRock import CatchModHardRock
from parsecore.Rulesets.Catch.Objects.Banana import Banana
from parsecore.Rulesets.Catch.Objects.Droplet import Droplet, TinyDroplet
from parsecore.Rulesets.Catch.Objects.Fruit import Fruit
from parsecore.Rulesets.Mods.ModDoubleTime import ModDoubleTime
from parsecore.Rulesets.Mods.ModHalfTime import ModHalfTime
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Scoring.ScoreInfo import ScoreInfo
from tests.conftest import BEATMAPS_DIR
from tests.Rulesets.Catch.conftest import convert, fruits_at

MODS = {
    "DT": ModDoubleTime,
    "HT": ModHalfTime,
    "EZ": CatchModEasy,
    "HR": CatchModHardRock,
}

GOLDEN = [
    (
        "IOSYS - Taihen na Mono no Shoushitsu (DJPop) [Kana's CTB].osu",
        "",
        4.098745127925479,
        1009,
        (1008, 1, 138, 98),
        60,
        186.99951402045778,
    ),
    (
        "IOSYS - Taihen na Mono no Shoushitsu (DJPop) [Kana's CTB].osu",
        "DT",
        5.534967141016891,
        1009,
        (1008, 1, 138, 98),
        60,
        363.92609890940946,
    ),
    (
        "IOSYS - Taihen na Mono no Shoushitsu (DJPop) [Kana's CTB].osu",
        "HR",
        5.14857693153876,
        1009,
        (1008, 1, 138, 98),
        68,
        324.69476189269113,
    ),
    (
        "Kenji Ninuma - DISCOPRINCE (peppy) [Normal].osu",
        "",
        1.2469803911193629,
        310,
        (235, 75, 360, 116),
        0,
        16.677338779476052,
    ),
    (
        "Marika - Knowing short ver. (Konei) [Rain].osu",
        "",
        3.6680675908589313,
        407,
        (403, 4, 120, 33),
        25,
        139.6335217994471,
    ),
    (
        "Marika - Knowing short ver. (Konei) [Rain].osu",
        "EZ",
        3.912936057070208,
        407,
        (403, 4, 120, 33),
        14,
        174.81205111555656,
    ),
    (
        "Yuuki Aoi - PLATINUM (Short Ver.) (DJPop) [STAC's Platter].osu",
        "",
        3.402670986873391,
        438,
        (391, 47, 160, 33),
        25,
        120.58600720476915,
    ),
    (
        "Yuuki Aoi - PLATINUM (Short Ver.) (DJPop) [STAC's Platter].osu",
        "HT",
        2.710854124978523,
        438,
        (391, 47, 160, 33),
        25,
        77.12900347305448,
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
        CatchBeatmapConverter, CatchBeatmapProcessor, mods
    )

    palpable = list(GetPalpableObjects(playable.HitObjects))
    fruits = sum(1 for h in palpable if isinstance(h, Fruit))
    droplets = sum(
        1
        for h in palpable
        if isinstance(h, Droplet) and not isinstance(h, TinyDroplet)
    )
    tiny = sum(1 for h in palpable if isinstance(h, TinyDroplet))
    bananas = sum(1 for h in palpable if isinstance(h, Banana))
    hypers = sum(1 for h in palpable if h.HyperDash)

    attributes = CatchDifficultyCalculator(playable).Calculate(mods)

    score = ScoreInfo(
        Mods=mods,
        BeatmapDifficulty=decoded.Difficulty,
        MaxCombo=attributes.MaxCombo,
        Accuracy=1.0,
        Statistics={
            HitResult.Great: fruits,
            HitResult.LargeTickHit: droplets,
            HitResult.SmallTickHit: tiny,
        },
    )
    performance = CatchPerformanceCalculator().Calculate(score, attributes)

    return (fruits, droplets, tiny, bananas), hypers, attributes, performance


@pytest.mark.parametrize(
    "name,mods,star_rating,max_combo,counts,hyperdashes,pp",
    GOLDEN,
    ids=[f'{n.split(" - ")[0]}{"+" + m if m else ""}' for n, m, *_ in GOLDEN],
)
def test_a_beatmap_matches_osu(
    beatmap_files, name, mods, star_rating, max_combo, counts, hyperdashes, pp
):
    """A real beatmap rates and pays exactly what osu! says it does."""
    path = next(f for f in beatmap_files if f.name == name)

    got_counts, got_hypers, attributes, performance = _play(
        path, mods.split(",") if mods else []
    )

    assert got_counts == counts
    assert got_hypers == hyperdashes
    assert attributes.MaxCombo == max_combo
    assert attributes.StarRating == star_rating
    assert performance.Total == pp


def test_an_empty_beatmap_rates_at_zero():
    """A beatmap with nothing to catch is worth no stars."""
    attributes = CatchDifficultyCalculator(convert("")).Calculate([])

    assert attributes.StarRating == 0.0
    assert attributes.MaxCombo == 0


def test_bananas_and_tiny_droplets_do_not_count_towards_the_combo():
    """Only fruit and full droplets are worth combo."""
    beatmap = convert(fruits_at(100.0, 200.0) + "256,192,3000,12,0,5000\n")

    attributes = CatchDifficultyCalculator(beatmap).Calculate([])

    assert attributes.MaxCombo == 2


def test_a_faster_beatmap_is_harder():
    """The same fruit at double speed leave less time to reach them."""
    objects = fruits_at(50.0, 250.0, 50.0, 250.0, gap=300.0)

    plain = CatchDifficultyCalculator(convert(objects)).Calculate([])
    fast = CatchDifficultyCalculator(
        convert(objects, mods=[ModDoubleTime()])
    ).Calculate([ModDoubleTime()])

    assert fast.StarRating > plain.StarRating


def test_easy_makes_a_catch_beatmap_harder_to_rate_not_easier():
    """Easy shrinks the plate, so movements it barely covered now count.

    This is not a mistake: in catch the mod trades a longer warning for a
    narrower catcher, and on a busy beatmap the catcher is what matters.
    """
    path_name = "Marika - Knowing short ver. (Konei) [Rain].osu"

    _, plain_hypers, plain, _ = _play(BEATMAPS_DIR / path_name, [])
    _, easy_hypers, easy, _ = _play(BEATMAPS_DIR / path_name, ["EZ"])

    assert easy.StarRating > plain.StarRating
    assert easy_hypers < plain_hypers


def test_missing_everything_is_worth_nothing():
    """A score that caught nothing earns no performance points."""
    beatmap = convert(fruits_at(*[i * 30.0 for i in range(10)]))
    attributes = CatchDifficultyCalculator(beatmap).Calculate([])

    score = ScoreInfo(
        Mods=[],
        BeatmapDifficulty=beatmap.Difficulty,
        MaxCombo=0,
        Accuracy=0.0,
        Statistics={HitResult.Miss: 10},
    )
    performance = CatchPerformanceCalculator().Calculate(score, attributes)

    assert performance.Total == 0.0
