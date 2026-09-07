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
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Colour.TaikoColourData import (
    TaikoColourData,
)
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Rhythm.TaikoRhythmData import (
    TaikoRhythmData,
)
from parsecore.Rulesets.Taiko.Objects.Hit import Hit
from parsecore.Rulesets.Taiko.Objects.HitType import HitType


class TaikoDifficultyHitObject(DifficultyHitObject):
    """A note with its place in the beatmap's colour and rhythm patterns."""

    def __init__(
        self,
        hit_object,
        last_object,
        clock_rate: float,
        objects: list,
        centre_hit_objects: list,
        rim_hit_objects: list,
        note_objects: list,
        index: int,
        control_point_info,
        global_slider_velocity: float,
    ) -> None:
        """Create a difficulty object and file it under the runs it belongs to.

        Args:
            hit_object: The note this describes.
            last_object: The object before it.
            clock_rate: The rate the beatmap is played at.
            objects: Every difficulty object built so far.
            centre_hit_objects: The centre notes built so far.
            rim_hit_objects: The rim notes built so far.
            note_objects: The notes built so far, of either colour.
            index: This object's place among ``objects``.
            control_point_info: The beatmap's control points.
            global_slider_velocity: The beatmap's slider multiplier.
        """
        super().__init__(hit_object, last_object, clock_rate, objects, index)

        self._note_difficulty_hit_objects = note_objects
        self._mono_difficulty_hit_objects: list | None = None
        self.MonoIndex: int = 0
        self.NoteIndex: int = 0

        self.ColourData = TaikoColourData()
        self.RhythmData = TaikoRhythmData(self)

        if isinstance(hit_object, Hit):
            match hit_object.Type:
                case HitType.Centre:
                    self.MonoIndex = len(centre_hit_objects)
                    centre_hit_objects.append(self)
                    self._mono_difficulty_hit_objects = centre_hit_objects

                case HitType.Rim:
                    self.MonoIndex = len(rim_hit_objects)
                    rim_hit_objects.append(self)
                    self._mono_difficulty_hit_objects = rim_hit_objects

            self.NoteIndex = len(note_objects)
            note_objects.append(self)

        # The control points are read at the beatmap's own speed, so the rate
        # is taken back out of the start time before looking them up.
        normalised_start_time = self.StartTime * clock_rate

        current_control_point = control_point_info.TimingPointAt(normalised_start_time)
        current_slider_velocity = _calculate_slider_velocity(
            control_point_info,
            global_slider_velocity,
            normalised_start_time,
            clock_rate,
        )

        self.EffectiveBPM: float = current_control_point.BPM * current_slider_velocity

    def PreviousMono(self, backwards_index: int):
        """Return an earlier note of this note's own colour.

        Args:
            backwards_index: How many notes of this colour to step back.
        """
        return _element_at(
            self._mono_difficulty_hit_objects,
            self.MonoIndex - (backwards_index + 1),
        )

    def NextMono(self, forwards_index: int):
        """Return a later note of this note's own colour.

        Args:
            forwards_index: How many notes of this colour to step forward.
        """
        return _element_at(
            self._mono_difficulty_hit_objects,
            self.MonoIndex + (forwards_index + 1),
        )

    def PreviousNote(self, backwards_index: int):
        """Return an earlier note, of either colour.

        Args:
            backwards_index: How many notes to step back.
        """
        return _element_at(
            self._note_difficulty_hit_objects,
            self.NoteIndex - (backwards_index + 1),
        )

    def NextNote(self, forwards_index: int):
        """Return a later note, of either colour.

        Args:
            forwards_index: How many notes to step forward.
        """
        return _element_at(
            self._note_difficulty_hit_objects,
            self.NoteIndex + (forwards_index + 1),
        )

    @property
    def Interval(self) -> float:
        """Return the gap to the object before this one."""
        return self.DeltaTime


def _calculate_slider_velocity(
    control_point_info,
    global_slider_velocity: float,
    start_time: float,
    clock_rate: float,
) -> float:
    """Return how fast the playfield scrolls at a point in time.

    Args:
        control_point_info: The beatmap's control points.
        global_slider_velocity: The beatmap's slider multiplier.
        start_time: When to sample, at the beatmap's own speed.
        clock_rate: The rate the beatmap is played at.
    """
    effect_point = control_point_info.EffectPointAt(start_time)
    return global_slider_velocity * effect_point.ScrollSpeed * clock_rate


def _element_at(items: list | None, index: int):
    """Return an item by index, or ``None`` where there is none.

    Args:
        items: The list to read, which may not exist.
        index: The index to read.
    """
    if items is None or index < 0 or index >= len(items):
        return None
    return items[index]
