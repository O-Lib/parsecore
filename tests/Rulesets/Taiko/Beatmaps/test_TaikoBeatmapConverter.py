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
from parsecore.Rulesets.Taiko.Beatmaps.TaikoBeatmapConverter import (
    RequiredSwellHitsPerSecond,
    TaikoBeatmapConverter,
)
from parsecore.Rulesets.Taiko.Objects.DrumRoll import DrumRoll
from parsecore.Rulesets.Taiko.Objects.Hit import Hit
from parsecore.Rulesets.Taiko.Objects.Swell import Swell

HEADER = (
    "osu file format v14\n"
    "[General]\nMode: {mode}\n"
    "[Difficulty]\nCircleSize:4\nApproachRate:9\nOverallDifficulty:8\n"
    "SliderMultiplier:1.4\nSliderTickRate:1\n"
    "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
    "[HitObjects]\n"
)


def _convert(hit_objects: str, mode: int = 1):
    """Decode a beatmap and run it through the taiko conversion pipeline."""
    decoded = LegacyBeatmapDecoder.FromText(HEADER.format(mode=mode) + hit_objects)
    return WorkingBeatmap(decoded).GetPlayableBeatmap(TaikoBeatmapConverter)


def test_each_type_converts_to_its_taiko_object():
    """Circles become notes, spinners become swells, sliders become rolls."""
    beatmap = _convert(
        "100,100,1000,1,0\n"
        "200,200,2000,2,0,L|300:200,1,140\n"
        "256,192,4000,12,0,6000\n"
    )
    assert isinstance(beatmap.HitObjects[0], Hit)
    assert isinstance(beatmap.HitObjects[1], DrumRoll)
    assert isinstance(beatmap.HitObjects[2], Swell)


def test_a_taiko_beatmap_keeps_its_sliders_as_rolls():
    """A beatmap already written for taiko is never broken into notes."""
    beatmap = _convert("200,200,2000,2,0,L|220:200,1,20\n", mode=1)
    assert isinstance(beatmap.HitObjects[0], DrumRoll)


def test_a_short_osu_slider_is_drummed_out_as_notes():
    """A slider from another ruleset becomes notes when it is short enough."""
    beatmap = _convert("200,200,2000,2,0,L|220:200,1,20\n", mode=0)
    assert all(isinstance(h, Hit) for h in beatmap.HitObjects)
    assert len(beatmap.HitObjects) > 1


def test_swell_hits_scale_with_overall_difficulty():
    """A harder beatmap asks for more hits over the same swell."""
    easy = RequiredSwellHitsPerSecond(0.0)
    mid = RequiredSwellHitsPerSecond(5.0)
    hard = RequiredSwellHitsPerSecond(10.0)
    assert easy < mid < hard
    assert mid == pytest.approx(5 * 1.65, rel=1e-6)

    beatmap = _convert("256,192,1000,12,0,3000\n")
    swell = beatmap.HitObjects[0]
    assert swell.RequiredHits == int(swell.Duration / 1000 * RequiredSwellHitsPerSecond(8.0))


def test_simultaneous_mania_notes_collapse_to_one():
    """Taiko has one drum, so notes sharing a moment become a single note."""
    beatmap = _convert(
        "64,192,1000,1,0\n192,192,1000,1,0\n320,192,2000,1,0\n", mode=3
    )
    assert len(beatmap.HitObjects) == 2
    assert [h.StartTime for h in beatmap.HitObjects] == [1000, 2000]
    assert beatmap.HitObjects[0].IsStrong
    assert not beatmap.HitObjects[1].IsStrong
