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

from parsecore.Beatmaps.BeatmapProcessor import BeatmapProcessor
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner
from parsecore.Utils.Vector2 import Vector2, f32

# How close two objects must be, in osu! pixels, to stack.
STACK_DISTANCE = 3.0

# Stacking was reworked in this beatmap format.
FIRST_MODERN_STACKING_VERSION = 6


class OsuBeatmapProcessor(BeatmapProcessor):
    """Assigns stack heights to overlapping osu! objects."""

    def PostProcess(self) -> None:
        """Reset and recompute every object's stack height."""
        super().PostProcess()

        hit_objects = self.Beatmap.HitObjects
        if not hit_objects:
            return

        for hit_object in hit_objects:
            hit_object.StackHeight = 0

        if self.Beatmap.BeatmapInfo.BeatmapVersion >= FIRST_MODERN_STACKING_VERSION:
            self._apply_stacking(0, len(hit_objects) - 1)
        else:
            self._apply_stacking_old()

    def _stack_threshold(self, hit_object) -> float:
        """Return how far apart in time two objects may stack.

        osu! truncates the preempt time to a whole number and keeps the result
        at single precision, both for osu!stable compatibility.

        Args:
            hit_object: The object whose preempt time sets the window.
        """
        return f32(
            int(hit_object.TimePreempt) * self.Beatmap.BeatmapInfo.StackLeniency
        )

    def _apply_stacking(self, start_index: int, end_index: int) -> None:
        """Stack objects the way osu! has since beatmap format v6.

        Args:
            start_index: The first object to consider.
            end_index: The last object to consider.
        """
        hit_objects = self.Beatmap.HitObjects

        extended_end_index = end_index

        if end_index < len(hit_objects) - 1:
            # Extend the range to cover objects later ones are stacked upon.
            for i in range(end_index, start_index - 1, -1):
                stack_base_index = i

                for n in range(stack_base_index + 1, len(hit_objects)):
                    stack_base_object = hit_objects[stack_base_index]
                    if isinstance(stack_base_object, Spinner):
                        break

                    object_n = hit_objects[n]
                    if isinstance(object_n, Spinner):
                        continue

                    end_time = stack_base_object.GetEndTime()
                    stack_threshold = self._stack_threshold(object_n)

                    if object_n.StartTime - end_time > stack_threshold:
                        break

                    if _close(
                        stack_base_object.Position, object_n.Position
                    ) or (
                        isinstance(stack_base_object, Slider)
                        and _close(stack_base_object.EndPosition, object_n.Position)
                    ):
                        stack_base_index = n
                        object_n.StackHeight = 0

                if stack_base_index > extended_end_index:
                    extended_end_index = stack_base_index
                    if extended_end_index == len(hit_objects) - 1:
                        break

        extended_start_index = start_index

        for i in range(extended_end_index, start_index, -1):
            n = i

            object_i = hit_objects[i]
            if object_i.StackHeight != 0 or isinstance(object_i, Spinner):
                continue

            stack_threshold = self._stack_threshold(object_i)

            if isinstance(object_i, HitCircle):
                while True:
                    n -= 1
                    if n < 0:
                        break

                    object_n = hit_objects[n]
                    if isinstance(object_n, Spinner):
                        continue

                    end_time = object_n.GetEndTime()
                    # Both times are truncated to whole milliseconds, because
                    # osu!stable subtracted two integers here.
                    if int(object_i.StartTime) - int(end_time) > stack_threshold:
                        break

                    if n < extended_start_index:
                        object_n.StackHeight = 0
                        extended_start_index = n

                    if isinstance(object_n, Slider) and _close(
                        object_n.EndPosition, object_i.Position
                    ):
                        # The circle continues the slider's own stack, so the
                        # objects between them shift down to meet it.
                        offset = object_i.StackHeight - object_n.StackHeight + 1

                        for j in range(n + 1, i + 1):
                            object_j = hit_objects[j]
                            if _close(object_n.EndPosition, object_j.Position):
                                object_j.StackHeight -= offset
                        break

                    if _close(object_n.Position, object_i.Position):
                        object_n.StackHeight = object_i.StackHeight + 1
                        object_i = object_n

            elif isinstance(object_i, Slider):
                while True:
                    n -= 1
                    if n < start_index:
                        break

                    object_n = hit_objects[n]
                    if isinstance(object_n, Spinner):
                        continue

                    if object_i.StartTime - object_n.StartTime > stack_threshold:
                        break

                    if _close(object_n.EndPosition, object_i.Position):
                        object_n.StackHeight = object_i.StackHeight + 1
                        object_i = object_n

    def _apply_stacking_old(self) -> None:
        """Stack objects the way osu! did before beatmap format v6."""
        hit_objects = self.Beatmap.HitObjects

        for i, current_hit_object in enumerate(hit_objects):
            if current_hit_object.StackHeight != 0 and not isinstance(
                current_hit_object, Slider
            ):
                continue

            start_time = current_hit_object.GetEndTime()
            slider_stack = 0

            for j in range(i + 1, len(hit_objects)):
                stack_threshold = self._stack_threshold(hit_objects[i])

                if hit_objects[j].StartTime - stack_threshold > start_time:
                    break

                position_2 = (
                    current_hit_object.Position
                    + current_hit_object.Path.PositionAt(1.0)
                    if isinstance(current_hit_object, Slider)
                    else current_hit_object.Position
                )

                if _close(hit_objects[j].Position, current_hit_object.Position):
                    current_hit_object.StackHeight += 1
                    start_time = hit_objects[j].StartTime
                elif _close(hit_objects[j].Position, position_2):
                    # Sliders shift the whole stack that follows them.
                    slider_stack += 1
                    hit_objects[j].StackHeight -= slider_stack
                    start_time = hit_objects[j].StartTime


def _close(a: Vector2, b: Vector2) -> bool:
    """Return whether two positions are near enough to stack.

    Args:
        a: The first position.
        b: The second position.
    """
    return Vector2.distance(a, b) < STACK_DISTANCE
