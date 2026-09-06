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
from parsecore.Rulesets.Mods.ModDoubleTime import ModDoubleTime
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Rulesets.Taiko.Beatmaps.TaikoBeatmapConverter import (
    TaikoBeatmapConverter,
)
from parsecore.Rulesets.Taiko.Difficulty.TaikoDifficultyCalculator import (
    TaikoDifficultyCalculator,
)
from parsecore.Rulesets.Taiko.Difficulty.TaikoPerformanceCalculator import (
    TaikoPerformanceCalculator,
)
from parsecore.Rulesets.Taiko.Mods.TaikoModEasy import TaikoModEasy
from parsecore.Rulesets.Taiko.Mods.TaikoModHardRock import TaikoModHardRock
from parsecore.Rulesets.Taiko.Objects.Hit import Hit
from parsecore.Scoring.ScoreInfo import ScoreInfo

HEADER = (
    "osu file format v14\n"
    "[General]\nMode: 1\n"
    "[Difficulty]\nCircleSize:4\nApproachRate:9\nOverallDifficulty:{od}\n"
    "SliderMultiplier:1.4\nSliderTickRate:1\n"
    "[TimingPoints]\n0,300,4,2,0,60,1,0\n"
    "[HitObjects]\n"
)


def _beatmap(pattern: str, gap: float = 150.0, od: float = 7.0, mods=None):
    """Return a converted taiko beatmap for a written-out pattern of notes."""
    lines = []
    for i, character in enumerate(pattern):
        sound = 8 if character == "k" else 0
        lines.append(f"256,192,{1000 + int(i * gap)},1,{sound}\n")

    decoded = LegacyBeatmapDecoder.FromText(
        HEADER.format(od=od) + "".join(lines)
    )
    return decoded, WorkingBeatmap(decoded).GetPlayableBeatmap(
        TaikoBeatmapConverter, None, mods or []
    )


def _rate(pattern: str, gap: float = 150.0, od: float = 7.0, mods=None):
    """Return the difficulty attributes of a written-out pattern of notes."""
    mods = mods or []
    _, beatmap = _beatmap(pattern, gap, od, mods)
    return TaikoDifficultyCalculator(beatmap).Calculate(mods)


def test_a_beatmap_is_rated_above_zero():
    """A beatmap with notes in it earns a star rating."""
    attributes = _rate("dkdkdkdkdkdkdkdkdkdk")

    assert attributes.StarRating > 0
    assert attributes.MaxCombo == 20
    assert attributes.MechanicalDifficulty > 0


def test_an_empty_beatmap_is_rated_at_nothing():
    """A beatmap with no objects has no difficulty to report."""
    decoded = LegacyBeatmapDecoder.FromText(HEADER.format(od=7))
    beatmap = WorkingBeatmap(decoded).GetPlayableBeatmap(TaikoBeatmapConverter)

    attributes = TaikoDifficultyCalculator(beatmap).Calculate([])

    assert attributes.StarRating == 0
    assert attributes.MaxCombo == 0


def test_faster_notes_are_rated_higher():
    """The same pattern packed tighter is worth more stars."""
    slow = _rate("dkdkdkdkdkdkdkdkdkdk", gap=300.0)
    fast = _rate("dkdkdkdkdkdkdkdkdkdk", gap=60.0)

    assert fast.StarRating > slow.StarRating


def test_the_skills_add_up_to_the_star_rating():
    """Each reported skill is its share of the finished rating.

    They are rescaled to sum to the star rating rather than reported raw, so
    the four can be read against each other.
    """
    attributes = _rate("ddkkddkkddkkddkkddkk", gap=120.0)

    total = (
        attributes.RhythmDifficulty
        + attributes.ReadingDifficulty
        + attributes.ColourDifficulty
        + attributes.StaminaDifficulty
    )
    assert total == pytest.approx(attributes.StarRating, rel=1e-9)

    assert attributes.MechanicalDifficulty == pytest.approx(
        attributes.ColourDifficulty + attributes.StaminaDifficulty, rel=1e-12
    )


def test_a_single_colour_beatmap_leans_on_mono_stamina():
    """A beatmap that never switches hands scores high on the mono factor."""
    single = _rate("dddddddddddddddddddd", gap=100.0)
    alternating = _rate("dkdkdkdkdkdkdkdkdkdk", gap=100.0)

    assert single.MonoStaminaFactor > alternating.MonoStaminaFactor


