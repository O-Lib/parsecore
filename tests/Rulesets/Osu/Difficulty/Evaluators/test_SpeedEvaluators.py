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
from parsecore.Rulesets.Osu.Difficulty.Evaluators.Speed import (
    RhythmEvaluator,
    SpeedEvaluator,
)
from parsecore.Rulesets.Osu.Difficulty.Preprocessing.OsuDifficultyHitObject import (
    OsuDifficultyHitObject,
)


def _header(overall_difficulty: float = 8.0) -> str:
    """Return a beatmap header at a given overall difficulty."""
    return (
        "osu file format v14\n"
        "[General]\nMode: 0\n"
        f"[Difficulty]\nCircleSize:4\nApproachRate:9\n"
        f"OverallDifficulty:{overall_difficulty}\n"
        "SliderMultiplier:1.4\nSliderTickRate:1\n"
        "[TimingPoints]\n0,300,4,2,0,60,1,0\n"
        "[HitObjects]\n"
    )


def _objects(hit_object_lines: str, overall_difficulty: float = 8.0):
    """Build difficulty objects from raw hit-object lines."""
    decoded = LegacyBeatmapDecoder.FromText(
        _header(overall_difficulty) + hit_object_lines
    )
    playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor
    )
    objects: list[OsuDifficultyHitObject] = []
    for i in range(1, len(playable.HitObjects)):
        objects.append(
            OsuDifficultyHitObject(
                playable.HitObjects[i],
                playable.HitObjects[i - 1],
                1.0,
                objects,
                len(objects),
            )
        )
    return objects


def _stream(interval: int, count: int = 12, spacing: int = 60) -> str:
    """Return evenly spaced circles at a fixed rhythm."""
    return "".join(
        f"{60 + (i % 5) * spacing},100,{1000 + i * interval},1,0\n"
        for i in range(count)
    )




def test_faster_streams_are_harder_to_tap():
    """Halving the gap between objects raises the tap difficulty."""
    slow = _objects(_stream(250))
    fast = _objects(_stream(90))
    assert SpeedEvaluator.EvaluateDifficultyOf(
        fast[-2]
    ) > SpeedEvaluator.EvaluateDifficultyOf(slow[-2])


def test_spinners_are_not_tapped():
    """A spinner earns no speed difficulty."""
    objects = _objects(
        "100,100,1000,1,0\n200,100,1150,1,0\n256,192,1300,12,0,3000\n"
    )
    assert SpeedEvaluator.EvaluateDifficultyOf(objects[-1]) == 0.0


def test_hit_window_matches_the_osu_formula():
    """The great window is ``80 - 6 * OD``, floored and narrowed by half a ms.

    osu! applies ``floor(range) - 0.5`` so that the overall difficulty can be
    recovered exactly as ``(79.5 - window) / 6``.
    """
    for overall_difficulty, window in ((0, 79.5), (5, 49.5), (8, 31.5), (10, 19.5)):
        objects = _objects(_stream(200), overall_difficulty=overall_difficulty)
        assert objects[0].HitWindowGreat == pytest.approx(2 * window)
        assert (79.5 - window) / 6 == pytest.approx(overall_difficulty)




def test_rhythm_multiplier_is_never_below_one():
    """The rhythm multiplier starts at one and only ever adds difficulty."""
    objects = _objects(_stream(150))
    for obj in objects:
        assert RhythmEvaluator.EvaluateDifficultyOf(obj) >= 1.0


def test_constant_rhythm_earns_little():
    """An unchanging rhythm is worth less than one that keeps changing."""
    steady = _objects(_stream(150, count=16))

    varied_lines = ""
    time = 1000
    for i in range(16):
        varied_lines += f"{60 + (i % 5) * 60},100,{time},1,0\n"
        time += 150 if i % 2 else 260
    varied = _objects(varied_lines)

    steady_sum = sum(RhythmEvaluator.EvaluateDifficultyOf(o) for o in steady)
    varied_sum = sum(RhythmEvaluator.EvaluateDifficultyOf(o) for o in varied)
    assert varied_sum > steady_sum


def test_rhythm_spinner_scores_nothing():
    """A spinner has no rhythm of its own."""
    objects = _objects(
        "100,100,1000,1,0\n200,100,1150,1,0\n256,192,1300,12,0,3000\n"
    )
    assert RhythmEvaluator.EvaluateDifficultyOf(objects[-1]) == 0.0


def test_speed_and_rhythm_stay_finite_on_real_beatmaps(beatmap_files):
    """Neither evaluator produces an infinite or negative value."""
    for path in beatmap_files:
        decoded = LegacyBeatmapDecoder.FromPath(str(path))
        if decoded.BeatmapInfo.RulesetID != 0:
            continue
        playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
            OsuBeatmapConverter, OsuBeatmapProcessor
        )
        objects: list[OsuDifficultyHitObject] = []
        for i in range(1, len(playable.HitObjects)):
            objects.append(
                OsuDifficultyHitObject(
                    playable.HitObjects[i],
                    playable.HitObjects[i - 1],
                    1.0,
                    objects,
                    len(objects),
                )
            )
        for obj in objects:
            speed = SpeedEvaluator.EvaluateDifficultyOf(obj)
            rhythm = RhythmEvaluator.EvaluateDifficultyOf(obj)
            assert math.isfinite(speed) and speed >= 0
            assert math.isfinite(rhythm) and rhythm >= 0
