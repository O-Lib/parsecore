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

from typing import cast

from parsecore.Rulesets.Mania.Objects.HoldNote import HoldNote
from parsecore.Rulesets.Mania.Objects.Note import Note
from parsecore.Rulesets.Mania.Scoring.ManiaHitWindows import ManiaHitWindows
from parsecore.Rulesets.Mods.IApplicableToHitObject import IApplicableToHitObject
from parsecore.Rulesets.Objects.HitObject import HitObject


class IManiaRateAdjustmentMod(IApplicableToHitObject):
    """A rate mod that scales the hit windows along with the rate."""
    
    SpeedChange: float

    def ApplyToHitObject(self, hit_object: HitObject) -> None:
        """Scale the windows of a note, or of both ends of a hold.

        Args:
            hit_object: The object to modify.
        """
        if isinstance(hit_object, HoldNote):
            if hit_object.Head is not None and hit_object.Tail is not None:
                cast(ManiaHitWindows, hit_object.Head.HitWindows).SpeedMultiplier = self.SpeedChange
                cast(ManiaHitWindows, hit_object.Tail.HitWindows).SpeedMultiplier = self.SpeedChange
        elif isinstance(hit_object, Note):
            cast(ManiaHitWindows, hit_object.HitWindows).SpeedMultiplier = self.SpeedChange
