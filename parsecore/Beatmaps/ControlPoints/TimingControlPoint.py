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

from dataclasses import dataclass, field

from parsecore.Beatmaps.ControlPoints.ControlPoint import ControlPoint
from parsecore.Beatmaps.Timing.TimeSignature import SIMPLE_QUADRUPLE
from parsecore.Beatmaps.Timing.TimeSignature import TimeSignature as TimeSignatureType
from parsecore.Utils.Precision import Clamp

DEFAULT_BEAT_LENGTH = 1000.0


@dataclass(slots=True)
class TimingControlPoint(ControlPoint):
    """Defines the beat length and time signature from a point onward."""

    BeatLength: float = DEFAULT_BEAT_LENGTH
    TimeSignature: TimeSignatureType = field(default_factory=lambda: SIMPLE_QUADRUPLE)
    OmitFirstBarLine: bool = False

    def __post_init__(self) -> None:
        """Clamp the beat length to the range osu! accepts."""
        self.BeatLength = Clamp(self.BeatLength, 6.0, 60000.0)

    @property
    def BPM(self) -> float:
        """Return the tempo in beats per minute."""
        return 60000.0 / self.BeatLength

    def IsRedundant(self, existing: ControlPoint | None) -> bool:
        """Return ``False``; timing points are never redundant.

        Args:
            existing: The point already in effect (unused).
        """
        return False

    def __eq__(self, value: object) -> bool:
        """Check equality with another timing control point.

        Args:
            value: The object to compare with.

        Returns:
            ``True`` if beat length, time signature, bar line settings, and time match.
        """
        if not isinstance(value, TimingControlPoint):
            raise NotImplementedError
        return (
            super().__eq__(value)
            and self.TimeSignature.__eq__(value)
            and self.OmitFirstBarLine == value.OmitFirstBarLine
            and self.BeatLength == value.BeatLength
        )


DEFAULT = TimingControlPoint(BeatLength=60000.0 / 60.0)
