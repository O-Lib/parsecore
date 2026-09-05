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

from parsecore.Audio.HitSampleInfo import HIT_FINISH, HIT_NORMAL
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.LegacyPatternGenerator import (
    LegacyPatternGenerator,
)
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.PatternType import PatternType
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Pattern import Pattern
from parsecore.Rulesets.Mania.Objects.HoldNote import HoldNote
from parsecore.Rulesets.Mania.Objects.Note import Note


class SpinnerPatternGenerator(LegacyPatternGenerator):
    """Turns one spinner into the object it becomes on a mania stage."""

    def __init__(
        self, random, hit_object, beatmap, total_columns: int, previous_pattern
    ) -> None:
        """Create a generator for one spinner.

        Args:
            random: The generator the whole conversion draws from.
            hit_object: The spinner to convert.
            beatmap: The beatmap it belongs to.
            total_columns: How many columns the stage has.
            previous_pattern: The notes generated for the object before it.
        """
        super().__init__(random, hit_object, beatmap, total_columns, previous_pattern)

        end_time = getattr(hit_object, "EndTime", None)
        self._end_time = int(end_time) if end_time is not None else 0

        self._convert_type = (
            PatternType.None_
            if self.PreviousPattern.ColumnWithObjects == self.TotalColumns
            else PatternType.ForceNotStack
        )

    def Generate(self) -> list:
        """Return the single pattern for this spinner."""
        return [self._generate()]

    def _generate(self) -> Pattern:
        """Return the object this spinner becomes."""
        pattern = Pattern()

        generate_hold = self._end_time - self.HitObject.StartTime >= 100

        if (
            self.TotalColumns == 8
            and any(s.Name == HIT_FINISH for s in self.HitObject.Samples)
            and self._end_time - self.HitObject.StartTime < 1000
        ):
            self._add_to_pattern(pattern, 0, generate_hold)
        elif self.TotalColumns == 8:
            self._add_to_pattern(pattern, self._get_random_column(), generate_hold)
        else:
            self._add_to_pattern(pattern, self._get_random_column(0), generate_hold)

        return pattern

    def _get_random_column(self, lower_bound: int | None = None) -> int:
        """Return a free column drawn at random.

        Args:
            lower_bound: The lowest column allowed.
        """
        if self._convert_type & PatternType.ForceNotStack:
            return self.FindAvailableColumn(
                self.GetRandomColumn(lower_bound),
                self.PreviousPattern,
                lower_bound=lower_bound,
            )

        return self.FindAvailableColumn(
            self.GetRandomColumn(lower_bound), lower_bound=lower_bound
        )

    def _add_to_pattern(self, pattern: Pattern, column: int, hold_note: bool) -> None:
        """Add the spinner's object to a pattern.

        Args:
            pattern: The pattern to add to.
            column: The column to place it in.
            hold_note: Whether it is long enough to be held.
        """
        if hold_note:
            new_object = HoldNote(
                self.HitObject.StartTime,
                column,
                self._end_time - self.HitObject.StartTime,
                node_samples=[
                    [s for s in self.HitObject.Samples if s.Name == HIT_NORMAL],
                    self.HitObject.Samples,
                ],
            )
            new_object.Samples = self.HitObject.Samples
        else:
            new_object = Note(self.HitObject.StartTime, column)
            new_object.Samples = self.HitObject.Samples

        pattern.Add(new_object)
