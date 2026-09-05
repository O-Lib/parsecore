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


class PatternGenerator:
    """The base of every way an object becomes mania notes."""

    def __init__(self, hit_object, beatmap, total_columns: int, previous_pattern) -> None:
        """Create a generator for one object.

        Args:
            hit_object: The object to generate notes for.
            beatmap: The beatmap it belongs to.
            total_columns: How many columns the stage has.
            previous_pattern: The notes generated for the object before it.
        """
        self.HitObject = hit_object
        self.Beatmap = beatmap
        self.PreviousPattern = previous_pattern
        self.TotalColumns = total_columns

    def Generate(self) -> list:
        """Return the patterns of notes for this object."""
        raise NotImplementedError
