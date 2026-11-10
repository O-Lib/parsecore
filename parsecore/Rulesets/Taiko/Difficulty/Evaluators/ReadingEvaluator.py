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

from __future__ import annotations

from dataclasses import dataclass

from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.TaikoDifficultyHitObject import (
    TaikoDifficultyHitObject,
)


def EvaluateDifficultyOf(note_object: TaikoDifficultyHitObject) -> float:
    """Return how hard a note is to read.

    Args:
        note_object: The difficulty object to rate.
    """
    high_velocity = VelocityRange(480, 640)
    mid_velocity = VelocityRange(360, 480)

    effective_bpm = max(1.0, note_object.EffectiveBPM)

    mid_velocity_difficulty = 0.5 * DiffUtils.Logistic(
        effective_bpm,
        mid_velocity.Center,
        1.0 / (mid_velocity.Range / 10),
    )

    # How closely the notes are packed compared to what this scroll speed
    # would ordinarily give.
    expected_delta_time = 21000.0 / effective_bpm
    object_density = expected_delta_time / max(1.0, note_object.DeltaTime)
    density_penalty = DiffUtils.Logistic(object_density, 0.925, 15)

    high_velocity_difficulty = (1.0 - 0.33 * density_penalty) * DiffUtils.Logistic(
        effective_bpm,
        high_velocity.Center + 8 * density_penalty,
        (1.0 + 0.5 * density_penalty)
        / (high_velocity.Range / 10),
    )

    return mid_velocity_difficulty + high_velocity_difficulty


@dataclass(frozen=True)
class VelocityRange:
    """Range of scroll velocities for reading difficulty evaluation."""
    
    Min: float
    Max: float

    @property
    def Center(self) -> float:
        """Return the midpoint of the velocity range."""
        return (self.Max + self.Min) / 2

    @property
    def Range(self) -> float:
        """Return the total span of the velocity range."""
        return self.Max - self.Min
