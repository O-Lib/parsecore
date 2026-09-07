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

from parsecore.Rulesets.Difficulty.Preprocessing.DifficultyHitObject import (
    DifficultyHitObject,
)


class ManiaDifficultyHitObject(DifficultyHitObject):
    """A mania note, and what the rest of the stage was doing."""

    def __init__(
        self,
        hit_object,
        last_object,
        clock_rate: float,
        objects: list,
        per_column_objects: list[list],
        index: int,
    ) -> None:
        """Create a difficulty object for one note.

        Args:
            hit_object: The note being rated.
            last_object: The note before it, in any column.
            clock_rate: The rate the beatmap is played at.
            objects: Every difficulty object built so far.
            per_column_objects: Those objects, split by column.
            index: This object's place among them.
        """
        super().__init__(hit_object, last_object, clock_rate, objects, index)

        total_columns = len(per_column_objects)
        self._per_column_objects = per_column_objects
        self.Column = hit_object.Column
        self._column_index = len(per_column_objects[self.Column])
        self.PreviousHitObjects: list = [None] * total_columns

        previous = self.PrevInColumn(0)
        self.ColumnStrainTime = (
            self.StartTime - previous.StartTime if previous is not None
            else self.StartTime
        )

        if index > 0:
            previous_note = objects[index - 1]

            for i in range(len(previous_note.PreviousHitObjects)):
                self.PreviousHitObjects[i] = previous_note.PreviousHitObjects[i]

            # This deliberately depends on the order objects are built in,
            # which is what osu! itself does.
            self.PreviousHitObjects[previous_note.Column] = previous_note

    def PrevInColumn(self, backwards_index: int):
        """Return an earlier note in this column, tails excluded.

        Args:
            backwards_index: How many notes to go back.
        """
        index = self._column_index - (backwards_index + 1)
        column = self._per_column_objects[self.Column]
        return column[index] if 0 <= index < len(column) else None

    def NextInColumn(self, forwards_index: int):
        """Return a later note in this column, tails excluded.

        Args:
            forwards_index: How many notes to go forward.
        """
        index = self._column_index + (forwards_index + 1)
        column = self._per_column_objects[self.Column]
        return column[index] if 0 <= index < len(column) else None
