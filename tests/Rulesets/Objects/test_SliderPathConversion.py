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
from parsecore.Rulesets.Objects.Legacy.ConvertSlider import ConvertSlider
from parsecore.Rulesets.Objects.Types.PathType import (
    BEZIER,
    CATMULL,
    LINEAR,
    PERFECT_CURVE,
    PathType,
    SplineType,
)


def _slider(hit_object_line: str, version: int = 14) -> ConvertSlider:
    """Decode a single slider from a hit-object line."""
    beatmap = LegacyBeatmapDecoder.FromText(
        f"osu file format v{version}\n"
        "[General]\nMode: 0\n"
        "[Difficulty]\nSliderMultiplier:1.4\nSliderTickRate:1\n"
        "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
        f"[HitObjects]\n{hit_object_line}\n"
    )
    return beatmap.HitObjects[0]


def test_curve_letters_map_to_their_types():
    """Each legacy curve letter selects the matching path type."""
    assert PathType.from_legacy("L") == LINEAR
    assert PathType.from_legacy("P") == PERFECT_CURVE
    assert PathType.from_legacy("B") == BEZIER
    assert PathType.from_legacy("C") == CATMULL


def test_unknown_curve_letter_falls_back_to_catmull():
    """osu! treats anything unrecognised as catmull, not bezier."""
    assert PathType.from_legacy("X") == CATMULL
    assert PathType.from_legacy("") == CATMULL


def test_bezier_can_carry_a_bspline_degree():
    """``B3`` declares a B-spline of degree three."""
    parsed = PathType.from_legacy("B3")
    assert parsed.type == SplineType.BSpline
    assert parsed.degree == 3


def test_repeated_control_point_starts_a_new_segment():
    """Two identical consecutive points split the path in two.

    This is a red anchor in the editor. Treating the points as one continuous
    curve instead bends the path through the anchor and changes its length.
    """
    slider = _slider("0,0,1000,2,0,B|100:0|100:0|200:0,1,200")

    types = [cp.Type for cp in slider.Path.ControlPoints]
    assert types[0] is not None
    assert sum(1 for t in types if t is not None) == 2, types


def test_single_segment_has_one_typed_control_point():
    """A path without repeats stays a single segment."""
    slider = _slider("0,0,1000,2,0,B|100:0|200:100,1,200")

    types = [cp.Type for cp in slider.Path.ControlPoints]
    assert sum(1 for t in types if t is not None) == 1


def test_legacy_formats_truncate_path_coordinates():
    """Before the lazer format, path coordinates are whole pixels."""
    legacy = _slider("0,0,1000,2,0,B|100.7:50.9,1,100", version=14)
    assert legacy.Path.ControlPoints[1].Position.X == pytest.approx(100.0)
    assert legacy.Path.ControlPoints[1].Position.Y == pytest.approx(50.0)


def test_slider_length_keeps_full_precision():
    """The declared length is a double, not a single-precision value.

    Rounding it to single precision shifts slider duration by a fraction of a
    millisecond, which is enough to move objects between strain sections.
    """
    slider = _slider("188,76,8182,2,0,P|336:72,1,144.000005493164")
    assert slider.Path.ExpectedDistance == pytest.approx(
        144.000005493164, abs=1e-12
    )
    assert slider.Path.Distance == pytest.approx(144.000005493164, abs=1e-9)


def test_early_format_shifts_every_time_by_24ms():
    """Beatmaps before format v5 carry a 24 ms timing offset."""
    early = LegacyBeatmapDecoder.FromText(
        "osu file format v4\n[General]\nMode: 0\n"
        "[HitObjects]\n256,192,1000,1,0\n"
    )
    modern = LegacyBeatmapDecoder.FromText(
        "osu file format v5\n[General]\nMode: 0\n"
        "[HitObjects]\n256,192,1000,1,0\n"
    )
    assert early.HitObjects[0].StartTime == 1024.0
    assert modern.HitObjects[0].StartTime == 1000.0
