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
from enum import IntEnum


class SplineType(IntEnum):
    """The spline family a path segment is built from."""

    Catmull = 0
    BSpline = 1
    Linear = 2
    PerfectCurve = 3


@dataclass(frozen=True, slots=True)
class PathType:
    """The type of a slider path segment, optionally with a B-spline degree."""

    type: SplineType = SplineType.BSpline
    degree: int | None = None

    @classmethod
    def from_legacy(cls, token: str) -> PathType:
        """Return the path type a legacy ``.osu`` curve token declares.

        A ``B`` may carry a B-spline degree, as in ``B3``. Anything
        unrecognised falls back to catmull, matching osu!.

        Args:
            token: The curve token, such as ``B``, ``L``, ``P``, ``C`` or ``B3``.

        Returns:
            The matching path type.
        """
        if not token:
            return CATMULL

        match token[0]:
            case "B":
                if len(token) > 1:
                    try:
                        degree = int(token[1:])
                    except ValueError:
                        degree = 0
                    if degree > 0:
                        return PathType(SplineType.BSpline, degree)
                return BEZIER
            case "L":
                return LINEAR
            case "P":
                return PERFECT_CURVE
            case _:
                return CATMULL


CATMULL = PathType(SplineType.Catmull)
BEZIER = PathType(SplineType.BSpline)
LINEAR = PathType(SplineType.Linear)
PERFECT_CURVE = PathType(SplineType.PerfectCurve)
