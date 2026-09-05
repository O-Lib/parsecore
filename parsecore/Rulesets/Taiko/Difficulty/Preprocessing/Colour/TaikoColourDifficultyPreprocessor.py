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

from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Colour.Data.AlternatingMonoPattern import (
    AlternatingMonoPattern,
)
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Colour.Data.MonoStreak import (
    MonoStreak,
)
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Colour.Data.RepeatingHitPatterns import (
    RepeatingHitPatterns,
)
from parsecore.Rulesets.Taiko.Objects.Hit import Hit


def ProcessAndAssign(hit_objects: list) -> None:
    """Encode the beatmap's colours and give every note its groupings.

    Args:
        hit_objects: Every difficulty object of the beatmap, in time order.
    """
    for repeating_pattern in _encode(hit_objects):
        for i, mono_pattern in enumerate(repeating_pattern.AlternatingMonoPatterns):
            mono_pattern.Parent = repeating_pattern
            mono_pattern.Index = i

            for j, mono_streak in enumerate(mono_pattern.MonoStreaks):
                mono_streak.Parent = mono_pattern
                mono_streak.Index = j

                for hit_object in mono_streak.HitObjects:
                    hit_object.ColourData.RepeatingHitPattern = repeating_pattern
                    hit_object.ColourData.AlternatingMonoPattern = mono_pattern
                    hit_object.ColourData.MonoStreak = mono_streak


def _encode(data: list) -> list[RepeatingHitPatterns]:
    """Run the three encoding passes over the beatmap.

    Args:
        data: Every difficulty object of the beatmap.

    Returns:
        The repeating pattern groups.
    """
    mono_streaks = _encode_mono_streak(data)
    alternating_patterns = _encode_alternating_mono_pattern(mono_streaks)
    return _encode_repeating_hit_pattern(alternating_patterns)


def _encode_mono_streak(data: list) -> list[MonoStreak]:
    """Split the notes into runs of a single colour.

    Args:
        data: Every difficulty object of the beatmap.

    Returns:
        The colour runs, in order.
    """
    mono_streaks: list[MonoStreak] = []
    current: MonoStreak | None = None

    for taiko_object in data:
        previous_object = taiko_object.PreviousNote(0)

        if (
            current is None
            or previous_object is None
            or _hit_type_of(taiko_object) != _hit_type_of(previous_object)
        ):
            current = MonoStreak()
            mono_streaks.append(current)

        current.HitObjects.append(taiko_object)

    return mono_streaks


def _hit_type_of(taiko_object):
    """Return which side of the drum an object is played on, if any.

    Args:
        taiko_object: The difficulty object to read.
    """
    base_object = taiko_object.BaseObject
    return base_object.Type if isinstance(base_object, Hit) else None


def _encode_alternating_mono_pattern(
    data: list[MonoStreak],
) -> list[AlternatingMonoPattern]:
    """Group colour runs of equal length into alternating patterns.

    Args:
        data: The colour runs, in order.

    Returns:
        The alternating patterns, in order.
    """
    patterns: list[AlternatingMonoPattern] = []
    current: AlternatingMonoPattern | None = None

    for i, streak in enumerate(data):
        if current is None or streak.RunLength != data[i - 1].RunLength:
            current = AlternatingMonoPattern()
            patterns.append(current)

        current.MonoStreaks.append(streak)

    return patterns


def _encode_repeating_hit_pattern(
    data: list[AlternatingMonoPattern],
) -> list[RepeatingHitPatterns]:
    """Group alternating patterns that repeat every other pattern.

    A pattern is coupled when the one two along plays the same way; a run of
    coupled patterns is taken as one group, closed by the two that follow it.

    Args:
        data: The alternating patterns, in order.

    Returns:
        The repeating pattern groups, each knowing how long ago it recurred.
    """
    hit_patterns: list[RepeatingHitPatterns] = []
    current: RepeatingHitPatterns | None = None

    i = 0
    while i < len(data):
        current = RepeatingHitPatterns(current)

        is_coupled = i < len(data) - 2 and data[i].IsRepetitionOf(data[i + 2])

        if not is_coupled:
            current.AlternatingMonoPatterns.append(data[i])
        else:
            while is_coupled:
                current.AlternatingMonoPatterns.append(data[i])
                i += 1
                is_coupled = i < len(data) - 2 and data[i].IsRepetitionOf(data[i + 2])

            # The two patterns that break the run still close out the group.
            current.AlternatingMonoPatterns.append(data[i])
            current.AlternatingMonoPatterns.append(data[i + 1])
            i += 1

        hit_patterns.append(current)
        i += 1

    for hit_pattern in hit_patterns:
        hit_pattern.FindRepetitionInterval()

    return hit_patterns
