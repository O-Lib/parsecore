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
from parsecore.Rulesets.Osu.Difficulty.Evaluators.Aim import (
    AgilityEvaluator,
    FlowAimEvaluator,
    SnapAimEvaluator,
)
from parsecore.Rulesets.Osu.Difficulty.Preprocessing.OsuDifficultyHitObject import (
    OsuDifficultyHitObject,
)

HEADER = (
    "osu file format v14\n"
    "[General]\nMode: 0\n"
    "[Difficulty]\nCircleSize:4\nApproachRate:9\nOverallDifficulty:8\n"
    "SliderMultiplier:1.4\nSliderTickRate:1\n"
    "[TimingPoints]\n0,300,4,2,0,60,1,0\n"
    "[HitObjects]\n"
)


def _objects(hit_object_lines: str, clock_rate: float = 1.0):
    """Build difficulty objects from raw hit-object lines."""
    decoded = LegacyBeatmapDecoder.FromText(HEADER + hit_object_lines)
    playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor
    )
    objects: list[OsuDifficultyHitObject] = []
    for i in range(1, len(playable.HitObjects)):
        objects.append(
            OsuDifficultyHitObject(
                playable.HitObjects[i],
                playable.HitObjects[i - 1],
                clock_rate,
                objects,
                len(objects),
            )
        )
    return objects


def _stream(spacing: int, count: int = 8, interval: int = 150) -> str:
    """Return evenly spaced circles along the x axis."""
    return "".join(
        f"{60 + i * spacing},100,{1000 + i * interval},1,0\n" for i in range(count)
    )




def test_evaluators_ignore_the_first_objects():
    """No aim evaluator scores before two objects have been seen."""
    objects = _objects(_stream(80))
    for index in (0, 1):
        assert SnapAimEvaluator.EvaluateDifficultyOf(objects[index], True) == 0.0
        assert FlowAimEvaluator.EvaluateDifficultyOf(objects[index], True) == 0.0


def test_spinners_score_no_aim():
    """A spinner is not aimed, so it earns nothing."""
    objects = _objects(
        "100,100,1000,1,0\n"
        "200,100,1300,1,0\n"
        "300,100,1600,1,0\n"
        "256,192,1900,12,0,3000\n"
    )
    spinner_object = objects[-1]
    assert AgilityEvaluator.EvaluateDifficultyOf(spinner_object) == 0.0
    assert SnapAimEvaluator.EvaluateDifficultyOf(spinner_object, True) == 0.0
    assert FlowAimEvaluator.EvaluateDifficultyOf(spinner_object, True) == 0.0


def test_all_evaluators_stay_finite_and_positive(beatmap_files):
    """Real beatmaps never produce negative or infinite aim values."""
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
            for value in (
                AgilityEvaluator.EvaluateDifficultyOf(obj),
                SnapAimEvaluator.EvaluateDifficultyOf(obj, True),
                FlowAimEvaluator.EvaluateDifficultyOf(obj, True),
            ):
                assert math.isfinite(value)
                assert value >= 0




def test_agility_rises_as_the_rhythm_speeds_up():
    """The same spacing played faster is harder to move through."""
    slow = _objects(_stream(80, interval=300))
    fast = _objects(_stream(80, interval=100))
    assert AgilityEvaluator.EvaluateDifficultyOf(
        fast[-1]
    ) > AgilityEvaluator.EvaluateDifficultyOf(slow[-1])


def test_agility_caps_the_distance_it_rewards():
    """Beyond the distance cap, agility stops growing with spacing."""
    far = _objects(_stream(300))
    further = _objects(_stream(500))
    assert AgilityEvaluator.EvaluateDifficultyOf(
        further[-1]
    ) == pytest.approx(AgilityEvaluator.EvaluateDifficultyOf(far[-1]))




def test_snap_rises_with_spacing():
    """Wider jumps are harder to snap to."""
    close = _objects(_stream(40))
    far = _objects(_stream(200))
    assert SnapAimEvaluator.EvaluateDifficultyOf(
        far[-1], True
    ) > SnapAimEvaluator.EvaluateDifficultyOf(close[-1], True)


def test_angle_acuteness_and_wideness_are_opposites():
    """Acuteness falls exactly where wideness rises."""
    assert SnapAimEvaluator.CalcAngleAcuteness(math.radians(30)) == pytest.approx(1.0)
    assert SnapAimEvaluator.CalcAngleAcuteness(math.radians(180)) == pytest.approx(0.0)
    assert SnapAimEvaluator._calc_angle_wideness(math.radians(180)) == pytest.approx(1.0)
    assert SnapAimEvaluator._calc_angle_wideness(math.radians(30)) == pytest.approx(0.0)




def test_flow_ignores_spacing_below_one_radius():
    """Objects closer than a radius need no real movement, so flow is tiny."""
    stacked = _objects(_stream(2))
    spread = _objects(_stream(120))
    assert FlowAimEvaluator.EvaluateDifficultyOf(
        stacked[-1], True
    ) < FlowAimEvaluator.EvaluateDifficultyOf(spread[-1], True)


def test_slider_travel_can_be_excluded():
    """Turning off slider travel changes what the evaluators measure."""
    with_slider = (
        "100,100,1000,1,0\n"
        "200,100,1300,1,0\n"
        "300,100,1600,2,0,L|400:100,1,100\n"
        "100,200,2200,1,0\n"
    )
    objects = _objects(with_slider)
    last = objects[-1]
    assert SnapAimEvaluator.EvaluateDifficultyOf(
        last, True
    ) != SnapAimEvaluator.EvaluateDifficultyOf(last, False)
