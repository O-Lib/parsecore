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

from parsecore.Beatmaps.Legacy.LegacyHitObjectType import LegacyHitObjectType
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Objects.Legacy.IHasLegacyHitObjectType import (
    IHasLegacyHitObjectType,
)
from parsecore.Rulesets.Objects.Types.IHasCombo import IHasCombo
from parsecore.Rulesets.Objects.Types.IHasPosition import IHasPosition
from parsecore.Utils.Vector2 import Vector2


class ConvertHitObject(HitObject, IHasCombo, IHasPosition, IHasLegacyHitObjectType):
    """A decoded but not yet ruleset-specific hit object."""

    def __init__(self, start_time: float = 0.0) -> None:
        """Create a convert hit object.

        Args:
            start_time: The object's time in milliseconds.
        """
        super().__init__(start_time)
        self.NewCombo: bool = False
        self.ComboOffset: int = 0
        self.position: Vector2 = Vector2()
        self.LegacyType: LegacyHitObjectType = LegacyHitObjectType.Circle

    @property
    def Position(self) -> Vector2:
        """Return or set the 2D position of the object on the playfield."""
        return self.position

    @Position.setter
    def Position(self, value: Vector2) -> None:
        self.position = value

    @property
    def X(self) -> float:
        """Return or set the X position of the object."""
        return self.Position.X

    @X.setter
    def X(self, value: float) -> None:
        self.Position = Vector2(value, self.Position.Y)

    @property
    def Y(self) -> float:
        """Return or set the Y position of the object."""
        return self.Position.Y

    @Y.setter
    def Y(self, value: float) -> None:
        self.Position = Vector2(self.Position.X, value)

    def CreateJudgement(self):
        """Return the judgement for this object.

        Returns:
            An IgnoreJudgement instance.
        """
        from parsecore.Rulesets.Judgements.IgnoreJudgement import IgnoreJudgement
        return IgnoreJudgement()

    def CreateHitWindows(self):
        """Return the hit windows for this object.

        Returns:
            An EmptyHitWindows instance.
        """
        from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows
        return EmptyHitWindows()
