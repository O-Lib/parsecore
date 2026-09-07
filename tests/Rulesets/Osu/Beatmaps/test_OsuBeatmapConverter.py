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
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapConverter import OsuBeatmapConverter
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapProcessor import OsuBeatmapProcessor
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.SliderHeadCircle import SliderHeadCircle
from parsecore.Rulesets.Osu.Objects.SliderTailCircle import SliderTailCircle
from parsecore.Rulesets.Osu.Objects.Spinner import BONUS_SPINS_GAP, Spinner
from parsecore.Rulesets.Osu.Objects.SpinnerTick import SpinnerBonusTick, SpinnerTick

SIMPLE_MAP = (
    "osu file format v14\n"
    "[General]\nMode: 0\nStackLeniency: 0.7\n"
    "[Difficulty]\nCircleSize:4\nApproachRate:9\nOverallDifficulty:8\n"
    "SliderMultiplier:1.4\nSliderTickRate:1\n"
    "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
    "[HitObjects]\n"
    "100,100,1000,1,0\n"
    "200,200,2000,2,0,L|300:200,1,140\n"
    "256,192,3000,12,0,5000\n"
)


def _convert(text: str):
    """Decode a beatmap and run it through the osu! conversion pipeline."""
    decoded = LegacyBeatmapDecoder.FromText(text)
    return WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor
    )


def test_each_type_converts_to_its_osu_object():
    """Circles, sliders and spinners map onto their osu! counterparts."""
    beatmap = _convert(SIMPLE_MAP)
    assert isinstance(beatmap.HitObjects[0], HitCircle)
    assert isinstance(beatmap.HitObjects[1], Slider)
    assert isinstance(beatmap.HitObjects[2], Spinner)


def test_slider_velocity_follows_beat_length():
    """Slider velocity is the scoring distance over the beat length."""
    beatmap = _convert(SIMPLE_MAP)
    slider = beatmap.HitObjects[1]
    assert slider.Velocity == pytest.approx(100 * 1.4 / 500)


def test_slider_generates_head_and_tail():
    """A slider always nests at least a head and a tail."""
    beatmap = _convert(SIMPLE_MAP)
    nested = beatmap.HitObjects[1].NestedHitObjects
    assert any(isinstance(n, SliderHeadCircle) for n in nested)
    assert any(isinstance(n, SliderTailCircle) for n in nested)


def test_spinner_generates_spin_ticks():
    """A spinner nests a tick per spin, plus the gap before the bonus ones."""
    beatmap = _convert(SIMPLE_MAP)
    spinner = beatmap.HitObjects[2]
    assert spinner.SpinsRequired > 0
    assert len(spinner.NestedHitObjects) == (
        spinner.SpinsRequired + spinner.MaximumBonusSpins + BONUS_SPINS_GAP
    )
    assert spinner.SpinsRequiredForBonus == spinner.SpinsRequired + BONUS_SPINS_GAP
    plain = sum(
        1
        for n in spinner.NestedHitObjects
        if isinstance(n, SpinnerTick) and not isinstance(n, SpinnerBonusTick)
    )
    assert plain == spinner.SpinsRequiredForBonus


def test_every_bundled_osu_beatmap_converts(beatmap_files):
    """Every bundled osu! beatmap converts and post-processes cleanly."""
    converted_any = False
    for path in beatmap_files:
        decoded = LegacyBeatmapDecoder.FromPath(str(path))
        if decoded.BeatmapInfo.RulesetID != 0:
            continue
        converted = WorkingBeatmap(decoded).GetPlayableBeatmap(
            OsuBeatmapConverter, OsuBeatmapProcessor
        )
        assert converted.HitObjects
        converted_any = True
    assert converted_any, "no osu! beatmaps among the test files"


def test_combo_indices_are_assigned():
    """The first object starts a combo and indices advance within it."""
    beatmap = _convert(SIMPLE_MAP)
    assert beatmap.HitObjects[0].NewCombo is True
    assert beatmap.HitObjects[0].IndexInCurrentCombo == 0
    assert beatmap.HitObjects[1].IndexInCurrentCombo == 1
