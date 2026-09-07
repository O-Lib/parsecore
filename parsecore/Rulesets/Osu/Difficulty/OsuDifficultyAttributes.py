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

from parsecore.Rulesets.Difficulty.DifficultyAttributes import DifficultyAttributes


@dataclass(slots=True)
class OsuDifficultyAttributes(DifficultyAttributes):
    """How hard an osu! beatmap is, broken down by skill."""

    AimDifficulty: float = 0.0
    AimDifficultSliderCount: float = 0.0
    SpeedDifficulty: float = 0.0
    SpeedNoteCount: float = 0.0
    FlashlightDifficulty: float = 0.0
    ReadingDifficulty: float = 0.0

    SliderFactor: float = 1.0
    AimTopWeightedSliderFactor: float = 0.0
    SpeedTopWeightedSliderFactor: float = 0.0

    AimDifficultStrainCount: float = 0.0
    SpeedDifficultStrainCount: float = 0.0
    ReadingDifficultNoteCount: float = 0.0

    # Filled in by the legacy score simulator, which is not ported yet.
    NestedScorePerObject: float = 0.0
    LegacyScoreBaseMultiplier: float = 0.0
    MaximumLegacyComboScore: float = 0.0

    HitCircleCount: int = 0
    SliderCount: int = 0
    SpinnerCount: int = 0
