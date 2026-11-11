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

from parsecore.Rulesets.Mods.IApplicableToRate import IApplicableToRate
from parsecore.Rulesets.Mods.Mod import Mod


class ModRateAdjust(Mod, IApplicableToRate):
    """A mod that multiplies the beatmap's playback rate."""

    SpeedChange: float = 1.0

    def ApplyToRate(self, time: float, rate: float = 1.0) -> float:
        """Return the rate with this mod's multiplier applied.

        Args:
            time: The time in the beatmap.
            rate: The rate before this mod is applied.

        Returns:
            The adjusted playback rate.
        """
        return rate * self.SpeedChange

    def _rateAdjustMultiplier(self) -> float:
        """Calculate the score multiplier based on the current speed change.

        Returns:
            The calculated score multiplier for rate adjustments.
        """
        value = int(self.SpeedChange * 10) / 10.0
        value -= 1

        if self.SpeedChange >= 1:
            return 1 + value / 5
        else:
            return 0.6 + value
