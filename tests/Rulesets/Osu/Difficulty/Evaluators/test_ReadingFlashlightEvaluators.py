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

from parsecore.Beatmaps.Formats.LegacyBeatmapDecoder import LegacyBeatmapDecoder
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapConverter import OsuBeatmapConverter
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapProcessor import OsuBeatmapProcessor
from parsecore.Rulesets.Osu.Difficulty.Evaluators import (
    FlashlightEvaluator,
    ReadingEvaluator,
)
from parsecore.Rulesets.Osu.Difficulty.Evaluators.ReadingEvaluator import (
    _calculate_preempt_difficulty,
    _retrieve_current_visible_object_density,
)
from parsecore.Rulesets.Osu.Difficulty.Preprocessing.OsuDifficultyHitObject import (
    OsuDifficultyHitObject,
)
from parsecore.Rulesets.Osu.Mods.OsuModHidden import OsuModHidden


def _header(approach_rate: float = 9.0) -> str:
    """Return a beatmap header at a given approach rate."""
    return (
        "osu file format v14\n"
        "[General]\nMode: 0\n"
        f"[Difficulty]\nCircleSize:4\nApproachRate:{approach_rate}\n"
        "OverallDifficulty:8\nSliderMultiplier:1.4\nSliderTickRate:1\n"
        "[TimingPoints]\n0,300,4,2,0,60,1,0\n"
        "[HitObjects]\n"
    )


def _objects(hit_object_lines: str, approach_rate: float = 9.0):
    """Build difficulty objects from raw hit-object lines."""
    decoded = LegacyBeatmapDecoder.FromText(_header(approach_rate) + hit_object_lines)
    playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
        OsuBeatmapConverter, OsuBeatmapProcessor
    )
    objects: list[OsuDifficultyHitObject] = []
    for i in range(1, len(playable.HitObjects)):
        objects.append(
            OsuDifficultyHitObject(
                playable.HitObjects[i],
                playable.HitObjects[i - 1],
                1.0,
                objects,
                len(objects),
            )
        )
    return objects


def _pattern(count: int = 14, spacing: int = 70, interval: int = 200) -> str:
    """Return a zig-zag pattern of circles."""
    return "".join(
        f"{80 + (i % 4) * spacing},{100 + (i % 3) * spacing},"
        f"{1000 + i * interval},1,0\n"
        for i in range(count)
    )




def test_flashlight_rewards_larger_movements():
    """Patterns that travel further are harder to see coming."""
    tight = _objects(_pattern(spacing=10))
    wide = _objects(_pattern(spacing=110))
    assert sum(
        FlashlightEvaluator.EvaluateDifficultyOf(o, []) for o in wide
    ) > sum(FlashlightEvaluator.EvaluateDifficultyOf(o, []) for o in tight)


def test_flashlight_is_harder_with_hidden():
    """Hidden removes the approach circles, so flashlight rates higher."""
    objects = _objects(_pattern())
    plain = sum(FlashlightEvaluator.EvaluateDifficultyOf(o, []) for o in objects)
    with_hidden = sum(
        FlashlightEvaluator.EvaluateDifficultyOf(o, [OsuModHidden()]) for o in objects
    )
    assert with_hidden > plain


def test_flashlight_ignores_spinners():
    """A spinner has nothing to read."""
    objects = _objects(
        "100,100,1000,1,0\n200,200,1300,1,0\n256,192,1600,12,0,3500\n"
    )
    assert FlashlightEvaluator.EvaluateDifficultyOf(objects[-1], []) == 0.0




def test_reading_is_harder_with_hidden():
    """Objects that spend time invisible are harder to read."""
    objects = _objects(_pattern())
    plain = sum(ReadingEvaluator.EvaluateDifficultyOf(o, False) for o in objects)
    with_hidden = sum(ReadingEvaluator.EvaluateDifficultyOf(o, True) for o in objects)
    assert with_hidden > plain


def test_preempt_difficulty_starts_above_approach_rate_nine_and_two_thirds():
    """Approach time only becomes a difficulty below 500 ms, as osu! defines it.

    Reading difficulty as a whole is deliberately not monotonic in approach
    rate: a low rate leaves more objects on screen at once, which is its own
    kind of reading difficulty. Only this component is monotonic.
    """
    assert _calculate_preempt_difficulty(1.0, 1.0, 900) == 0.0
    assert _calculate_preempt_difficulty(1.0, 1.0, 600) == 0.0
    assert _calculate_preempt_difficulty(1.0, 1.0, 500) == 0.0

    at_450 = _calculate_preempt_difficulty(1.0, 1.0, 450)
    at_300 = _calculate_preempt_difficulty(1.0, 1.0, 300)
    assert 0 < at_450 < at_300


def test_lower_approach_rate_leaves_more_objects_visible():
    """A longer approach window puts more objects on screen at once."""
    low = _objects(_pattern(), approach_rate=4)
    high = _objects(_pattern(), approach_rate=10)
    assert _retrieve_current_visible_object_density(
        low[3]
    ) > _retrieve_current_visible_object_density(high[3])


def test_reading_scores_nothing_for_the_first_object():
    """Nothing has been seen yet before the first difficulty object."""
    objects = _objects(_pattern())
    assert ReadingEvaluator.EvaluateDifficultyOf(objects[0], False) == 0.0


def test_reading_and_flashlight_stay_finite(beatmap_files):
    """Neither evaluator produces an infinite or negative value."""
    for path in beatmap_files:
        decoded = LegacyBeatmapDecoder.FromPath(str(path))
        if decoded.BeatmapInfo.RulesetID != 0:
            continue
        playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
            OsuBeatmapConverter, OsuBeatmapProcessor
        )
        objects: list[OsuDifficultyHitObject] = []
        for i in range(1, len(playable.HitObjects)):
            objects.append(
                OsuDifficultyHitObject(
                    playable.HitObjects[i],
                    playable.HitObjects[i - 1],
                    1.0,
                    objects,
                    len(objects),
                )
            )
        for obj in objects:
            for value in (
                ReadingEvaluator.EvaluateDifficultyOf(obj, False),
                ReadingEvaluator.EvaluateDifficultyOf(obj, True),
                FlashlightEvaluator.EvaluateDifficultyOf(obj, []),
                FlashlightEvaluator.EvaluateDifficultyOf(obj, [OsuModHidden()]),
            ):
                assert math.isfinite(value)
                assert value >= 0
