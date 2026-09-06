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

from enum import IntFlag


class PatternType(IntFlag):
    """What kind of pattern to generate."""

    None_ = 0

    # Keep the same as the last row.
    ForceStack = 1

    # Keep different from the last row.
    ForceNotStack = 1 << 1

    # Keep as a single note at its original position.
    KeepSingle = 1 << 2

    # Use a lower random value.
    LowProbability = 1 << 3

    # Reserved.
    Alternate = 1 << 4

    # Ignore the repeat count.
    ForceSigSlider = 1 << 5

    # Convert the slider to a circle.
    ForceNotSlider = 1 << 6

    # Notes gathered together.
    Gathered = 1 << 7

    Mirror = 1 << 8

    # Change 0 to 6.
    Reverse = 1 << 9

    # 1 to 5 to 1 to 5, like reverse.
    Cycle = 1 << 10

    # The next note will be one column along.
    Stair = 1 << 11

    # The next note will be one column back.
    ReverseStair = 1 << 12
