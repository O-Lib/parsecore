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
from parsecore.Beatmaps.Formats.LegacyBeatmapDecoder import LegacyBeatmapDecoder
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Mods.ModDoubleTime import ModDoubleTime
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    CalculateDifficultyPeppyStars,
)
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapConverter import OsuBeatmapConverter
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapProcessor import OsuBeatmapProcessor
from parsecore.Rulesets.Osu.Difficulty.OsuDifficultyCalculator import (
    OsuDifficultyCalculator,
)
from parsecore.Rulesets.Osu.Difficulty.OsuLegacyScoreSimulator import (
    GetLegacyScoreMultiplier,
    OsuLegacyScoreSimulator,
)
from parsecore.Rulesets.Osu.Difficulty.OsuPerformanceCalculator import (
    OsuPerformanceCalculator,
)
from parsecore.Rulesets.Osu.Mods.OsuModClassic import OsuModClassic
from parsecore.Rulesets.Osu.Mods.OsuModEasy import OsuModEasy
from parsecore.Rulesets.Osu.Mods.OsuModHardRock import OsuModHardRock
from parsecore.Rulesets.Osu.Mods.OsuModHidden import OsuModHidden
from parsecore.Rulesets.Osu.Mods.OsuModNoFail import OsuModNoFail
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Scoring.ScoreInfo import ScoreInfo

GOLDEN = [
    (
        "Kenji Ninuma - DISCOPRINCE (peppy) [Normal].osu",
        4,
        115.4639175257732,
        1416576,
    ),
    (
        "3rd Coast - Coastal Tempo (peppy) [Hard].osu",
        4,
        28.636363636363637,
        1518000,
    ),
]


def _attributes(path, mods=None):
    """Return the difficulty of a beatmap, legacy score figures included.

    Args:
        path: The beatmap file to rate.
        mods: The mods to rate it with.
    """
    mods = mods or []
    decoded = LegacyBeatmapDecoder.FromPath(str(path))
    playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor, mods
    )
    return decoded, OsuDifficultyCalculator(playable, decoded).Calculate(mods)


def test_the_score_figure_is_worked_out_at_decimal_precision():
    """osu!stable computed this on eighty bit registers, not on doubles.

    osu! reproduces that with a decimal type, and so does this. The three
    settings below add up to a value that a double would round the other way.
    """
    difficulty = BeatmapDifficulty()
    difficulty.DrainRate = 3.3
    difficulty.OverallDifficulty = 3.3
    difficulty.CircleSize = 3.3

    assert CalculateDifficultyPeppyStars(difficulty, 317, 37) == 3


def test_a_beatmap_with_no_drain_time_is_treated_as_dense():
    """With no length to measure against, the object ratio pins at sixteen."""
    difficulty = BeatmapDifficulty()
    difficulty.DrainRate = 0.0
    difficulty.OverallDifficulty = 0.0
    difficulty.CircleSize = 0.0

    assert CalculateDifficultyPeppyStars(difficulty, 100, 0) == 2


@pytest.mark.parametrize(
    "name,peppy_stars,nested_score,combo_score",
    GOLDEN,
    ids=[n.split(" - ")[0] for n, *_ in GOLDEN],
)
def test_a_beatmap_matches_osu(
    beatmap_files, name, peppy_stars, nested_score, combo_score
):
    """A real beatmap carries exactly the legacy score figures osu! reports."""
    path = next(f for f in beatmap_files if f.name == name)

    _, attributes = _attributes(path)

    assert attributes.LegacyScoreBaseMultiplier == peppy_stars
    assert attributes.NestedScorePerObject == nested_score
    assert attributes.MaximumLegacyComboScore == combo_score


def test_the_simulated_combo_never_exceeds_the_beatmap_s_own(beatmap_files):
    """The simulation walks the same objects the combo is counted from."""
    path = next(
        f for f in beatmap_files if f.name.startswith("Kenji Ninuma - DISCOPRINCE")
    )
    decoded = LegacyBeatmapDecoder.FromPath(str(path))
    playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor, []
    )

    simulated = OsuLegacyScoreSimulator().Simulate(decoded, playable)

    assert simulated.MaxCombo == playable.GetMaxCombo()
    assert simulated.AccuracyScore > 0


