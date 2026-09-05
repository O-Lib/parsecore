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
from parsecore.Rulesets.Difficulty.DifficultyCalculator import DifficultyCalculator
from parsecore.Rulesets.Mods.ModDoubleTime import ModDoubleTime
from parsecore.Rulesets.Mods.ModEasy import ModEasy
from parsecore.Rulesets.Mods.ModHalfTime import ModHalfTime
from parsecore.Rulesets.Mods.ModHardRock import ADJUST_RATIO, ModHardRock
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapConverter import OsuBeatmapConverter
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapProcessor import OsuBeatmapProcessor
from parsecore.Rulesets.Osu.Mods.OsuModEasy import OsuModEasy
from parsecore.Rulesets.Osu.Mods.OsuModHardRock import (
    CIRCLE_SIZE_RATIO,
    OsuModHardRock,
)
from parsecore.Rulesets.Osu.Mods.OsuModHidden import OsuModHidden
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Utils.Vector2 import Vector2, f32


def test_rate_mods_change_the_clock_rate():
    """Rate mods multiply the clock rate the calculator uses."""
    assert DifficultyCalculator.GetClockRate([]) == pytest.approx(1.0)
    assert DifficultyCalculator.GetClockRate([ModDoubleTime()]) == pytest.approx(1.5)
    assert DifficultyCalculator.GetClockRate([ModHalfTime()]) == pytest.approx(0.75)


def test_hard_rock_base_only_raises_the_drain_rate():
    """The shared hard rock only touches HP; the rest belongs to each ruleset."""
    difficulty = BeatmapDifficulty(
        DrainRate=5, CircleSize=5, OverallDifficulty=5, ApproachRate=5
    )
    ModHardRock().ApplyToDifficulty(difficulty)

    assert difficulty.DrainRate == pytest.approx(7.0)
    assert difficulty.CircleSize == 5.0
    assert difficulty.OverallDifficulty == 5.0
    assert difficulty.ApproachRate == 5.0


def test_osu_hard_rock_raises_difficulty_and_caps_at_ten():
    """Hard rock scales every setting for osu! and never exceeds ten."""
    difficulty = BeatmapDifficulty(
        DrainRate=5, CircleSize=5, OverallDifficulty=5, ApproachRate=5
    )
    OsuModHardRock().ApplyToDifficulty(difficulty)

    assert difficulty.OverallDifficulty == pytest.approx(7.0)
    assert difficulty.ApproachRate == pytest.approx(7.0)
    assert difficulty.DrainRate == pytest.approx(7.0)
    assert difficulty.CircleSize == pytest.approx(6.5)

    maxed = BeatmapDifficulty(
        DrainRate=9, CircleSize=9, OverallDifficulty=9, ApproachRate=9
    )
    OsuModHardRock().ApplyToDifficulty(maxed)
    assert maxed.OverallDifficulty == 10.0
    assert maxed.ApproachRate == 10.0


def test_osu_hard_rock_mirrors_the_playfield():
    """Hard rock flips every object across the middle of the playfield."""
    circle = HitCircle(1000.0, Vector2(120, 100))
    OsuModHardRock().ApplyToHitObject(circle)

    assert circle.Position == Vector2(120, 284)