def test_double_time_raises_the_rating():
    """Playing a beatmap faster makes it harder."""
    plain = _rate("dkdkdkdkdkdkdkdkdkdk", gap=150.0)
    doubled = _rate("dkdkdkdkdkdkdkdkdkdk", gap=150.0, mods=[ModDoubleTime()])

    assert doubled.StarRating > plain.StarRating


def test_taiko_hard_rock_tightens_timing_and_speeds_the_playfield():
    """Taiko has no circles to shrink, so hard rock works on the other two."""
    from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty

    difficulty = BeatmapDifficulty(
        DrainRate=5, CircleSize=5, OverallDifficulty=5, ApproachRate=5,
        SliderMultiplier=1.4,
    )
    TaikoModHardRock().ApplyToDifficulty(difficulty)

    assert difficulty.OverallDifficulty == pytest.approx(7.0)
    assert difficulty.SliderMultiplier == pytest.approx(1.4 * (1.4 * 4 / 3))
    assert difficulty.CircleSize == 5.0


def test_taiko_easy_loosens_timing_and_slows_the_playfield():
    """Easy halves the accuracy window and slows the scroll."""
    from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty

    difficulty = BeatmapDifficulty(
        DrainRate=6, CircleSize=6, OverallDifficulty=6, ApproachRate=6,
        SliderMultiplier=1.4,
    )
    TaikoModEasy().ApplyToDifficulty(difficulty)

    assert difficulty.OverallDifficulty == pytest.approx(3.0)
    assert difficulty.SliderMultiplier == pytest.approx(1.4 * 0.8)


def _perfect_score(pattern: str, gap: float = 150.0, od: float = 7.0, mods=None):
    """Return the pp a flawless play of a pattern is worth."""
    mods = mods or []
    decoded, beatmap = _beatmap(pattern, gap, od, mods)
    attributes = TaikoDifficultyCalculator(beatmap).Calculate(mods)
    notes = sum(1 for h in beatmap.HitObjects if isinstance(h, Hit))

    score = ScoreInfo(
        Accuracy=1.0,
        MaxCombo=attributes.MaxCombo,
        RulesetID=decoded.BeatmapInfo.RulesetID,
        Statistics={HitResult.Great: notes},
        Mods=mods,
        BeatmapDifficulty=decoded.Difficulty,
    )
    return TaikoPerformanceCalculator().Calculate(score, attributes)


def test_a_flawless_play_earns_performance():
    """Hitting everything on a rated beatmap is worth something."""
    performance = _perfect_score("dkdkdkdkdkdkdkdkdkdk", gap=100.0)

    assert performance.Total > 0
    assert performance.Total == pytest.approx(
        performance.Difficulty + performance.Accuracy, rel=1e-12
    )
    assert performance.EstimatedUnstableRate is not None


def test_missing_everything_is_worth_nothing():
    """A score with no good hits has no timing to read, so it earns nothing."""
    decoded, beatmap = _beatmap("dkdkdkdkdkdkdkdkdkdk")
    attributes = TaikoDifficultyCalculator(beatmap).Calculate([])

    score = ScoreInfo(
        Accuracy=0.0,
        MaxCombo=0,
        RulesetID=1,
        Statistics={HitResult.Miss: 20},
        Mods=[],
        BeatmapDifficulty=decoded.Difficulty,
    )
    performance = TaikoPerformanceCalculator().Calculate(score, attributes)

    assert performance.EstimatedUnstableRate is None
    assert performance.Total == 0


def test_a_tighter_window_reads_as_steadier_timing():
    """The same accuracy on a harder window means the player was more precise.

    Taiko has nothing to aim at, so the whole calculation runs off how steady
    the timing must have been to reach the accuracy the player did.
    """
    loose = _perfect_score("dkdkdkdkdkdkdkdkdkdk", gap=100.0, od=2.0)
    tight = _perfect_score("dkdkdkdkdkdkdkdkdkdk", gap=100.0, od=9.0)

    assert tight.EstimatedUnstableRate < loose.EstimatedUnstableRate
    assert tight.Accuracy > loose.Accuracy
