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

from parsecore.Rulesets.Objects.Legacy.ConvertHitObject import ConvertHitObject
from parsecore.Utils.Vector2 import Vector2

# The centre of the osu! playfield, where spinners sit.
PLAYFIELD_CENTRE = Vector2(256, 192)


class ConvertSpinner(ConvertHitObject):
    """An object spun for a duration."""

    def __init__(self, start_time: float = 0.0, end_time: float = 0.0,
                 position: Vector2 | None = None) -> None:
        """Create a spinner.

        Args:
            start_time: The spinner's start in milliseconds.
            end_time: The spinner's end in milliseconds.
            position: The spinner's centre.
        """
        super().__init__(start_time)
        self.EndTime: float = end_time
        self.Position: Vector2 = position or PLAYFIELD_CENTRE

    @property
    def X(self) -> float:
        """Return the spinner's x position."""
        return self.Position.X

    @property
    def Y(self) -> float:
        """Return the spinner's y position."""
        return self.Position.Y

    @property
    def Duration(self) -> float:
        """Return how long the spinner lasts."""
        return self.EndTime - self.StartTime
