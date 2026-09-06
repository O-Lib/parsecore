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

from parsecore.Audio.HitSampleInfo import HIT_CLAP, HIT_FINISH
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.LegacyPatternGenerator import (
    LegacyPatternGenerator,
)
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.PatternType import PatternType
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Pattern import Pattern
from parsecore.Rulesets.Mania.Objects.Note import Note
from parsecore.Utils.Vector2 import Vector2


class HitCirclePatternGenerator(LegacyPatternGenerator):
    """Turns one circle into the notes it becomes on a mania stage."""

    def __init__(
        self,
        random,
        hit_object,
        beatmap,
        total_columns: int,
        previous_pattern,
        previous_time: float,
        previous_position: Vector2,
        density: float,
        last_stair: PatternType,
    ) -> None:
        """Create a generator for one circle.

        Args:
            random: The generator the whole conversion draws from.
            hit_object: The circle to convert.
            beatmap: The beatmap it belongs to.
            total_columns: How many columns the stage has.
            previous_pattern: The notes generated for the object before it.
            previous_time: When the last object was.
            previous_position: Where the last object was.
            density: How closely packed the last few objects have been.
            last_stair: Which way the last staircase was climbing.
        """
        super().__init__(random, hit_object, beatmap, total_columns, previous_pattern)

        self.StairType = last_stair
        self._convert_type = PatternType.None_

        timing_point = beatmap.ControlPointInfo.TimingPointAt(hit_object.StartTime)
        effect_point = beatmap.ControlPointInfo.EffectPointAt(hit_object.StartTime)

        position = getattr(hit_object, "Position", None) or Vector2()
        position_separation = (position - previous_position).length()
        time_separation = hit_object.StartTime - previous_time

        if time_separation <= 80:
            # More than 187 BPM.
            self._convert_type |= PatternType.ForceNotStack | PatternType.KeepSingle
        elif time_separation <= 95:
            # More than 157 BPM.
            self._convert_type |= (
                PatternType.ForceNotStack | PatternType.KeepSingle | last_stair
            )
        elif time_separation <= 105:
            # More than 140 BPM.
            self._convert_type |= PatternType.ForceNotStack | PatternType.LowProbability
        elif time_separation <= 125:
            # More than 120 BPM.
            self._convert_type |= PatternType.ForceNotStack
        elif time_separation <= 135 and position_separation < 20:
            # More than 111 BPM, and barely moving: a stream.
            self._convert_type |= PatternType.Cycle | PatternType.KeepSingle
        elif time_separation <= 150 and position_separation < 20:
            # More than 100 BPM, and barely moving: a slower stream.
            self._convert_type |= PatternType.ForceStack | PatternType.LowProbability
        elif position_separation < 20 and density >= timing_point.BeatLength / 2.5:
            # A low density stream.
            self._convert_type |= PatternType.Reverse | PatternType.LowProbability
        elif density < timing_point.BeatLength / 2.5 or effect_point.KiaiMode:
            # High density, which is left alone.
            pass
        else:
            self._convert_type |= PatternType.LowProbability

        if not self._has_flag(PatternType.KeepSingle):
            if (
                any(s.Name == HIT_FINISH for s in self.HitObject.Samples)
                and self.TotalColumns != 8
            ):
                self._convert_type |= PatternType.Mirror
            elif any(s.Name == HIT_CLAP for s in self.HitObject.Samples):
                self._convert_type |= PatternType.Gathered

    def _has_flag(self, flag: PatternType) -> bool:
        """Return whether a pattern flag is set.

        Args:
            flag: The flag to test for.
        """
        return bool(self._convert_type & flag)

    def Generate(self) -> list:
        """Return the single pattern of notes for this circle."""
        pattern = self._generate_core()

        for hit_object in pattern.HitObjects:
            if (
                self._has_flag(PatternType.Stair)
                and hit_object.Column == self.TotalColumns - 1
            ):
                self.StairType = PatternType.ReverseStair
            if (
                self._has_flag(PatternType.ReverseStair)
                and hit_object.Column == self.RandomStart
            ):
                self.StairType = PatternType.Stair

        return [pattern]

    def _generate_core(self) -> Pattern:
        """Return the notes this circle becomes, before the stair is updated."""
        pattern = Pattern()

        if self.TotalColumns == 1:
            self._add_to_pattern(pattern, 0)
            return pattern

        previous_objects = self.PreviousPattern.HitObjects
        last_column = previous_objects[0].Column if previous_objects else 0

        if self._has_flag(PatternType.Reverse) and previous_objects:
            # Copy the last row across, mirrored.
            for i in range(self.RandomStart, self.TotalColumns):
                if self.PreviousPattern.ColumnHasObject(i):
                    self._add_to_pattern(
                        pattern, self.RandomStart + self.TotalColumns - i - 1
                    )

            return pattern

        if (
            self._has_flag(PatternType.Cycle)
            and len(previous_objects) == 1
            # On seven keys plus one, leave the special column alone.
            and (self.TotalColumns != 8 or last_column != 0)
            # And leave the centre column alone.
            and (self.TotalColumns % 2 == 0 or last_column != self.TotalColumns // 2)
        ):
            # Mirror the single note of the last row.
            column = self.RandomStart + self.TotalColumns - last_column - 1
            self._add_to_pattern(pattern, column)

            return pattern

        if self._has_flag(PatternType.ForceStack) and previous_objects:
            # Repeat the last row exactly.
            for i in range(self.RandomStart, self.TotalColumns):
                if self.PreviousPattern.ColumnHasObject(i):
                    self._add_to_pattern(pattern, i)

            return pattern

        if len(previous_objects) == 1:
            if self._has_flag(PatternType.Stair):
                # Step one column along, wrapping back to the start.
                target_column = last_column + 1
                if target_column == self.TotalColumns:
                    target_column = self.RandomStart

                self._add_to_pattern(pattern, target_column)
                return pattern

            if self._has_flag(PatternType.ReverseStair):
                # Step one column back, wrapping round to the end.
                target_column = last_column - 1
                if target_column == self.RandomStart - 1:
                    target_column = self.TotalColumns - 1

                self._add_to_pattern(pattern, target_column)
                return pattern

        if self._has_flag(PatternType.KeepSingle):
            return self._generate_random_notes(1)

        if self._has_flag(PatternType.Mirror):
            if self.ConversionDifficulty > 6.5:
                return self._generate_random_pattern_with_mirrored(0.12, 0.38, 0.12)
            if self.ConversionDifficulty > 4:
                return self._generate_random_pattern_with_mirrored(0.12, 0.17, 0)

            return self._generate_random_pattern_with_mirrored(0.12, 0, 0)

        if self.ConversionDifficulty > 6.5:
            if self._has_flag(PatternType.LowProbability):
                return self._generate_random_pattern(0.78, 0.42, 0, 0)

            return self._generate_random_pattern(1, 0.62, 0, 0)

        if self.ConversionDifficulty > 4:
            if self._has_flag(PatternType.LowProbability):
                return self._generate_random_pattern(0.35, 0.08, 0, 0)

            return self._generate_random_pattern(0.52, 0.15, 0, 0)

        if self.ConversionDifficulty > 2:
            if self._has_flag(PatternType.LowProbability):
                return self._generate_random_pattern(0.18, 0, 0, 0)

            return self._generate_random_pattern(0.45, 0, 0, 0)

        return self._generate_random_pattern(0, 0, 0, 0)

    def _generate_random_notes(self, note_count: int) -> Pattern:
        """Return up to a number of notes in columns drawn at random.

        Fewer notes are generated than asked for where the pattern must not
        stack and there are not enough free columns left.

        Args:
            note_count: How many notes to generate.
        """
        pattern = Pattern()

        allow_stacking = not self._has_flag(PatternType.ForceNotStack)

        if not allow_stacking:
            note_count = min(
                note_count,
                self.TotalColumns
                - self.RandomStart
                - self.PreviousPattern.ColumnWithObjects,
            )

        next_column = self.GetColumn(getattr(self.HitObject, "X", 0.0), True)

        def get_next_column(last: int) -> int:
            if self._has_flag(PatternType.Gathered):
                last += 1
                if last == self.TotalColumns:
                    last = self.RandomStart
                return last

            return self.GetRandomColumn()

        for _ in range(note_count):
            if allow_stacking:
                next_column = self.FindAvailableColumn(
                    next_column, pattern, next_column=get_next_column
                )
            else:
                next_column = self.FindAvailableColumn(
                    next_column,
                    pattern,
                    self.PreviousPattern,
                    next_column=get_next_column,
                )

            self._add_to_pattern(pattern, next_column)

        return pattern

    @property
    def _has_special_column(self) -> bool:
        """Return whether this circle may fill the special column."""
        return any(s.Name == HIT_CLAP for s in self.HitObject.Samples) and any(
            s.Name == HIT_FINISH for s in self.HitObject.Samples
        )

    def _generate_random_pattern(
        self, p2: float, p3: float, p4: float, p5: float
    ) -> Pattern:
        """Return a row of notes in columns drawn at random.

        Args:
            p2: The chance of generating two notes.
            p3: The chance of generating three.
            p4: The chance of generating four.
            p5: The chance of generating five.
        """
        pattern = Pattern()

        pattern.Add(
            self._generate_random_notes(self._get_random_note_count(p2, p3, p4, p5))
        )

        if self.RandomStart > 0 and self._has_special_column:
            self._add_to_pattern(pattern, 0)

        return pattern

    def _generate_random_pattern_with_mirrored(
        self, centre_probability: float, p2: float, p3: float
    ) -> Pattern:
        """Return a row of notes paired across the middle of the stage.

        Args:
            centre_probability: The chance of also filling the centre column.
            p2: The chance of generating two pairs.
            p3: The chance of generating three.
        """
        if self._has_flag(PatternType.ForceNotStack):
            return self._generate_random_pattern(
                1 / 2 + p2 / 2, p2, (p2 + p3) / 2, p3
            )

        pattern = Pattern()

        note_count, add_to_centre = self._get_random_note_count_mirrored(
            centre_probability, p2, p3
        )

        column_limit = (
            self.TotalColumns if self.TotalColumns % 2 == 0 else self.TotalColumns - 1
        ) // 2
        next_column = self.GetRandomColumn(upper_bound=column_limit)

        for _ in range(note_count):
            next_column = self.FindAvailableColumn(
                next_column, pattern, upper_bound=column_limit
            )

            self._add_to_pattern(pattern, next_column)
            self._add_to_pattern(
                pattern, self.RandomStart + self.TotalColumns - next_column - 1
            )

        if add_to_centre:
            self._add_to_pattern(pattern, self.TotalColumns // 2)

        if self.RandomStart > 0 and self._has_special_column:
            self._add_to_pattern(pattern, 0)

        return pattern

    def _get_random_note_count(
        self, p2: float, p3: float, p4: float, p5: float
    ) -> int:
        """Return how many notes to generate, capped by the stage's width.

        Args:
            p2: The chance of generating two notes.
            p3: The chance of generating three.
            p4: The chance of generating four.
            p5: The chance of generating five.
        """
        match self.TotalColumns:
            case 2:
                p2 = p3 = p4 = p5 = 0
            case 3:
                p2 = min(p2, 0.1)
                p3 = p4 = p5 = 0
            case 4:
                p2 = min(p2, 0.23)
                p3 = min(p3, 0.04)
                p4 = p5 = 0
            case 5:
                p3 = min(p3, 0.15)
                p4 = min(p4, 0.03)
                p5 = 0

        if any(s.Name == HIT_CLAP for s in self.HitObject.Samples):
            p2 = 1

        return self.GetRandomNoteCount(p2, p3, p4, p5)

    def _get_random_note_count_mirrored(
        self, centre_probability: float, p2: float, p3: float
    ) -> tuple[int, bool]:
        """Return how many pairs to generate, and whether to fill the centre.

        Args:
            centre_probability: The chance of also filling the centre column.
            p2: The chance of generating two pairs.
            p3: The chance of generating three.

        Returns:
            The pair count, which excludes the centre note, and whether the
            centre column is filled.
        """
        match self.TotalColumns:
            case 2:
                centre_probability = 0
                p2 = p3 = 0
            case 3:
                centre_probability = min(centre_probability, 0.03)
                p2 = p3 = 0
            case 4:
                centre_probability = 0

                p2 = 1 - max((1 - p2) * 2, 0.8)
                p3 = 0
            case 5:
                centre_probability = min(centre_probability, 0.03)
                p3 = 0
            case 6:
                centre_probability = 0
                p2 = 1 - max((1 - p2) * 2, 0.5)
                p3 = 1 - max((1 - p3) * 2, 0.85)

        # osu!stable let these run past one, which reads as a negative
        # probability; they have to be pulled back into range.
        p2 = min(max(p2, 0.0), 1.0)
        p3 = min(max(p3, 0.0), 1.0)

        centre_value = self.Random.NextDouble()
        note_count = self.GetRandomNoteCount(p2, p3)

        add_to_centre = (
            self.TotalColumns % 2 != 0
            and note_count != 3
            and centre_value > 1 - centre_probability
        )
        return note_count, add_to_centre

    def _add_to_pattern(self, pattern: Pattern, column: int) -> None:
        """Add one note to a pattern.

        Args:
            pattern: The pattern to add to.
            column: The column to place the note in.
        """
        note = Note(self.HitObject.StartTime, column)
        note.Samples = self.HitObject.Samples
        pattern.Add(note)
