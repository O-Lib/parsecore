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
from parsecore.Rulesets.Objects.Legacy.ConvertHitCircle import ConvertHitCircle
from parsecore.Rulesets.Objects.Legacy.ConvertSlider import ConvertSlider


def _raw_hit_object_lines(path) -> list[str]:
    """Return the raw ``[HitObjects]`` lines of a file."""
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    starts = [n for n, line in enumerate(lines) if line.strip() == "[HitObjects]"]
    if not starts:
        return []
    return [
        line
        for line in lines[starts[0] + 1:]
        if line.strip() and not line.lstrip().startswith("//")
    ]


def test_every_beatmap_decodes(beatmap_files):
    """Every bundled beatmap decodes without error and has objects."""
    assert beatmap_files, "no test beatmaps found"
    for path in beatmap_files:
        beatmap = LegacyBeatmapDecoder.FromPath(str(path))
        assert beatmap.HitObjects, f"{path.name} decoded to no hit objects"


def test_hit_object_count_matches_file(beatmap_files):
    """No hit object is silently dropped while decoding."""
    for path in beatmap_files:
        expected = len(_raw_hit_object_lines(path))
        beatmap = LegacyBeatmapDecoder.FromPath(str(path))
        assert len(beatmap.HitObjects) == expected, path.name


def test_hit_objects_are_time_ordered(beatmap_files):
    """Decoded objects come back in ascending start-time order."""
    for path in beatmap_files:
        beatmap = LegacyBeatmapDecoder.FromPath(str(path))
        times = [h.StartTime for h in beatmap.HitObjects]
        assert times == sorted(times), path.name


def test_approach_rate_falls_back_to_overall_difficulty():
    """A file without an ``ApproachRate`` line uses its overall difficulty."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n"
        "[Difficulty]\n"
        "OverallDifficulty:7\n"
        "[HitObjects]\n"
        "256,192,1000,1,0\n"
    )
    assert beatmap.Difficulty.ApproachRate == 7.0


def test_explicit_approach_rate_is_kept():
    """An explicit ``ApproachRate`` is not overwritten by overall difficulty."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n"
        "[Difficulty]\n"
        "ApproachRate:9\n"
        "OverallDifficulty:7\n"
        "[HitObjects]\n"
        "256,192,1000,1,0\n"
    )
    assert beatmap.Difficulty.ApproachRate == 9.0


def test_early_format_applies_timing_offset():
    """Files before format v5 shift every time by 24 ms."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v4\n[HitObjects]\n256,192,1000,1,0\n"
    )
    assert beatmap.HitObjects[0].StartTime == 1024.0


def test_modern_format_applies_no_offset():
    """Files from format v5 onward keep their times unchanged."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n[HitObjects]\n256,192,1000,1,0\n"
    )
    assert beatmap.HitObjects[0].StartTime == 1000.0


def test_spinner_is_not_swallowed_by_combo_offset():
    """A spinner with a new-combo flag decodes as a spinner."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n[HitObjects]\n256,192,27390,12,6,29168\n"
    )
    assert len(beatmap.HitObjects) == 1
    assert beatmap.HitObjects[0].GetEndTime() == 29168


def test_slider_uses_declared_length():
    """A slider's path is trimmed to the length declared in the file."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n"
        "[Difficulty]\nSliderMultiplier:1.4\n"
        "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
        "[HitObjects]\n0,0,1000,2,0,L|100:0,1,70\n"
    )
    slider = beatmap.HitObjects[0]
    assert isinstance(slider, ConvertSlider)
    assert slider.Path.Distance == pytest.approx(70.0)


def test_hit_circle_position_is_read():
    """A hit circle keeps the position written in the file."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n[HitObjects]\n123,45,1000,1,0\n"
    )
    circle = beatmap.HitObjects[0]
    assert isinstance(circle, ConvertHitCircle)
    assert (circle.X, circle.Y) == (123, 45)


def test_breaks_are_read():
    """Break periods in the events section are collected."""
    beatmap = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n[Events]\n2,1000,2000\n[HitObjects]\n0,0,1,1,0\n"
    )
    assert len(beatmap.Breaks) == 1
    assert beatmap.Breaks[0].Duration == 1000
