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

import pytest

from parsecore.Beatmaps.Formats.LegacyBeatmapDecoder import LegacyBeatmapDecoder
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapConverter import OsuBeatmapConverter
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapProcessor import OsuBeatmapProcessor
from parsecore.Rulesets.Osu.Difficulty.Preprocessing.OsuDifficultyHitObject import (
    OsuDifficultyHitObject,
)
from parsecore.Rulesets.Osu.Difficulty.Skills.Aim import (
    Aim,
    _calculate_snap_flow_probability,
)
from parsecore.Rulesets.Osu.Difficulty.Skills.Flashlight import Flashlight
from parsecore.Rulesets.Osu.Difficulty.Skills.Reading import Reading
from parsecore.Rulesets.Osu.Difficulty.Skills.Speed import Speed
from parsecore.Rulesets.Osu.Mods.OsuModAutopilot import OsuModAutopilot
from parsecore.Rulesets.Osu.Mods.OsuModFlashlight import OsuModFlashlight
from parsecore.Rulesets.Osu.Mods.OsuModRelax import OsuModRelax

HEADER = (
    "osu file format v14\n"
    "[General]\nMode: 0\n"
    "[Difficulty]\nCircleSize:4\nApproachRate:9\nOverallDifficulty:8\n"
    "SliderMultiplier:1.4\nSliderTickRate:1\n"
    "[TimingPoints]\n0,300,4,2,0,60,1,0\n"
    "[HitObjects]\n"
)


def _objects(hit_object_lines: str):
    """Build difficulty objects from raw hit-object lines."""
    decoded = LegacyBeatmapDecoder.FromText(HEADER + hit_object_lines)
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
    return objects, playable


def _pattern(count: int = 20, spacing: int = 90, interval: int = 180) -> str:
    """Return a zig-zag pattern of circles."""
    return "".join(
        f"{60 + (i % 4) * spacing},{80 + (i % 3) * spacing},"
        f"{1000 + i * interval},1,0\n"
        for i in range(count)
    )


def _run(skill, objects):
    """Feed every object to a skill and return it."""
    for obj in objects:
        skill.Process(obj)
    return skill




def test_snap_and_flow_probabilities_always_sum_to_one():
    """The blend satisfies ``f(x) + f(1/x) = 1``, as the source requires."""
    for ratio in (0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 10.0):
        forward = _calculate_snap_flow_probability(ratio)
        inverse = _calculate_snap_flow_probability(1 / ratio)
        assert forward + inverse == pytest.approx(1.0)
        assert 0.0 <= forward <= 1.0


def test_equal_snap_and_flow_gives_an_even_blend():
    """When snap and flow are equally hard, neither dominates."""
    assert _calculate_snap_flow_probability(1.0) == pytest.approx(0.5)


def test_aim_counts_sliders_when_asked_to():
    """Including slider travel cannot lower the aim difficulty."""
    objects, _ = _objects(
        _pattern(10) + "100,100,5000,2,0,L|300:100,1,200\n200,200,5600,1,0\n"
    )
    with_sliders = _run(Aim([], True), objects).DifficultyValue()
    without_sliders = _run(Aim([], False), objects).DifficultyValue()
    assert with_sliders >= without_sliders


def test_autopilot_removes_all_aim_difficulty():
    """Autopilot aims for the player, so aim is worth nothing."""
    objects, _ = _objects(_pattern())
    assert _run(Aim([OsuModAutopilot()], True), objects).DifficultyValue() == 0.0




def test_relax_removes_all_speed_difficulty():
    """Relax taps for the player, so speed is worth nothing."""
    objects, _ = _objects(_pattern())
    assert _run(Speed([OsuModRelax()]), objects).DifficultyValue() == 0.0


def test_faster_patterns_raise_speed_difficulty():
    """A denser rhythm is harder to tap than a sparse one."""
    slow, _ = _objects(_pattern(interval=400))
    fast, _ = _objects(_pattern(interval=110))
    assert _run(Speed([]), fast).DifficultyValue() > _run(
        Speed([]), slow
    ).DifficultyValue()


def test_relevant_object_count_is_bounded_by_object_count():
    """The relevant object count never exceeds how many objects there are."""
    objects, _ = _objects(_pattern())
    skill = _run(Speed([]), objects)
    skill.DifficultyValue()
    assert 0 <= skill.RelevantObjectCount() <= len(objects)




def test_flashlight_is_zero_without_the_mod():
    """Flashlight only measures anything when the mod is on."""
    objects, playable = _objects(_pattern())
    skill = _run(Flashlight([], len(playable.HitObjects)), objects)
    assert skill.DifficultyValue() == 0.0


def test_flashlight_is_positive_with_the_mod():
    """With the mod on, flashlight contributes difficulty."""
    objects, playable = _objects(_pattern())
    skill = _run(Flashlight([OsuModFlashlight()], len(playable.HitObjects)), objects)
    assert skill.DifficultyValue() > 0


def test_longer_maps_get_a_larger_flashlight_multiplier():
    """A longer beatmap spends less time at the wide low-combo radius."""
    objects, _ = _objects(_pattern())
    short = _run(Flashlight([OsuModFlashlight()], 50), objects).DifficultyValue()
    long = _run(Flashlight([OsuModFlashlight()], 500), objects).DifficultyValue()
    assert long > short




def test_reading_produces_a_positive_value():
    """A varied pattern is worth something to read."""
    objects, _ = _objects(_pattern())
    assert _run(Reading([]), objects).DifficultyValue() > 0




def test_every_skill_stays_finite_on_real_beatmaps(beatmap_files):
    """No skill produces an infinite or negative difficulty."""
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

        for skill in (
            Aim([], True),
            Aim([], False),
            Speed([]),
            Reading([]),
            Flashlight([OsuModFlashlight()], len(playable.HitObjects)),
        ):
            value = _run(skill, objects).DifficultyValue()
            assert math.isfinite(value), f"{path.name} {type(skill).__name__}"
            assert value >= 0, f"{path.name} {type(skill).__name__}"
