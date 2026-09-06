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

# The minimum duration required for a break to be considered a break.
MIN_BREAK_DURATION = 650


@dataclass(slots=True)
class BreakPeriod:
    """A span of time during which no objects are hit."""

    StartTime: float = 0.0
    EndTime: float = 0.0

    @property
    def Duration(self) -> float:
        """Return the break's length in milliseconds."""
        return self.EndTime - self.StartTime

    @property
    def HasEffect(self) -> bool:
        """Return whether the break is long enough to count as one."""
        return self.Duration >= MIN_BREAK_DURATION

    def Contains(self, time: float) -> bool:
        """Return whether ``time`` falls inside this break.

        Args:
            time: The time in milliseconds.
        """
        return self.StartTime <= time <= self.EndTime
