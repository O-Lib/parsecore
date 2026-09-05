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


class StageDefinition:
    """One stage of the playfield, and the columns it holds."""

    def __init__(self, columns: int) -> None:
        """Create a stage.

        Args:
            columns: How many columns the stage has.

        Raises:
            ValueError: If the stage would have no columns.
        """
        if columns < 1:
            raise ValueError("column count must be above zero")

        self.Columns = columns

    def IsSpecialColumn(self, column: int) -> bool:
        """Return whether a column is the stage's special one.

        Only a stage with an odd number of columns has one, and it is the
        middle column.

        Args:
            column: The column to test, counted from the left.
        """
        return self.Columns % 2 == 1 and column == self.Columns // 2
