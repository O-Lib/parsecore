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


@dataclass
class TaikoDifficultyAttributes(DifficultyAttributes):
    """The parts a taiko beatmap's star rating is made of."""

    # Colour and stamina together: what the hands have to do.
    MechanicalDifficulty: float = 0.0

    RhythmDifficulty: float = 0.0
    ReadingDifficulty: float = 0.0
    ColourDifficulty: float = 0.0
    StaminaDifficulty: float = 0.0

    # How much of the stamina demand comes from single-colour runs alone.
    MonoStaminaFactor: float = 0.0

    # How evenly the difficulty is spread, rather than sitting in a few spikes.
    ConsistencyFactor: float = 0.0

    StaminaTopStrains: float = 0.0
