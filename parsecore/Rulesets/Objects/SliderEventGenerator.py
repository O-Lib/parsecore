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

from dataclasses import dataclass
from enum import IntEnum

# How close to the end of a span a tick may fall before it is dropped.
TICK_LENIENCY = 10.0

# A slider's tail is judged this much before the slider actually ends, so the
# player may release slightly early. Negative, as in osu!.
TAIL_LENIENCY = -36.0

# A very lenient upper bound on slider length before ticks stop being generated.
MAX_LENGTH = 100000.0


class SliderEventType(IntEnum):
    """The kind of event generated along a slider."""

    Tick = 0
    LegacyLastTick = 1
    Head = 2
    Tail = 3
    Repeat = 4


@dataclass(slots=True)
class SliderEventDescriptor:
    """One event along a slider's path."""

    Type: SliderEventType
    SpanIndex: int
    SpanStartTime: float
    Time: float
    PathProgress: float


def Generate(
    start_time: float,
    span_duration: float,
    velocity: float,
    tick_distance: float,
    total_distance: float,
    span_count: int,
) -> list[SliderEventDescriptor]:
    """Return every event along a slider, in time order.

    Args:
        start_time: The slider's start time.
        span_duration: How long one traversal of the path takes.
        velocity: The slider's velocity in osu! pixels per millisecond.
        tick_distance: The spacing between ticks, in osu! pixels.
        total_distance: The length of one span of the path.
        span_count: How many times the path is traversed.

    Returns:
        The slider's head, ticks, repeats and tail.
    """
    events: list[SliderEventDescriptor] = []

    length = min(MAX_LENGTH, total_distance)
    tick_distance = min(max(tick_distance, 0.0), length)

    min_distance_from_end = velocity * TICK_LENIENCY

    events.append(
        SliderEventDescriptor(
            Type=SliderEventType.Head,
            SpanIndex=0,
            SpanStartTime=start_time,
            Time=start_time,
            PathProgress=0.0,
        )
    )

    if tick_distance != 0:
        for span in range(span_count):
            span_start_time = start_time + span * span_duration
            reversed_span = span % 2 == 1

            ticks = _generate_ticks(
                span,
                span_start_time,
                span_duration,
                reversed_span,
                length,
                tick_distance,
                min_distance_from_end,
            )
            if reversed_span:
                ticks.reverse()
            events.extend(ticks)

            if span < span_count - 1:
                events.append(
                    SliderEventDescriptor(
                        Type=SliderEventType.Repeat,
                        SpanIndex=span,
                        SpanStartTime=start_time + span * span_duration,
                        Time=span_start_time + span_duration,
                        PathProgress=float((span + 1) % 2),
                    )
                )

    total_duration = span_count * span_duration

    final_span_index = span_count - 1
    final_span_start_time = start_time + final_span_index * span_duration

    legacy_last_tick_time = max(
        start_time + total_duration / 2,
        (final_span_start_time + span_duration) + TAIL_LENIENCY,
    )

    legacy_last_tick_progress = (
        (legacy_last_tick_time - final_span_start_time) / span_duration
        if span_duration
        else 0.0
    )
    if span_count % 2 == 0:
        legacy_last_tick_progress = 1 - legacy_last_tick_progress

    events.append(
        SliderEventDescriptor(
            Type=SliderEventType.LegacyLastTick,
            SpanIndex=final_span_index,
            SpanStartTime=final_span_start_time,
            Time=legacy_last_tick_time,
            PathProgress=legacy_last_tick_progress,
        )
    )

    events.append(
        SliderEventDescriptor(
            Type=SliderEventType.Tail,
            SpanIndex=final_span_index,
            SpanStartTime=start_time + (span_count - 1) * span_duration,
            Time=start_time + total_duration,
            PathProgress=float(span_count % 2),
        )
    )

    return events


def _generate_ticks(
    span_index: int,
    span_start_time: float,
    span_duration: float,
    reversed_span: bool,
    length: float,
    tick_distance: float,
    min_distance_from_end: float,
) -> list[SliderEventDescriptor]:
    """Return the ticks of a single span.

    Args:
        span_index: Which traversal of the path this is.
        span_start_time: When the span starts.
        span_duration: How long the span lasts.
        reversed_span: Whether the span runs backwards along the path.
        length: The path's length.
        tick_distance: The spacing between ticks.
        min_distance_from_end: How close to the end a tick may fall.

    Returns:
        The span's ticks, in forward path order.
    """
    ticks: list[SliderEventDescriptor] = []

    distance = tick_distance
    while distance < length - min_distance_from_end:
        progress = distance / length
        time_progress = 1 - progress if reversed_span else progress

        ticks.append(
            SliderEventDescriptor(
                Type=SliderEventType.Tick,
                SpanIndex=span_index,
                SpanStartTime=span_start_time,
                Time=span_start_time + time_progress * span_duration,
                PathProgress=progress,
            )
        )

        distance += tick_distance

    return ticks
