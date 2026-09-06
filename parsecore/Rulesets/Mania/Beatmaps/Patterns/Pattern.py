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


class Pattern:
    """The notes generated for one object, and the columns they fill."""

    def __init__(self) -> None:
        """Create an empty pattern."""
        self._hit_objects: list = []
        self._contained_columns: set[int] = set()

    @property
    def HitObjects(self) -> list:
        """Return every note in this pattern."""
        return self._hit_objects

    def ColumnHasObject(self, column: int) -> bool:
        """Return whether a column already holds a note.

        Args:
            column: The column to test.
        """
        return column in self._contained_columns

    @property
    def ColumnWithObjects(self) -> int:
        """Return how many columns this pattern fills."""
        return len(self._contained_columns)

    def Add(self, value) -> None:
        """Add a note, or every note of another pattern.

        Args:
            value: A mania object, or a pattern to copy from.
        """
        if isinstance(value, Pattern):
            for hit_object in value._hit_objects:
                self._hit_objects.append(hit_object)
                self._contained_columns.add(hit_object.Column)
            return

        self._hit_objects.append(value)
        self._contained_columns.add(value.Column)

    def Clear(self) -> None:
        """Remove every note from this pattern."""
        self._hit_objects.clear()
        self._contained_columns.clear()
