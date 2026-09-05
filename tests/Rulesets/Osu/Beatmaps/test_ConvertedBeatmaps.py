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
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapConverter import OsuBeatmapConverter
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapProcessor import OsuBeatmapProcessor
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner
from parsecore.Utils.Vector2 import Vector2

MANIA_MAP = (
    "osu file format v14\n"
    "[General]\nMode: 3\nStackLeniency: 0.7\n"
    "[Difficulty]\nCircleSize:5\nApproachRate:9\nOverallDifficulty:8\n"
    "SliderMultiplier:1.4\nSliderTickRate:1\n"
    "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
    "[HitObjects]\n"
    "51,192,1000,1,0\n"
    "153,192,1500,128,0,2500:0\n"
    "460,192,3000,1,0\n"
)


def _convert(text: str):
    """Decode a beatmap and run it through the osu! conversion pipeline."""
    decoded = LegacyBeatmapDecoder.FromText(text)
    return WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor
    )


def test_a_hold_note_becomes_a_spinner():
    """A mania hold note converts to a spinner, not a circle.

    osu! decides this on the object having a duration rather than on which
    ruleset wrote it, so a hold note takes the same branch a spinner does.
    """
    beatmap = _convert(MANIA_MAP)

    assert isinstance(beatmap.HitObjects[0], HitCircle)
    assert isinstance(beatmap.HitObjects[1], Spinner)
    assert isinstance(beatmap.HitObjects[2], HitCircle)

    spinner = beatmap.HitObjects[1]
    assert spinner.EndTime == 2500
    assert spinner.Position == Vector2(153, 192)


def test_a_spinner_is_never_moved_by_stacking():
    """Stacking raises a spinner's height but never its position.

    The pre-v6 algorithm happily stacks spinners, and converted beatmaps pile
    objects onto identical positions, so without this a spinner would drift off
    the playfield.
    """
    stacked = (
        "osu file format v5\n"
        "[General]\nMode: 1\nStackLeniency: 0.7\n"
        "[Difficulty]\nCircleSize:5\nApproachRate:9\nOverallDifficulty:8\n"
        "SliderMultiplier:1.4\nSliderTickRate:1\n"
        "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
        "[HitObjects]\n"
        + "".join(f"256,192,{1000 + i * 50},1,0\n" for i in range(8))
        + "256,192,1400,12,0,2000\n"
    )
    beatmap = _convert(stacked)

    spinner = next(o for o in beatmap.HitObjects if isinstance(o, Spinner))
    assert spinner.StackOffset == Vector2()
    assert spinner.StackedPosition == spinner.Position

    circles = [o for o in beatmap.HitObjects if isinstance(o, HitCircle)]
    assert any(c.StackHeight != 0 for c in circles), "expected the circles to stack"


def test_pre_v6_stacking_advances_by_start_time():
    """The old algorithm measures the next object from its start time.

    osu!stable never computed an end time for the object it was comparing
    against, and osu! keeps that: using the end time instead lets a stack run
    on far longer than it should.
    """
    text = (
        "osu file format v5\n"
        "[General]\nMode: 0\nStackLeniency: 0.7\n"
        "[Difficulty]\nCircleSize:4\nApproachRate:9\nOverallDifficulty:8\n"
        "SliderMultiplier:1.4\nSliderTickRate:1\n"
        "[TimingPoints]\n0,500,4,2,0,60,1,0\n"
        "[HitObjects]\n"
        "100,100,1000,1,0\n"
        "100,100,1200,1,0\n"
        "100,100,1400,1,0\n"
    )
    beatmap = _convert(text)

    heights = [o.StackHeight for o in beatmap.HitObjects]
    assert heights == [2, 1, 0]


def test_every_mode_can_be_rated_as_osu():
    """A beatmap from any ruleset converts and rates without complaint."""
    from parsecore.Rulesets.Osu.Difficulty.OsuDifficultyCalculator import (
        OsuDifficultyCalculator,
    )

    for mode in (0, 1, 2, 3):
        text = MANIA_MAP.replace("Mode: 3", f"Mode: {mode}")
        beatmap = _convert(text)
        attributes = OsuDifficultyCalculator(beatmap).Calculate([])
        assert attributes.StarRating > 0, f"mode {mode} rated as zero"
        assert attributes.MaxCombo > 0
