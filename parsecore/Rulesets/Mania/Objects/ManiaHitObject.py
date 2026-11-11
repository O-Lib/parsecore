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

from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Objects.Types.IHasColumn import IHasColumn
from parsecore.Rulesets.Objects.Types.IHasXPosition import IHasXPosition


class ManiaHitObject(HitObject, IHasColumn, IHasXPosition):
    """A note in one column of the stage."""

    def __init__(self) -> None:
        """Create a mania object."""
        super().__init__()
        self._column = 0

    @property
    def Column(self) -> int:
        """Return the column this object is played in."""
        return self._column

    @Column.setter
    def Column(self, value: int) -> None:
        """Move the object to another column.

        Args:
            value: The column to move it to.
        """
        self._column = value

    @property
    def X(self) -> float:
        """Return the column as a position, which is how osu! writes it out."""
        return self.Column

    @X.setter
    def X(self, value: float) -> None:
        """Set the column from an x position.

        Args:
            value: The x position to set.
        """
        self.Column = int(value)

    def CreateHitWindows(self):
        """Return the hit windows this object is judged with."""
        from parsecore.Rulesets.Mania.Scoring.ManiaHitWindows import ManiaHitWindows

        return ManiaHitWindows()
