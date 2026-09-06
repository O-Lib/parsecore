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

from parsecore.Rulesets.Mania.Objects.HoldNote import HoldNote
from parsecore.Rulesets.Mania.Objects.Note import Note
from parsecore.Rulesets.Mods.ModEasy import ModEasy

# How much the hit windows are widened by.
HIT_WINDOW_DIFFICULTY_MULTIPLIER = 1 / 1.4


class ManiaModEasy(ModEasy):
    """More forgiving drain, less accuracy required, and extra lives."""

    Description = (
        "More forgiving HP drain, less accuracy required, and extra lives!"
    )

    def ApplyToHitObject(self, hit_object) -> None:
        """Widen the windows of a note, or of both ends of a hold.

        Args:
            hit_object: The object to modify.
        """
        if isinstance(hit_object, HoldNote):
            hit_object.Head.HitWindows.DifficultyMultiplier = (
                HIT_WINDOW_DIFFICULTY_MULTIPLIER
            )
            hit_object.Tail.HitWindows.DifficultyMultiplier = (
                HIT_WINDOW_DIFFICULTY_MULTIPLIER
            )
        elif isinstance(hit_object, Note):
            hit_object.HitWindows.DifficultyMultiplier = (
                HIT_WINDOW_DIFFICULTY_MULTIPLIER
            )
