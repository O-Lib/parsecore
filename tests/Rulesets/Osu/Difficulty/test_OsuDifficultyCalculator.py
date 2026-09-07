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

import math

import pytest

from parsecore.Beatmaps.Formats.LegacyBeatmapDecoder import LegacyBeatmapDecoder
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Mods.ModDoubleTime import ModDoubleTime
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapConverter import OsuBeatmapConverter
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapProcessor import OsuBeatmapProcessor
from parsecore.Rulesets.Osu.Difficulty.OsuDifficultyCalculator import (
    OsuDifficultyCalculator,
    SumCognitionDifficulty,
)
from parsecore.Rulesets.Osu.Mods.OsuModFlashlight import OsuModFlashlight


def _attributes(path, mods=None):
    """Return the difficulty attributes of a beatmap file."""
    decoded = LegacyBeatmapDecoder.FromPath(str(path))
    playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor, mods
    )
    return OsuDifficultyCalculator(playable).Calculate(mods or [])


def _osu_files(beatmap_files):
    """Return only the beatmaps written for the osu! ruleset."""
    return [
        p
        for p in beatmap_files
        if LegacyBeatmapDecoder.FromPath(str(p)).BeatmapInfo.RulesetID == 0
    ]


def test_bpm_helpers_default_to_quarter_notes():
    """The BPM helpers use a 1/4 delimiter, as osu! does.

    This defaulted to whole beats at one point, which made every note under
    300 ms earn the high-BPM speed bonus instead of only those under 75 ms,
    and inflated speed difficulty roughly fifteenfold.
    """
    assert DiffUtils.BPMToMilliseconds(200) == pytest.approx(75.0)
    assert DiffUtils.MillisecondsToBPM(75) == pytest.approx(200.0)

    assert DiffUtils.BPMToMilliseconds(200, 1) == pytest.approx(300.0)


def test_pow_matches_dotnet_semantics():
    """``Pow`` follows ``Math.Pow`` rather than guarding against zero."""
    assert DiffUtils.Pow(5, 0) == 1.0
    assert DiffUtils.Pow(0, 0) == 1.0
    assert DiffUtils.Pow(0, 0.9) == 0.0
    assert DiffUtils.Pow(-2, 2) == 4.0


def test_every_osu_beatmap_gets_a_plausible_star_rating(beatmap_files):
    """Every bundled osu! beatmap rates within the range real maps occupy."""
    files = _osu_files(beatmap_files)
    assert files, "no osu! beatmaps among the test files"

    for path in files:
        attributes = _attributes(path)
        assert math.isfinite(attributes.StarRating)
        assert 0 < attributes.StarRating < 15, f"{path.name}: {attributes.StarRating}"
        assert attributes.MaxCombo > 0


def test_star_rating_components_are_populated(beatmap_files):
    """The attributes carry a breakdown, not just a total."""
    path = _osu_files(beatmap_files)[0]
    attributes = _attributes(path)

    assert attributes.AimDifficulty > 0
    assert attributes.SpeedDifficulty > 0
    assert attributes.SliderFactor > 0
    assert attributes.HitCircleCount + attributes.SliderCount > 0


def test_flashlight_only_counts_with_the_mod(beatmap_files):
    """Flashlight difficulty stays zero unless the mod is applied."""
    path = _osu_files(beatmap_files)[0]

    assert _attributes(path).FlashlightDifficulty == 0.0
    assert _attributes(path, [OsuModFlashlight()]).FlashlightDifficulty > 0


def test_rate_increasing_mods_raise_the_star_rating(beatmap_files):
    """Double time makes a beatmap harder."""
    path = _osu_files(beatmap_files)[0]
    assert _attributes(path, [ModDoubleTime()]).StarRating > _attributes(
        path
    ).StarRating


def test_cognition_falls_back_to_whichever_side_is_present():
    """With only one of reading or flashlight, that value passes through."""
    assert SumCognitionDifficulty(0, 5) == 5
    assert SumCognitionDifficulty(5, 0) == 5
    assert SumCognitionDifficulty(5, 5) > 5


def test_empty_beatmap_has_no_difficulty():
    """A beatmap without objects rates zero rather than failing."""
    decoded = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n[General]\nMode: 0\n[HitObjects]\n"
    )
    playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor
    )
    assert OsuDifficultyCalculator(playable).Calculate([]).StarRating == 0.0
