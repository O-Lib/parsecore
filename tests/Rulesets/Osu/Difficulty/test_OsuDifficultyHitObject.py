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
from parsecore.Rulesets.Osu.Difficulty.Preprocessing.OsuDifficultyHitObject import (
    MIN_DELTA_TIME,
    NORMALISED_RADIUS,
    OsuDifficultyHitObject,
)
from parsecore.Rulesets.Osu.Objects.Slider import Slider


def _difficulty_objects(text: str, clock_rate: float = 1.0):
    """Build the difficulty object list for a beatmap."""
    decoded = LegacyBeatmapDecoder.FromText(text)
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


TWO_CIRCLES = (
    "osu file format v14\n"
    "[General]\nMode: 0\n"
    "[Difficulty]\nCircleSize:5\nApproachRate:5\nOverallDifficulty:5\n"
    "SliderMultiplier:1.4\nSliderTickRate:1\n"
    "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
    "[HitObjects]\n100,100,1000,1,0\n200,100,1500,1,0\n"
)

FOUR_CIRCLES_RIGHT_ANGLE = (
    "osu file format v14\n"
    "[General]\nMode: 0\n"
    "[Difficulty]\nCircleSize:5\nApproachRate:5\nOverallDifficulty:5\n"
    "SliderMultiplier:1.4\nSliderTickRate:1\n"
    "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
    "[HitObjects]\n"
    "50,50,500,1,0\n"
    "100,100,1000,1,0\n"
    "200,100,1500,1,0\n"
    "200,200,2000,1,0\n"
)


def test_distance_is_normalised_to_radius_fifty():
    """A jump of one circle diameter measures one normalised diameter."""
    objects = _difficulty_objects(TWO_CIRCLES)
    circle = objects[0].BaseObject
    expected = 100 * (NORMALISED_RADIUS / circle.Radius)
    assert objects[0].LazyJumpDistance == pytest.approx(expected, rel=1e-6)


def test_delta_time_respects_the_clock_rate():
    """A faster clock rate shortens the time between objects."""
    normal = _difficulty_objects(TWO_CIRCLES)
    fast = _difficulty_objects(TWO_CIRCLES, clock_rate=1.5)
    assert normal[0].DeltaTime == pytest.approx(500)
    assert fast[0].DeltaTime == pytest.approx(500 / 1.5)


def test_delta_time_never_falls_below_the_minimum():
    """Simultaneous objects are held apart so no division by zero occurs."""
    stacked = (
        "osu file format v14\n[General]\nMode: 0\n"
        "[Difficulty]\nCircleSize:5\nApproachRate:5\nOverallDifficulty:5\n"
        "SliderMultiplier:1.4\nSliderTickRate:1\n"
        "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
        "[HitObjects]\n100,100,1000,1,0\n300,300,1000,1,0\n"
    )
    objects = _difficulty_objects(stacked)
    assert objects[0].AdjustedDeltaTime == MIN_DELTA_TIME


def test_right_angle_pattern_measures_ninety_degrees():
    """Objects forming a right angle report a right angle."""
    objects = _difficulty_objects(FOUR_CIRCLES_RIGHT_ANGLE)
    assert objects[2].Angle is not None
    assert math.degrees(objects[2].Angle) == pytest.approx(90.0, abs=1e-6)


def test_angles_need_two_preceding_objects():
    """The first two difficulty objects cannot form an angle yet."""
    objects = _difficulty_objects(FOUR_CIRCLES_RIGHT_ANGLE)
    assert objects[0].Angle is None
    assert objects[1].Angle is None


def test_slider_tracks_cursor_travel():
    """A slider reports how far the cursor must travel along it."""
    with_slider = (
        "osu file format v14\n[General]\nMode: 0\n"
        "[Difficulty]\nCircleSize:5\nApproachRate:5\nOverallDifficulty:5\n"
        "SliderMultiplier:1.4\nSliderTickRate:1\n"
        "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
        "[HitObjects]\n"
        "50,50,1000,1,0\n"
        "100,100,2000,2,0,L|300:100,1,200\n"
    )
    objects = _difficulty_objects(with_slider)
    slider_object = next(o for o in objects if isinstance(o.BaseObject, Slider))
    assert slider_object.LazyTravelDistance > 0
    assert slider_object.TravelTime >= MIN_DELTA_TIME
    assert slider_object.LazyEndPosition is not None


def test_small_circle_bonus_only_applies_below_thirty():
    """Circles larger than 30 units get no small-circle bonus."""
    objects = _difficulty_objects(TWO_CIRCLES)
    assert objects[0].SmallCircleBonus == pytest.approx(1.0)
