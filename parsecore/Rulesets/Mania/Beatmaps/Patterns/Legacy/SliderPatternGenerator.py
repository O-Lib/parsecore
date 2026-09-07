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

from parsecore.Audio.HitSampleInfo import HIT_CLAP, HIT_FINISH, HIT_WHISTLE
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.LegacyPatternGenerator import (
    LegacyPatternGenerator,
)
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.PatternType import PatternType
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Pattern import Pattern
from parsecore.Rulesets.Mania.Objects.HoldNote import HoldNote
from parsecore.Rulesets.Mania.Objects.Note import Note
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    GetPrecisionAdjustedBeatLength,
)


class SliderPatternGenerator(LegacyPatternGenerator):
    """Turns one slider into the notes and holds it becomes."""

    def __init__(
        self, random, hit_object, beatmap, total_columns: int, previous_pattern
    ) -> None:
        """Create a generator for one slider.

        Args:
            random: The generator the whole conversion draws from.
            hit_object: The slider to convert.
            beatmap: The beatmap it belongs to.
            total_columns: How many columns the stage has.
            previous_pattern: The notes generated for the object before it.
        """
        super().__init__(random, hit_object, beatmap, total_columns, previous_pattern)

        self._convert_type = PatternType.None_
        if not beatmap.ControlPointInfo.EffectPointAt(hit_object.StartTime).KiaiMode:
            self._convert_type = PatternType.LowProbability

        timing_point = beatmap.ControlPointInfo.TimingPointAt(hit_object.StartTime)

        if hasattr(hit_object, "SliderVelocityMultiplier"):
            beat_length = GetPrecisionAdjustedBeatLength(
                hit_object, timing_point, "mania"
            )
        else:
            beat_length = timing_point.BeatLength

        self.SpanCount = getattr(hit_object, "SpanCount", 1)
        self.StartTime = int(round(hit_object.StartTime))

        distance = hit_object.Path.ExpectedDistance
        if distance is None:
            distance = 0.0

        # This matches what osu!stable worked out.
        self.EndTime = int(
            math.floor(
                self.StartTime
                + distance * beat_length * self.SpanCount * 0.01
                / beatmap.Difficulty.SliderMultiplier
            )
        )

        # osu! divides two whole numbers here, truncating towards zero.
        self.SegmentDuration = int((self.EndTime - self.StartTime) / self.SpanCount)

    def _has_flag(self, flag: PatternType) -> bool:
        """Return whether a pattern flag is set.

        Args:
            flag: The flag to test for.
        """
        return bool(self._convert_type & flag)

    def Generate(self) -> list:
        """Return the patterns of notes and holds for this slider.

        A slider that became more than one object is split in two: everything
        that finishes early, and everything that finishes with the slider. Only
        the second is carried forward, because that is what the next object is
        generated against.
        """
        original_pattern = self._generate()

        if len(original_pattern.HitObjects) == 1:
            return [original_pattern]

        intermediate_pattern = Pattern()
        end_time_pattern = Pattern()

        for hit_object in original_pattern.HitObjects:
            if self.EndTime != int(round(hit_object.GetEndTime())):
                intermediate_pattern.Add(hit_object)
            else:
                end_time_pattern.Add(hit_object)

        return [intermediate_pattern, end_time_pattern]

    def _generate(self) -> Pattern:
        """Return everything this slider becomes, in one pattern."""
        if self.TotalColumns == 1:
            pattern = Pattern()
            self._add_to_pattern(pattern, 0, self.StartTime, self.EndTime)
            return pattern

        if self.SpanCount > 1:
            if self.SegmentDuration <= 90:
                return self._generate_random_hold_notes(self.StartTime, 1)

            if self.SegmentDuration <= 120:
                self._convert_type |= PatternType.ForceNotStack
                return self._generate_random_notes(self.StartTime, self.SpanCount + 1)

            if self.SegmentDuration <= 160:
                return self._generate_stair(self.StartTime)

            if self.SegmentDuration <= 200 and self.ConversionDifficulty > 3:
                return self._generate_random_multiple_notes(self.StartTime)

            duration = self.EndTime - self.StartTime
            if duration >= 4000:
                return self._generate_n_random_notes(self.StartTime, 0.23, 0, 0)

            if (
                self.SegmentDuration > 400
                and self.SpanCount < self.TotalColumns - 1 - self.RandomStart
            ):
                return self._generate_tiled_hold_notes(self.StartTime)

            return self._generate_hold_and_normal_notes(self.StartTime)

        if self.SegmentDuration <= 110:
            if self.PreviousPattern.ColumnWithObjects < self.TotalColumns:
                self._convert_type |= PatternType.ForceNotStack
            else:
                self._convert_type &= ~PatternType.ForceNotStack
            return self._generate_random_notes(
                self.StartTime, 1 if self.SegmentDuration < 80 else 2
            )

        if self.ConversionDifficulty > 6.5:
            if self._has_flag(PatternType.LowProbability):
                return self._generate_n_random_notes(self.StartTime, 0.78, 0.3, 0)

            return self._generate_n_random_notes(self.StartTime, 0.85, 0.36, 0.03)

        if self.ConversionDifficulty > 4:
            if self._has_flag(PatternType.LowProbability):
                return self._generate_n_random_notes(self.StartTime, 0.43, 0.08, 0)

            return self._generate_n_random_notes(self.StartTime, 0.56, 0.18, 0)

        if self.ConversionDifficulty > 2.5:
            if self._has_flag(PatternType.LowProbability):
                return self._generate_n_random_notes(self.StartTime, 0.3, 0, 0)

            return self._generate_n_random_notes(self.StartTime, 0.37, 0.08, 0)

        if self._has_flag(PatternType.LowProbability):
            return self._generate_n_random_notes(self.StartTime, 0.17, 0, 0)

        return self._generate_n_random_notes(self.StartTime, 0.27, 0, 0)

    def _generate_random_hold_notes(self, start_time: int, note_count: int) -> Pattern:
        """Return holds that all begin and end together.

        Args:
            start_time: When each hold begins.
            note_count: How many holds to generate.
        """
        pattern = Pattern()

        usable_columns = (
            self.TotalColumns - self.RandomStart - self.PreviousPattern.ColumnWithObjects
        )
        next_column = self.GetRandomColumn()

        for _ in range(min(usable_columns, note_count)):
            next_column = self.FindAvailableColumn(
                next_column, pattern, self.PreviousPattern
            )
            self._add_to_pattern(pattern, next_column, start_time, self.EndTime)

        # This cannot be folded into the loop above: the two search different
        # patterns, so they draw different numbers.
        for _ in range(note_count - usable_columns):
            next_column = self.FindAvailableColumn(next_column, pattern)
            self._add_to_pattern(pattern, next_column, start_time, self.EndTime)

        return pattern

    def _generate_random_notes(self, start_time: int, note_count: int) -> Pattern:
        """Return one note per row, never twice in the same column.

        Args:
            start_time: When the first note is.
            note_count: How many notes to generate.
        """
        pattern = Pattern()

        next_column = self.GetColumn(getattr(self.HitObject, "X", 0.0), True)
        if (
            self._has_flag(PatternType.ForceNotStack)
            and self.PreviousPattern.ColumnWithObjects < self.TotalColumns
        ):
            next_column = self.FindAvailableColumn(next_column, self.PreviousPattern)

        last_column = next_column

        for _ in range(note_count):
            self._add_to_pattern(pattern, next_column, start_time, start_time)
            # The column to avoid is the one standing now, so it is bound
            # here rather than read when the check runs.
            next_column = self.FindAvailableColumn(
                next_column, validation=lambda c, avoid=last_column: c != avoid
            )
            last_column = next_column
            start_time += self.SegmentDuration

        return pattern

    def _generate_stair(self, start_time: int) -> Pattern:
        """Return a staircase of notes that turns around at the stage edges.

        Args:
            start_time: When the first note is.
        """
        pattern = Pattern()

        column = self.GetColumn(getattr(self.HitObject, "X", 0.0), True)
        increasing = self.Random.NextDouble() > 0.5

        for _ in range(self.SpanCount + 1):
            self._add_to_pattern(pattern, column, start_time, start_time)
            start_time += self.SegmentDuration

            if increasing:
                if column >= self.TotalColumns - 1:
                    increasing = False
                    column -= 1
                else:
                    column += 1
            else:
                if column <= self.RandomStart:
                    increasing = True
                    column += 1
                else:
                    column -= 1

        return pattern

    def _generate_random_multiple_notes(self, start_time: int) -> Pattern:
        """Return one or two notes per row, never stacked.

        Args:
            start_time: When the first row is.
        """
        pattern = Pattern()

        legacy = 4 <= self.TotalColumns <= 8
        interval = self.Random.Next(1, self.TotalColumns - (1 if legacy else 0))

        next_column = self.GetColumn(getattr(self.HitObject, "X", 0.0), True)

        for _ in range(self.SpanCount + 1):
            self._add_to_pattern(pattern, next_column, start_time, start_time)

            next_column += interval
            if next_column >= self.TotalColumns - self.RandomStart:
                next_column = (
                    next_column
                    - self.TotalColumns
                    - self.RandomStart
                    + (1 if legacy else 0)
                )
            next_column += self.RandomStart

            # On a two column stage, back-to-back chords would be too much.
            if self.TotalColumns > 2:
                self._add_to_pattern(pattern, next_column, start_time, start_time)

            next_column = self.GetRandomColumn()
            start_time += self.SegmentDuration

        return pattern

    def _generate_n_random_notes(
        self, start_time: int, p2: float, p3: float, p4: float
    ) -> Pattern:
        """Return holds, how many being drawn against probabilities.

        Args:
            start_time: When the holds begin.
            p2: The chance of generating two holds.
            p3: The chance of generating three.
            p4: The chance of generating four.
        """
        match self.TotalColumns:
            case 2:
                p2 = p3 = p4 = 0
            case 3:
                p2 = min(p2, 0.1)
                p3 = p4 = 0
            case 4:
                p2 = min(p2, 0.3)
                p3 = min(p3, 0.04)
                p4 = 0
            case 5:
                p2 = min(p2, 0.34)
                p3 = min(p3, 0.1)
                p4 = min(p4, 0.03)

        def is_double_sample(sample) -> bool:
            return sample.Name in (HIT_CLAP, HIT_FINISH)

        can_generate_two_notes = not self._has_flag(PatternType.LowProbability)
        can_generate_two_notes &= any(
            is_double_sample(s) for s in self.HitObject.Samples
        ) or any(is_double_sample(s) for s in self._sample_info_list_at(self.StartTime))

        if can_generate_two_notes:
            p2 = 1

        return self._generate_random_hold_notes(
            start_time, self.GetRandomNoteCount(p2, p3, p4)
        )

    def _generate_tiled_hold_notes(self, start_time: int) -> Pattern:
        """Return holds that start one after another and end together.

        Args:
            start_time: When the first hold begins.
        """
        pattern = Pattern()

        column_repeat = min(self.SpanCount, self.TotalColumns)

        # Integer division means this need not land on the slider's own end.
        end_time = start_time + self.SegmentDuration * self.SpanCount

        next_column = self.GetColumn(getattr(self.HitObject, "X", 0.0), True)
        if (
            self._has_flag(PatternType.ForceNotStack)
            and self.PreviousPattern.ColumnWithObjects < self.TotalColumns
        ):
            next_column = self.FindAvailableColumn(next_column, self.PreviousPattern)

        for _ in range(column_repeat):
            next_column = self.FindAvailableColumn(next_column, pattern)
            self._add_to_pattern(pattern, next_column, start_time, end_time)
            start_time += self.SegmentDuration

        return pattern

    def _generate_hold_and_normal_notes(self, start_time: int) -> Pattern:
        """Return one hold with rows of notes played alongside it.

        Args:
            start_time: When the hold begins.
        """
        pattern = Pattern()

        hold_column = self.GetColumn(getattr(self.HitObject, "X", 0.0), True)
        if (
            self._has_flag(PatternType.ForceNotStack)
            and self.PreviousPattern.ColumnWithObjects < self.TotalColumns
        ):
            hold_column = self.FindAvailableColumn(hold_column, self.PreviousPattern)

        self._add_to_pattern(pattern, hold_column, start_time, self.EndTime)

        next_column = self.GetRandomColumn()

        if self.ConversionDifficulty > 6.5:
            note_count = self.GetRandomNoteCount(0.63, 0)
        elif self.ConversionDifficulty > 4:
            note_count = self.GetRandomNoteCount(
                0.12 if self.TotalColumns < 6 else 0.45, 0
            )
        elif self.ConversionDifficulty > 2.5:
            note_count = self.GetRandomNoteCount(
                0 if self.TotalColumns < 6 else 0.24, 0
            )
        else:
            note_count = 0
        note_count = min(self.TotalColumns - 1, note_count)

        # A silent slider head plays nothing alongside the hold's first row.
        ignore_head = not any(
            s.Name in (HIT_WHISTLE, HIT_FINISH, HIT_CLAP)
            for s in self._sample_info_list_at(start_time)
        )

        row_pattern = Pattern()

        for _ in range(self.SpanCount + 1):
            if not (ignore_head and start_time == self.StartTime):
                for _ in range(note_count):
                    next_column = self.FindAvailableColumn(
                        next_column,
                        row_pattern,
                        validation=lambda c: c != hold_column,
                    )
                    self._add_to_pattern(
                        row_pattern, next_column, start_time, start_time
                    )

            pattern.Add(row_pattern)
            row_pattern.Clear()

            start_time += self.SegmentDuration

        return pattern

    def _sample_info_list_at(self, time: int) -> list:
        """Return the samples sounding at a point along the slider.

        Args:
            time: The time to read at.
        """
        node_samples = self._node_samples_at(time)
        if node_samples:
            return node_samples[0]
        return self.HitObject.Samples

    def _node_samples_at(self, time: int) -> list | None:
        """Return the node samples from a point along the slider onwards.

        Args:
            time: The time to read from.
        """
        node_samples = getattr(self.HitObject, "NodeSamples", None)
        if node_samples is None or not hasattr(self.HitObject, "Path"):
            return None

        index = (
            0
            if self.SegmentDuration == 0
            else int((time - self.StartTime) / self.SegmentDuration)
        )

        return node_samples if index == 0 else list(node_samples[index:])

    def _add_to_pattern(
        self, pattern: Pattern, column: int, start_time: int, end_time: int
    ) -> None:
        """Add one note or hold to a pattern.

        Args:
            pattern: The pattern to add to.
            column: The column to place it in.
            start_time: When it begins.
            end_time: When it ends, equal to the start for a plain note.
        """
        if start_time == end_time:
            new_object = Note(start_time, column)
            new_object.Samples = self._sample_info_list_at(start_time)
        else:
            new_object = HoldNote(
                start_time,
                column,
                end_time - start_time,
                play_sliding_samples=True,
                node_samples=self._node_samples_at(start_time),
            )
            new_object.Samples = self.HitObject.Samples

        pattern.Add(new_object)