def test_osu_hard_rock_mirrors_a_slider_and_its_nested_objects():
    """A mirrored slider keeps its length and drags its ticks along."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n[General]\nMode: 0\n"
        "[Difficulty]\nCircleSize:4\nApproachRate:9\nOverallDifficulty:8\n"
        "SliderMultiplier:1.6\nSliderTickRate:2\n"
        "[TimingPoints]\n0,300,4,2,0,60,1,0\n"
        "[HitObjects]\n100,100,1000,2,0,L|100:260,1,160\n"
    )
    playable = WorkingBeatmap(beatmap).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor
    )
    slider = playable.HitObjects[0]
    length_before = slider.Path.Distance
    nested_before = [n.Position for n in slider.NestedHitObjects]
    assert len(nested_before) > 2, "expected the slider to place ticks"

    OsuModHardRock().ApplyToHitObject(slider)

    assert slider.Position == Vector2(100, 284)
    assert slider.Path.Distance == pytest.approx(length_before)

    for before, nested in zip(
        nested_before, slider.NestedHitObjects, strict=True
    ):
        assert nested.Position != before
        assert nested.Position.Y == pytest.approx(384 - before.Y)


def test_easy_base_leaves_the_accuracy_window_alone():
    """The shared easy halves what every ruleset has; each adds its own.

    osu! keeps the accuracy window out of the shared mod because the rulesets
    read it differently, so the base must not touch it.
    """
    difficulty = BeatmapDifficulty(
        DrainRate=6, CircleSize=6, OverallDifficulty=6, ApproachRate=6
    )
    ModEasy().ApplyToDifficulty(difficulty)

    assert difficulty.CircleSize == pytest.approx(3.0)
    assert difficulty.ApproachRate == pytest.approx(3.0)
    assert difficulty.DrainRate == pytest.approx(3.0)
    assert difficulty.OverallDifficulty == 6.0


def test_osu_easy_halves_the_accuracy_window_too():
    """osu!'s easy adds the accuracy window to what the shared mod halves."""
    difficulty = BeatmapDifficulty(
        DrainRate=6, CircleSize=6, OverallDifficulty=6, ApproachRate=6
    )
    OsuModEasy().ApplyToDifficulty(difficulty)

    assert difficulty.CircleSize == pytest.approx(3.0)
    assert difficulty.OverallDifficulty == pytest.approx(3.0)


def test_hard_rock_ratios_are_single_precision():
    """The scaling ratios are the ``float`` values osu! writes, not exact ones.

    ``1.4f`` and ``1.3f`` are both a shade below their decimal spelling, and
    that shade reaches the object scale, so circle size 7 must land on the same
    value osu! computes rather than on a clean 9.1.
    """
    assert ADJUST_RATIO == f32(1.4)
    assert ADJUST_RATIO != 1.4
    assert CIRCLE_SIZE_RATIO == f32(1.3)
    assert CIRCLE_SIZE_RATIO != 1.3

    difficulty = BeatmapDifficulty(CircleSize=7, ApproachRate=5)
    OsuModHardRock().ApplyToDifficulty(difficulty)

    assert difficulty.CircleSize == 9.09999942779541
    assert difficulty.CircleSize != f32(9.1)


def test_hidden_shortens_the_fade_in():
    """Hidden rewrites how long every object takes to fade in.

    The difficulty calculation reads ``TimeFadeIn`` when deciding whether an
    object is invisible, so leaving it at its default understates hidden.
    """
    playable = _playable_slider_map()
    hit_objects = playable.HitObjects
    before = [o.TimeFadeIn for o in hit_objects]

    OsuModHidden().ApplyToBeatmap(playable)

    circle = next(o for o in hit_objects if isinstance(o, HitCircle))
    assert circle.TimeFadeIn == circle.TimePreempt * 0.4
    assert circle.TimeFadeIn != before[hit_objects.index(circle)]

    slider = next(o for o in hit_objects if isinstance(o, Slider))
    assert slider.TimeFadeIn == before[hit_objects.index(slider)]

    for nested in slider.NestedHitObjects:
        assert nested.TimeFadeIn == nested.TimePreempt * 0.4


def _playable_slider_map():
    """Return a converted beatmap holding one circle and one slider."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n[General]\nMode: 0\n"
        "[Difficulty]\nCircleSize:4\nApproachRate:9\nOverallDifficulty:8\n"
        "SliderMultiplier:1.6\nSliderTickRate:2\n"
        "[TimingPoints]\n0,300,4,2,0,60,1,0\n"
        "[HitObjects]\n100,100,1000,1,0\n100,100,2000,2,0,L|300:100,1,160\n"
    )
    return WorkingBeatmap(beatmap).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor
    )


def test_mods_compare_by_type():
    """Two instances of the same mod are equal."""
    assert ModDoubleTime() == ModDoubleTime()
    assert ModDoubleTime() != ModHalfTime()
    assert len({ModDoubleTime(), ModDoubleTime(), ModHalfTime()}) == 2
