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

import math

from parsecore.Rulesets.Mania.Beatmaps.Patterns.PatternGenerator import PatternGenerator
from parsecore.Utils.Vector2 import f32


class NotEnoughColumnsError(Exception):
    """Raised when no column is left to place a note in."""

    def __init__(self) -> None:
        """Create the error."""
        super().__init__("there were not enough columns to complete conversion")


class LegacyPatternGenerator(PatternGenerator):
    """The base of the generators osu!stable converted beatmaps with."""

    def __init__(
        self, random, hit_object, beatmap, total_columns: int, previous_pattern
    ) -> None:
        """Create a generator for one object.

        Args:
            random: The generator the whole conversion draws from.
            hit_object: The object to generate notes for.
            beatmap: The beatmap it belongs to.
            total_columns: How many columns the stage has.
            previous_pattern: The notes generated for the object before it.
        """
        super().__init__(hit_object, beatmap, total_columns, previous_pattern)

        self.Random = random
        # On a seven key stage plus a special column, the leftmost column is
        # reserved and never drawn at random.
        self.RandomStart = 1 if self.TotalColumns == 8 else 0
        self._conversion_difficulty: float | None = None

    def GetColumn(self, position: float, allow_special: bool = False) -> int:
        """Return the column an x position falls in.

        Args:
            position: The x position in the source beatmap.
            allow_special: Whether to read the stage as seven keys plus one.
        """
        # Both the divisor and the division are single precision in osu!,
        # which decides which side of a column boundary a note lands on.
        if allow_special and self.TotalColumns == 8:
            local_x_divisor = f32(512.0 / 7)
            column = int(math.floor(f32(f32(position) / local_x_divisor)))
            return min(max(column, 0), 6) + 1

        local_x_divisor = f32(512.0 / self.TotalColumns)
        column = int(math.floor(f32(f32(position) / local_x_divisor)))
        return min(max(column, 0), self.TotalColumns - 1)

    def GetRandomNoteCount(
        self, p2: float, p3: float, p4: float = 0.0, p5: float = 0.0, p6: float = 0.0
    ) -> int:
        """Return how many notes to generate, drawn against probabilities.

        Args:
            p2: The chance of generating two notes.
            p3: The chance of generating three.
            p4: The chance of generating four.
            p5: The chance of generating five.
            p6: The chance of generating six.

        Raises:
            ValueError: If any probability lies outside zero to one.
        """
        for probability in (p2, p3, p4, p5, p6):
            if probability < 0 or probability > 1:
                raise ValueError("probability must be between zero and one")

        value = self.Random.NextDouble()

        if value >= 1 - p6:
            return 6
        if value >= 1 - p5:
            return 5
        if value >= 1 - p4:
            return 4
        if value >= 1 - p3:
            return 3

        return 2 if value >= 1 - p2 else 1

    @property
    def ConversionDifficulty(self) -> float:
        """Return the difficulty figure osu!stable converted beatmaps against.

        This is not the star rating; it is a rough number from the drain rate,
        the approach rate and how densely the beatmap is packed, and it decides
        which set of probabilities a pattern is drawn against.
        """
        if self._conversion_difficulty is not None:
            return self._conversion_difficulty

        hit_objects = self.Beatmap.HitObjects
        last_object = hit_objects[-1] if hit_objects else None
        first_object = hit_objects[0] if hit_objects else None

        # The drain time in whole seconds.
        drain_time = int(
            (
                (last_object.StartTime if last_object is not None else 0)
                - (first_object.StartTime if first_object is not None else 0)
                - self.Beatmap.TotalBreakTime
            )
            / 1000
        )

        if drain_time == 0:
            drain_time = 10000

        difficulty = self.Beatmap.Difficulty
        # The two settings are single precision, so they are added there
        # before the rest of the expression widens them.
        settings = f32(
            f32(difficulty.DrainRate) + f32(min(max(difficulty.ApproachRate, 4.0), 7.0))
        )
        value = (
            settings / 1.5 + len(hit_objects) / drain_time * 9.0
        ) / 38.0 * 5.0 / 1.15

        self._conversion_difficulty = min(value, 12.0)
        return self._conversion_difficulty

    def FindAvailableColumn(
        self,
        initial_column: int,
        *patterns,
        lower_bound: int | None = None,
        upper_bound: int | None = None,
        next_column=None,
        validation=None,
    ) -> int:
        """Return a column no given pattern has a note in yet.

        Args:
            initial_column: The column to try first, which may be returned.
            patterns: The patterns a candidate column must be free in.
            lower_bound: The lowest column allowed.
            upper_bound: One past the highest column allowed.
            next_column: How to pick the next candidate, drawn at random
                by default.
            validation: A further test a candidate column must pass.

        Raises:
            NotEnoughColumnsError: If no column is free.
        """
        if lower_bound is None:
            lower_bound = self.RandomStart
        if upper_bound is None:
            upper_bound = self.TotalColumns
        if next_column is None:
            def next_column(_):
                return self.GetRandomColumn(lower_bound, upper_bound)

        def is_valid(column: int) -> bool:
            if validation is not None and not validation(column):
                return False
            return not any(pattern.ColumnHasObject(column) for pattern in patterns)

        if is_valid(initial_column):
            return initial_column

        has_valid_columns = False
        for i in range(lower_bound, upper_bound):
            has_valid_columns = is_valid(i)
            if has_valid_columns:
                break

        if not has_valid_columns:
            raise NotEnoughColumnsError()

        while True:
            initial_column = next_column(initial_column)
            if is_valid(initial_column):
                return initial_column

    def GetRandomColumn(
        self, lower_bound: int | None = None, upper_bound: int | None = None
    ) -> int:
        """Return a column drawn at random.

        Args:
            lower_bound: The lowest column allowed.
            upper_bound: One past the highest column allowed.
        """
        return self.Random.Next(
            self.RandomStart if lower_bound is None else lower_bound,
            self.TotalColumns if upper_bound is None else upper_bound,
        )
