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

from parsecore.Beatmaps.ControlPoints.ControlPoint import ControlPoint


@dataclass(slots=True)
class EffectControlPoint(ControlPoint):
    """Sets kiai time and scroll speed from a point onward."""

    KiaiMode: bool = False
    ScrollSpeed: float = 1.0

    def __post_init__(self) -> None:
        """Clamp the scroll speed to the range osu! accepts."""
        self.ScrollSpeed = min(max(self.ScrollSpeed, 0.01), 10.0)

    def IsRedundant(self, existing: ControlPoint) -> bool:
        """Return whether this point matches ``existing``.

        Args:
            existing: The point already in effect at this time.
        """
        return (
            isinstance(existing, EffectControlPoint)
            and self.KiaiMode == existing.KiaiMode
            and self.ScrollSpeed == existing.ScrollSpeed
        )


DEFAULT = EffectControlPoint()
