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

from parsecore.Rulesets.Objects.Types.PathType import PathType
from parsecore.Utils.Vector2 import Vector2


@dataclass(slots=True)
class PathControlPoint:
    """One control point, optionally starting a new path segment.

    A non-``None`` :attr:`Type` marks this point as the start of a new segment
    of that curve type; ``None`` continues the current segment.
    """

    Position: Vector2 = field(default_factory=Vector2)
    Type: PathType | None = None

    def __repr__(self) -> str:
        """Return an unambiguous representation."""
        return f"PathControlPoint({self.Position!r}, {self.Type!r})"
