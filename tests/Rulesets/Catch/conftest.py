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

from parsecore.Beatmaps.Formats.LegacyBeatmapDecoder import LegacyBeatmapDecoder
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmapConverter import (
    CatchBeatmapConverter,
)
from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmapProcessor import (
    CatchBeatmapProcessor,
)

HEADER = (
    "osu file format v14\n"
    "[General]\nMode: 2\n"
    "[Difficulty]\nCircleSize:{cs}\nApproachRate:9\nOverallDifficulty:7\n"
    "SliderMultiplier:1.4\nSliderTickRate:1\n"
    "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
    "[HitObjects]\n"
)


def decode(objects: str, cs: float = 4.0):
    """Return a decoded beatmap for written-out hit object lines.

    Args:
        objects: The ``[HitObjects]`` lines, newline separated.
        cs: The circle size, which decides how wide the plate is.
    """
    return LegacyBeatmapDecoder.FromText(HEADER.format(cs=cs) + objects)


def convert(objects: str, cs: float = 4.0, mods=None):
    """Return a playable catch beatmap for written-out hit object lines.

    Args:
        objects: The ``[HitObjects]`` lines, newline separated.
        cs: The circle size, which decides how wide the plate is.
        mods: The mods to convert under.
    """
    decoded = decode(objects, cs)
    return WorkingBeatmap(decoded).GetPlayableBeatmap(
        CatchBeatmapConverter, CatchBeatmapProcessor, mods or []
    )


def fruits_at(*positions: float, gap: float = 500.0) -> str:
    """Return hit object lines placing one fruit at each position.

    Args:
        positions: Where along the playfield each fruit sits.
        gap: How long to leave between them, in milliseconds.
    """
    return "".join(
        f"{int(x)},192,{1000 + int(i * gap)},1,0\n" for i, x in enumerate(positions)
    )
