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
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapConverter import OsuBeatmapConverter
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapProcessor import OsuBeatmapProcessor
from parsecore.Rulesets.Osu.Difficulty.OsuDifficultyCalculator import (
    OsuDifficultyCalculator,
)
from parsecore.Rulesets.Osu.Difficulty.OsuPerformanceCalculator import (
    OsuPerformanceCalculator,
)
from parsecore.Rulesets.Osu.Mods.OsuModAutopilot import OsuModAutopilot
from parsecore.Rulesets.Osu.Mods.OsuModRelax import OsuModRelax
from parsecore.Rulesets.Osu.Scoring.OsuHitWindows import OsuHitWindows
from parsecore.Rulesets.Scoring.HitResult import HitResult
from parsecore.Scoring.ScoreInfo import ScoreInfo


def _prepared(path, mods=None):
    """Return a playable beatmap and its difficulty attributes."""
    decoded = LegacyBeatmapDecoder.FromPath(str(path))
    playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor, mods
    )
    return playable, OsuDifficultyCalculator(playable).Calculate(mods or [])


def _score(playable, attributes, accuracy=1.0, combo=None, misses=0, oks=0, mods=None):
    """Build a score for a beatmap."""
    total = len(playable.HitObjects)
    return ScoreInfo(
        Accuracy=accuracy,
        MaxCombo=attributes.MaxCombo if combo is None else combo,
        Mods=list(mods or []),
        BeatmapDifficulty=playable.Difficulty,
        Statistics={
            HitResult.Great: total - misses - oks,
            HitResult.Ok: oks,
            HitResult.Miss: misses,
            HitResult.SliderTailHit: attributes.SliderCount,
        },
    )


def _osu_files(beatmap_files):
    """Return only the beatmaps written for the osu! ruleset."""
    return [
        p
        for p in beatmap_files
        if LegacyBeatmapDecoder.FromPath(str(p)).BeatmapInfo.RulesetID == 0
    ]


def test_hit_windows_are_floored_and_narrowed():
    """osu! floors each window then subtracts half a millisecond.

    Skipping this rounding shifts the overall difficulty used in performance
    by about 0.08, which moved the accuracy value by over three percent.
    """
    windows = OsuHitWindows()
    windows.SetDifficulty(7)

    assert windows.WindowFor(HitResult.Great) == pytest.approx(37.5)
    assert windows.WindowFor(HitResult.Ok) == pytest.approx(83.5)
    assert windows.WindowFor(HitResult.Meh) == pytest.approx(129.5)

    assert (79.5 - windows.WindowFor(HitResult.Great)) / 6 == pytest.approx(7.0)


def test_perfect_score_scores_something(beatmap_files):
    """A full combo with no mistakes is worth a positive amount."""
    playable, attributes = _prepared(_osu_files(beatmap_files)[0])
    result = OsuPerformanceCalculator().Calculate(
        _score(playable, attributes), attributes
    )

    assert result.Total > 0
    assert result.Aim > 0
    assert result.Speed > 0
    assert result.Accuracy > 0
    assert result.EffectiveMissCount == 0


def test_misses_and_lost_combo_reduce_performance(beatmap_files):
    """A worse score on the same beatmap is worth less."""
    playable, attributes = _prepared(_osu_files(beatmap_files)[0])

    perfect = OsuPerformanceCalculator().Calculate(
        _score(playable, attributes), attributes
    )
    dropped = OsuPerformanceCalculator().Calculate(
        _score(
            playable,
            attributes,
            accuracy=0.97,
            combo=int(attributes.MaxCombo * 0.7),
            misses=3,
            oks=5,
        ),
        attributes,
    )

    assert dropped.Total < perfect.Total
    assert dropped.EffectiveMissCount >= 3


def test_lower_accuracy_is_worth_less(beatmap_files):
    """Accuracy scales the total, so a lower one pays less."""
    playable, attributes = _prepared(_osu_files(beatmap_files)[0])

    high = OsuPerformanceCalculator().Calculate(
        _score(playable, attributes, accuracy=1.0), attributes
    )
    low = OsuPerformanceCalculator().Calculate(
        _score(playable, attributes, accuracy=0.9), attributes
    )
    assert low.Total < high.Total


def test_autopilot_removes_aim_value(beatmap_files):
    """Autopilot aims for the player, so aim pays nothing."""
    path = _osu_files(beatmap_files)[0]
    mods = [OsuModAutopilot()]
    playable, attributes = _prepared(path, mods)

    result = OsuPerformanceCalculator().Calculate(
        _score(playable, attributes, mods=mods), attributes
    )
    assert result.Aim == 0.0


def test_relax_removes_speed_and_accuracy_value(beatmap_files):
    """Relax taps for the player, so speed and accuracy pay nothing."""
    path = _osu_files(beatmap_files)[0]
    mods = [OsuModRelax()]
    playable, attributes = _prepared(path, mods)

    result = OsuPerformanceCalculator().Calculate(
        _score(playable, attributes, mods=mods), attributes
    )
    assert result.Speed == 0.0
    assert result.Accuracy == 0.0


def test_performance_stays_finite_on_every_beatmap(beatmap_files):
    """No beatmap produces an infinite or negative performance value."""
    for path in _osu_files(beatmap_files):
        playable, attributes = _prepared(path)
        result = OsuPerformanceCalculator().Calculate(
            _score(playable, attributes), attributes
        )
        assert math.isfinite(result.Total), path.name
        assert result.Total > 0, path.name
