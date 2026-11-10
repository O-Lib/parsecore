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

from parsecore.Rulesets.Mods.ModTracable import ModTracable
from parsecore.Rulesets.Mods.ModType import ModType
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner
from parsecore.Rulesets.Osu.Objects.SpinnerTick import SpinnerTick


class OsuModTraceable(ModTracable):
    """Put your faith in the approach circles..."""

    Name = "Traceable"
    Acronym = "TC"
    Description = "Put your faith in the approach circles..."
    Type = ModType.DifficultyIncrease
    Ranked = True

    @staticmethod
    def IsFirstAdjustableObject(hit_object: HitObject) -> bool:
        """Check if a hit object is eligible for traceable visibility adjustments.

        Args:
            hit_object: The hit object to test.
        """
        return not (isinstance(hit_object, Spinner) or isinstance(hit_object, SpinnerTick))