@pytest.mark.parametrize(
    "mods,expected",
    [
        ([], 1.0),
        ([OsuModNoFail()], 0.5),
        ([OsuModEasy()], 0.5),
        ([OsuModHidden()], 1.06),
        ([OsuModHardRock()], 1.06),
        ([ModDoubleTime()], 1.12),
        ([OsuModHidden(), OsuModHardRock()], 1.06 * 1.06),
    ],
    ids=["NM", "NF", "EZ", "HD", "HR", "DT", "HDHR"],
)
def test_the_mods_scale_an_old_score(mods, expected):
    """osu!stable paid more for some mods and less for others."""
    assert GetLegacyScoreMultiplier(mods) == pytest.approx(expected)


def test_relax_scored_nothing_at_all():
    """osu!stable refused to score a relax play."""
    from parsecore.Rulesets.Osu.Mods.OsuModRelax import OsuModRelax

    assert GetLegacyScoreMultiplier([OsuModRelax()]) == 0.0


LEGACY_PLAYS = [
    (314, 0, 194, 1474776, 1.0, 34.209837117751626),
    (282, 0, 194, 1209316, 1.0, 34.209837117751626),
    (219, 1, 193, 884865, 0.9948453608247423, 29.39506791603259),
    (125, 5, 189, 442432, 0.9742268041237113, 18.258804144556144),
    (31, 20, 174, 73738, 0.8969072164948454, 5.25604892536091),
]


@pytest.mark.parametrize(
    "combo,misses,great,legacy_total,accuracy,pp",
    LEGACY_PLAYS,
    ids=[f"combo{c}-miss{m}" for c, m, *_ in LEGACY_PLAYS],
)
def test_an_old_score_pays_what_osu_pays(
    beatmap_files, combo, misses, great, legacy_total, accuracy, pp
):
    """A score from osu!stable is worth exactly what osu! says it is."""
    path = next(
        f for f in beatmap_files if f.name.startswith("Kenji Ninuma - DISCOPRINCE")
    )
    mods = [OsuModClassic()]
    decoded, attributes = _attributes(path, mods)

    score = ScoreInfo(
        Mods=mods,
        BeatmapDifficulty=decoded.Difficulty,
        MaxCombo=combo,
        Accuracy=accuracy,
        LegacyTotalScore=legacy_total,
        Statistics={HitResult.Great: great, HitResult.Miss: misses},
    )

    assert OsuPerformanceCalculator().Calculate(score, attributes).Total == pp


def test_a_perfect_score_can_hide_no_combo_breaks(beatmap_files):
    """With nothing judged imperfectly, no break can be inferred at all.

    Both plays below dropped combo -- one to 314, one to 282 -- but neither
    dropped a single judgement, and an old score cannot have more breaks than
    it has imperfect hits. They are therefore worth exactly the same.
    """
    path = next(
        f for f in beatmap_files if f.name.startswith("Kenji Ninuma - DISCOPRINCE")
    )
    mods = [OsuModClassic()]
    decoded, attributes = _attributes(path, mods)

    def pp_for(legacy_total, combo):
        score = ScoreInfo(
            Mods=mods,
            BeatmapDifficulty=decoded.Difficulty,
            MaxCombo=combo,
            Accuracy=1.0,
            LegacyTotalScore=legacy_total,
            Statistics={HitResult.Great: 194},
        )
        return OsuPerformanceCalculator().Calculate(score, attributes).Total

    assert pp_for(1474776, 314) == pp_for(1209316, 282)


def test_a_score_that_dropped_judgements_is_read_from_its_total(beatmap_files):
    """Once judgements were dropped, a lower total is worth less.

    These are osu!'s own numbers: one miss at combo 219 pays more than five
    misses at combo 125, and the totals are what separate them.
    """
    path = next(
        f for f in beatmap_files if f.name.startswith("Kenji Ninuma - DISCOPRINCE")
    )
    mods = [OsuModClassic()]
    decoded, attributes = _attributes(path, mods)

    def pp_for(combo, misses, great, legacy_total, accuracy):
        score = ScoreInfo(
            Mods=mods,
            BeatmapDifficulty=decoded.Difficulty,
            MaxCombo=combo,
            Accuracy=accuracy,
            LegacyTotalScore=legacy_total,
            Statistics={HitResult.Great: great, HitResult.Miss: misses},
        )
        return OsuPerformanceCalculator().Calculate(score, attributes).Total

    one_miss = pp_for(219, 1, 193, 884865, 0.9948453608247423)
    five_misses = pp_for(125, 5, 189, 442432, 0.9742268041237113)

    assert one_miss > five_misses
