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
from parsecore.Rulesets.Mania.Beatmaps.ManiaBeatmapConverter import (
    ManiaBeatmapConverter,
)

MANIA_HEADER = (
    "osu file format v14\n"
    "[General]\nMode: 3\n"
    "[Difficulty]\nHPDrainRate:5\nCircleSize:{keys}\nApproachRate:5\n"
    "OverallDifficulty:{od}\nSliderMultiplier:1.4\nSliderTickRate:1\n"
    "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
    "[HitObjects]\n"
)

OSU_HEADER = (
    "osu file format v14\n"
    "[General]\nMode: 0\n"
    "[Difficulty]\nHPDrainRate:5\nCircleSize:4\nApproachRate:9\n"
    "OverallDifficulty:{od}\nSliderMultiplier:1.4\nSliderTickRate:1\n"
    "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
    "[HitObjects]\n"
)


def decode_mania(objects: str, keys: int = 4, od: float = 7.0):
    """Return a decoded beatmap already written for mania.

    Args:
        objects: The ``[HitObjects]`` lines, newline separated.
        keys: How many columns the beatmap is written for.
        od: The overall difficulty.
    """
    return LegacyBeatmapDecoder.FromText(
        MANIA_HEADER.format(keys=keys, od=od) + objects
    )


def decode_osu(objects: str, od: float = 7.0):
    """Return a decoded beatmap written for osu!.

    Args:
        objects: The ``[HitObjects]`` lines, newline separated.
        od: The overall difficulty.
    """
    return LegacyBeatmapDecoder.FromText(OSU_HEADER.format(od=od) + objects)


def convert(decoded, mods=None):
    """Return a decoded beatmap as mania plays it.

    Args:
        decoded: The decoded beatmap.
        mods: The mods to convert under.
    """
    return WorkingBeatmap(decoded).GetPlayableBeatmap(
        ManiaBeatmapConverter, None, mods or []
    )


def notes_in(*columns: int, keys: int = 4, gap: float = 250.0) -> str:
    """Return hit object lines placing one mania note in each column.

    Args:
        columns: The column of each note, counted from the left.
        keys: How many columns the beatmap has, which the positions encode.
        gap: How long to leave between the notes, in milliseconds.
    """
    return "".join(
        f"{_column_to_x(column, keys)},192,{1000 + int(i * gap)},1,0\n"
        for i, column in enumerate(columns)
    )


def hold(column: int, start: float, end: float, keys: int = 4) -> str:
    """Return one hit object line for a mania hold note.

    Args:
        column: The column to hold, counted from the left.
        start: When the hold begins.
        end: When the hold ends.
        keys: How many columns the beatmap has.
    """
    return f"{_column_to_x(column, keys)},192,{int(start)},128,0,{int(end)}\n"


def _column_to_x(column: int, keys: int) -> int:
    """Return the x position a mania column is written as.

    Args:
        column: The column, counted from the left.
        keys: How many columns the beatmap has.
    """
    return int((column + 0.5) * 512 / keys)
