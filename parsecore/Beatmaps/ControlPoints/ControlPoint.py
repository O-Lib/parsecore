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

import copy
from dataclasses import dataclass


@dataclass(slots=True)
class ControlPoint:
    """A change that takes effect from :attr:`Time` onward."""

    Time: float = 0.0

    def IsRedundant(self, existing: ControlPoint) -> bool:
        """Return whether this point changes nothing over ``existing``.

        Args:
            existing: The point already in effect at this time.

        Returns:
            ``True`` if this point can be dropped.
        """
        raise NotImplementedError

    def DeepClone(self) -> ControlPoint:
        """Return a copy that shares nothing with this point."""
        return copy.deepcopy(self)

    def __lt__(self, other: ControlPoint) -> bool:
        """Order control points by time."""
        return self.Time < other.Time
