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

_UINT_MASK = 0xFFFFFFFF
_INT_MASK = 0x7FFFFFFF
_INT_TO_REAL = 1.0 / (0x7FFFFFFF + 1.0)

# The generator's fixed starting state, beyond the seed.
_Y = 842502087
_Z = 3579807591
_W = 273326509


class LegacyRandom:
    """osu!stable's xorshift generator."""

    def __init__(self, seed: int = 0) -> None:
        """Create a generator.

        Args:
            seed: The number to start from.
        """
        self.X = seed & _UINT_MASK
        self.Y = _Y
        self.Z = _Z
        self.W = _W

        self._bit_buffer = 0
        self._bit_index = 32

    def NextUInt(self) -> int:
        """Return the next raw value and advance the state."""
        t = (self.X ^ (self.X << 11)) & _UINT_MASK
        self.X = self.Y
        self.Y = self.Z
        self.Z = self.W
        self.W = (self.W ^ (self.W >> 19) ^ t ^ (t >> 8)) & _UINT_MASK
        return self.W

    def Next(self, lower_bound: float | None = None, upper_bound: float | None = None) -> int:
        """Return the next whole number.

        With no bounds this is the raw value with its sign bit cleared; with one
        bound it falls below it; with two it falls between them.

        Args:
            lower_bound: The lower bound, or the upper one when given alone.
            upper_bound: The upper bound.

        Returns:
            The number, truncated towards zero as osu! casts it.
        """
        if lower_bound is None:
            return _INT_MASK & self.NextUInt()

        if upper_bound is None:
            return int(self.NextDouble() * lower_bound)

        return int(lower_bound + self.NextDouble() * (upper_bound - lower_bound))

    def NextDouble(self) -> float:
        """Return the next value between zero and one."""
        return _INT_TO_REAL * self.Next()

    def NextBool(self) -> bool:
        """Return the next single bit, drawing a fresh value when spent."""
        if self._bit_index == 32:
            self._bit_buffer = self.NextUInt()
            self._bit_index = 1
            return (self._bit_buffer & 1) == 1

        self._bit_index += 1
        self._bit_buffer >>= 1
        return (self._bit_buffer & 1) == 1
