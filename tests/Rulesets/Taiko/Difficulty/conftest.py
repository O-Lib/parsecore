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

from parsecore.Audio.HitSampleInfo import HIT_CLAP, HIT_NORMAL, HitSampleInfo
from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Beatmaps.ControlPoints.ControlPointInfo import ControlPointInfo
from parsecore.Beatmaps.ControlPoints.TimingControlPoint import TimingControlPoint
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.TaikoDifficultyHitObject import (
    TaikoDifficultyHitObject,
)
from parsecore.Rulesets.Taiko.Objects.Hit import Hit


def build_difficulty_objects(
    pattern: str, deltas: list[float] | None = None, beat_length: float = 500.0
) -> list[TaikoDifficultyHitObject]:
    """Return difficulty objects for a written-out pattern of notes.

    Args:
        pattern: One character per note -- ``d`` for a centre hit, ``k`` for a
            rim hit.
        deltas: The gap before each note, defaulting to an even 200 ms.
        beat_length: The beat length to time the beatmap at.

    Returns:
        The difficulty objects, one per note after the first two.
    """
    gaps = deltas if deltas is not None else [200.0] * len(pattern)

    notes = []
    time = 0.0
    for character, gap in zip(pattern, gaps, strict=True):
        time += gap
        note = Hit(time)
        note.Samples = (
            [HitSampleInfo(HIT_NORMAL), HitSampleInfo(HIT_CLAP)]
            if character == "k"
            else [HitSampleInfo(HIT_NORMAL)]
        )
        notes.append(note)

    control_points = ControlPointInfo()
    control_points.Add(0.0, TimingControlPoint(BeatLength=beat_length))
    difficulty = BeatmapDifficulty()
    for note in notes:
        note.ApplyDefaults(control_points, difficulty)

    objects: list[TaikoDifficultyHitObject] = []
    centres: list[TaikoDifficultyHitObject] = []
    rims: list[TaikoDifficultyHitObject] = []
    all_notes: list[TaikoDifficultyHitObject] = []

    for i in range(2, len(notes)):
        objects.append(
            TaikoDifficultyHitObject(
                notes[i],
                notes[i - 1],
                1.0,
                objects,
                centres,
                rims,
                all_notes,
                len(objects),
                control_points,
                difficulty.SliderMultiplier,
            )
        )

    return objects
