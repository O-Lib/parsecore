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

# The spacing changes a player reads as musical rather than as a mistake.
COMMON_RATIOS = (
    1.0 / 1,
    2.0 / 1,
    1.0 / 2,
    3.0 / 1,
    1.0 / 3,
    3.0 / 2,
    2.0 / 3,
    5.0 / 4,
    4.0 / 5,
)


class TaikoRhythmData:
    """The rhythm groupings one note belongs to, and its spacing ratio."""

    def __init__(self, current) -> None:
        """Read a note's spacing ratio against the note before it.

        The raw ratio is snapped to the nearest musical one, so a rhythm the
        mapper meant as a half-speed passage reads as exactly that.

        Args:
            current: The difficulty object to read.
        """
        self.SameRhythmGroupedHitObjects = None
        self.SamePatternsGroupedHitObjects = None

        previous = current.Previous(0)

        if previous is None:
            self.Ratio: float = 1.0
            return

        actual_ratio = current.DeltaTime / previous.DeltaTime
        self.Ratio = min(COMMON_RATIOS, key=lambda r: abs(r - actual_ratio))
