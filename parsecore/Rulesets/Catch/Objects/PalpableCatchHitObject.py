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

from parsecore.Rulesets.Catch.Objects.CatchHitObject import CatchHitObject


class PalpableCatchHitObject(CatchHitObject):
    """Something the plate can catch."""

    def __init__(self, start_time: float = 0.0, x: float = 0.0) -> None:
        """Create a catchable object.

        Args:
            start_time: The object's time in milliseconds.
            x: Where the beatmap places it across the playfield.
        """
        super().__init__(start_time, x)
        # How much further the object could sit before the player would have
        # to hyper-dash to reach the next one.
        self.DistanceToHyperDash: float = 0.0
        self._hyper_dash_target = None

    @property
    def HyperDash(self) -> bool:
        """Return whether reaching the next object needs a hyper-dash."""
        return self._hyper_dash_target is not None

    @property
    def HyperDashTarget(self):
        """Return the object a hyper-dash from here leads to."""
        return self._hyper_dash_target

    @HyperDashTarget.setter
    def HyperDashTarget(self, value) -> None:
        """Set the object a hyper-dash from here leads to.

        Args:
            value: The target, or ``None`` for no hyper-dash.
        """
        self._hyper_dash_target = value
