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

from parsecore.Rulesets.Taiko.Objects.Hit import Hit


class MonoStreak:
    """Consecutive notes of one colour, unbroken by the other."""

    def __init__(self) -> None:
        """Create an empty streak."""
        self.HitObjects: list = []
        self.Parent = None
        self.Index: int = 0

    @property
    def FirstHitObject(self):
        """Return the note the streak opens on."""
        return self.HitObjects[0]

    @property
    def LastHitObject(self):
        """Return the note the streak closes on."""
        return self.HitObjects[-1]

    @property
    def HitType(self):
        """Return which side of the drum the streak is played on."""
        base_object = self.HitObjects[0].BaseObject
        return base_object.Type if isinstance(base_object, Hit) else None

    @property
    def RunLength(self) -> int:
        """Return how many notes the streak holds."""
        return len(self.HitObjects)
