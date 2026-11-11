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
from parsecore.Rulesets.Objects.Legacy.ConvertHitObject import ConvertHitObject
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration


class ConvertHold(ConvertHitObject, IHasDuration):
    """A note held down for a duration."""

    def __init__(self) -> None:
        """Create a hold note."""

        super().__init__()
        self.LegacyType = LegacyHitObjectType.Hold
        self.Duration: float = 0.0

    @property
    def EndTime(self) -> float:
        """Return the end time of the hold note in milliseconds."""
        return self.StartTime + self.Duration
