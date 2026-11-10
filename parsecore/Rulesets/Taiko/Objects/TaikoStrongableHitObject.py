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

from parsecore.Audio.HitSampleInfo import HIT_FINISH
from parsecore.Rulesets.Taiko.Objects.TaikoHitObject import TaikoHitObject

# A strong note is drawn larger than a normal one.
STRONG_SCALE = 1 / 0.65
DEFAULT_STRONG_SIZE = 0.475 * STRONG_SCALE


class TaikoStrongableHitObject(TaikoHitObject):
    """A note that is strong when it carries a finish sample."""

    def __init__(self) -> None:
        """Create a strongable object."""
        # Set before the base class, which assigns empty samples and so reads
        # this back through the setter below.
        self._is_strong = False
        super().__init__()
        self._read_from_samples()

    @property
    def IsStrong(self) -> bool:
        """Return whether this note is struck with both hands."""
        return self._is_strong

    @IsStrong.setter
    def IsStrong(self, value: bool) -> None:
        """Set whether this note is struck with both hands.

        osu! drives this through a bindable, so writing it rewrites the samples
        to match, and the samples are then read back. That round trip can undo
        the write: a note whose sound the beatmap named by file cannot be given
        a finish sample, so it stays weak however the converter asks.

        Args:
            value: Whether the note is strong.
        """
        if value == self._is_strong:
            return

        self._is_strong = value
        self._write_strength_to_samples()

    def CreateNestedHitObjects(self) -> None:
        """Add the second hand's hit if this note is strong."""
        super().CreateNestedHitObjects()

        if self.IsStrong:
            self.AddNested(self.CreateStrongNestedHit(self.GetEndTime()))

    def CreateStrongNestedHit(self, start_time: float):
        """Return the nested object standing in for the second hand.

        Args:
            start_time: When the second hand lands.

        Returns:
            The nested strong hit object.
        """
        raise NotImplementedError

    def _read_from_samples(self) -> None:
        """Derive whether this note is strong from its samples.

        Subclasses extend this to read the rest of what the samples encode.
        """
        self.IsStrong = any(s.Name == HIT_FINISH for s in self.Samples)

    def _write_strength_to_samples(self) -> None:
        """Add or remove the finish sample this note's strength implies."""
        strong_samples = [s for s in self.Samples if s.Name == HIT_FINISH]

        if self._is_strong == bool(strong_samples):
            return

        if self._is_strong:
            self.Samples.append(self.CreateHitSampleInfo(HIT_FINISH))
        else:
            for sample in strong_samples:
                self.Samples.remove(sample)

        self._read_from_samples()
