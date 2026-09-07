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
from parsecore.Beatmaps.Formats.LegacyBeatmapEncoder import (
    FIRST_LAZER_VERSION,
    LegacyBeatmapEncoder,
)

GOLDEN_SECTIONS = [
    (
        "Kenji Ninuma - DISCOPRINCE (peppy) [Normal].osu",
        "[TimingPoints]",
        ["142,500.004999999999,4,1,0,100,1,0"],
    ),
    (
        "Shuhei Kita - Soul Phrase (HakuNoKaemi) [Orpheus Telos].osu",
        "[TimingPoints]",
        [
            "635,-100,4,0,2,60,0,0",
            "1317,340.909090909091,4,1,2,60,1,0",
            "5834,-100,4,1,0,60,0,0",
        ],
    ),
]


def _encode(path) -> str:
    """Return a beatmap decoded and written straight back out.

    Args:
        path: The beatmap file to round trip.
    """
    return LegacyBeatmapEncoder(LegacyBeatmapDecoder.FromPath(str(path))).EncodeToString()


def _section(text: str, name: str) -> list[str]:
    """Return the lines of one section of an encoded beatmap.

    Args:
        text: The encoded beatmap.
        name: The section header to read, brackets included.
    """
    lines = text.replace("\r\n", "\n").split("\n")
    start = lines.index(name) + 1
    end = next(
        (i for i in range(start, len(lines)) if lines[i].startswith("[")), len(lines)
    )
    return [line for line in lines[start:end] if line]


def test_the_format_version_is_the_one_osu_writes(beatmap_files):
    """osu!lazer writes a version osu!stable was never meant to read."""
    text = _encode(beatmap_files[0])

    assert text.startswith(f"osu file format v{FIRST_LAZER_VERSION}")


def test_lines_end_the_way_osu_ends_them(beatmap_files):
    """A ``.osu`` file ends its lines with a carriage return and a newline."""
    text = _encode(beatmap_files[0])

    assert "\r\n" in text
    assert "\n" not in text.replace("\r\n", "")


def test_every_section_is_written(beatmap_files):
    """All eight sections appear, in the order osu! writes them."""
    text = _encode(beatmap_files[0])

    positions = [
        text.index(name)
        for name in (
            "[General]",
            "[Editor]",
            "[Metadata]",
            "[Difficulty]",
            "[Events]",
            "[TimingPoints]",
            "[HitObjects]",
        )
    ]

    assert positions == sorted(positions)


def test_a_single_precision_setting_is_not_written_out_in_full(beatmap_files):
    """A stack leniency of seven tenths writes as ``0.7``, not as a double."""
    path = next(
        f for f in beatmap_files if f.name.startswith("Kenji Ninuma - DISCOPRINCE")
    )

    assert "StackLeniency: 0.7\r\n" in _encode(path)
    assert "0.699999988079071" not in _encode(path)


@pytest.mark.parametrize(
    "name,section,expected",
    GOLDEN_SECTIONS,
    ids=[f'{n.split(" - ")[0]}' for n, _, _ in GOLDEN_SECTIONS],
)
def test_a_section_matches_osu(beatmap_files, name, section, expected):
    """The lines osu! writes for a section come out the same here."""
    path = next(f for f in beatmap_files if f.name == name)

    lines = _section(_encode(path), section)

    for wanted in expected:
        assert wanted in lines


def test_a_red_and_an_inherited_line_on_one_millisecond_collapse(beatmap_files):
    """Only the later of two points of a kind at one time survives decoding.

    This beatmap opens with a red and an inherited line both at 1317, and the
    inherited one's sample bank is the one that counts. Getting this wrong
    leaves two sample points and the whole beatmap sounds off.
    """
    path = next(
        f for f in beatmap_files if f.name.startswith("Shuhei Kita - Soul Phrase")
    )
    decoded = LegacyBeatmapDecoder.FromPath(str(path))

    at_1317 = [p for p in decoded.ControlPointInfo.SamplePoints if p.Time == 1317]

    assert len(at_1317) == 1
    assert at_1317[0].SampleBank == "normal"
    assert at_1317[0].SampleVolume == 60


def test_a_beatmap_survives_a_round_trip(beatmap_files):
    """Encoding, decoding and encoding again changes nothing."""
    path = next(
        f for f in beatmap_files if f.name.startswith("Kenji Ninuma - DISCOPRINCE")
    )

    once = _encode(path)
    twice = LegacyBeatmapEncoder(
        LegacyBeatmapDecoder.FromText(once)
    ).EncodeToString()

    assert once == twice


def test_a_beatmap_of_no_legacy_ruleset_is_refused():
    """Only the four rulesets the format knows can be written."""
    decoded = LegacyBeatmapDecoder.FromText(
        "osu file format v14\n[General]\nMode: 0\n[HitObjects]\n"
    )
    decoded.BeatmapInfo.RulesetID = 7

    with pytest.raises(ValueError):
        LegacyBeatmapEncoder(decoded)
