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

from parsecore.Rulesets.Objects.Types.IHasPath import IHasPath
from parsecore.Rulesets.Objects.Types.IHasRepeats import IHasRepeats, SpanCount
from parsecore.Utils.Vector2 import Vector2


class IHasPathWithRepeats(IHasPath, IHasRepeats):
    """A HitObject that has a curve."""

    def CurvePositionAt(self, progress: float) -> Vector2:
        """
        Computes the position on the curve relative
        to how much of the ``HitObject`` has been completed.

        Args:
            progress: 0 is the start time of the ``HitObject`` and 1 is the end time of the ``HitObject``

        Return:
            Vector2: The position on the curve.
        """
        return self.Path.PositionAt(self.ProgressAt(progress))

    def ProgressAt(self, progress: float) -> float:
        """
        Computes the progress along the curve relative
        to how much of the ``HitObject`` has been completed.

        Args:
            progress: 0 is the start time of the ``HitObject`` and 1 is the end time of the ``HitObject``

        Return:
            0 or 1, where 0 is the beginning of the curve and 1 is the end of the curve.
        """
        p = progress * SpanCount(self) % 1

        if self.SpanAt(progress) % 2 == 1:
            p = 1 - p

        return p

    def SpanAt(self, progress: float) -> int:
        """
        Determines which span of the curve the progress point is on.

        Args:
            progress: 0 is the beginning of the curve and 1 is the end of the curve.

        Return:
            0 or SpanCount's value, where 0 is the first run.
        """

        return int(progress * SpanCount(self))
