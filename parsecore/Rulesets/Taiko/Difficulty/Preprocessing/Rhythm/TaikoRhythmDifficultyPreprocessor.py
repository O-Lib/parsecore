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

from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Rhythm.Data.SamePatternsGroupedHitObjects import (
    SamePatternsGroupedHitObjects,
)
from parsecore.Rulesets.Taiko.Difficulty.Preprocessing.Rhythm.Data.SameRhythmHitObjectGrouping import (
    SameRhythmHitObjectGrouping,
)
from parsecore.Rulesets.Taiko.Difficulty.Utils.IntervalGroupingUtils import (
    GroupByInterval,
)


def ProcessAndAssign(hit_objects: list) -> None:
    """Group the beatmap's rhythms and give every note its groupings.

    Args:
        hit_objects: Every difficulty object of the beatmap, in time order.
    """
    rhythm_groups = _create_same_rhythm_grouped_hit_objects(hit_objects)

    for rhythm_group in rhythm_groups:
        for hit_object in rhythm_group.HitObjects:
            hit_object.RhythmData.SameRhythmGroupedHitObjects = rhythm_group

    for pattern_group in _create_same_pattern_grouped_hit_objects(rhythm_groups):
        for hit_object in pattern_group.AllHitObjects:
            hit_object.RhythmData.SamePatternsGroupedHitObjects = pattern_group


def _create_same_rhythm_grouped_hit_objects(
    hit_objects: list,
) -> list[SameRhythmHitObjectGrouping]:
    """Split the notes into runs that share a spacing.

    Args:
        hit_objects: Every difficulty object of the beatmap.

    Returns:
        The rhythm groups, in order.
    """
    rhythm_groups: list[SameRhythmHitObjectGrouping] = []

    for grouped in GroupByInterval(hit_objects):
        rhythm_groups.append(
            SameRhythmHitObjectGrouping(
                rhythm_groups[-1] if rhythm_groups else None, grouped
            )
        )

    return rhythm_groups


def _create_same_pattern_grouped_hit_objects(
    rhythm_groups: list[SameRhythmHitObjectGrouping],
) -> list[SamePatternsGroupedHitObjects]:
    """Split the rhythm groups into runs that recur at one spacing.

    Args:
        rhythm_groups: The rhythm groups, in order.

    Returns:
        The pattern groups, in order.
    """
    pattern_groups: list[SamePatternsGroupedHitObjects] = []

    for grouped in GroupByInterval(rhythm_groups):
        pattern_groups.append(
            SamePatternsGroupedHitObjects(
                pattern_groups[-1] if pattern_groups else None, grouped
            )
        )

    return pattern_groups
