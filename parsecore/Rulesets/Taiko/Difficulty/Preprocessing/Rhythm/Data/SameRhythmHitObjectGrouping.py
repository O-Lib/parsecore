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

from parsecore.Rulesets.Taiko.Difficulty.Utils import DeltaTimeNormaliser
from parsecore.Rulesets.Taiko.Difficulty.Utils.IntervalGroupingUtils import (
    MARGIN_OF_ERROR,
)

# How far two spacings may differ and still be snapped together.
SNAP_TOLERANCE = MARGIN_OF_ERROR


class SameRhythmHitObjectGrouping:
    """Notes that follow each other at one spacing."""

    def __init__(self, previous, hit_objects: list) -> None:
        """Group a run of evenly spaced notes.

        The group's spacing is carried over from the previous group when the
        two are within snapping distance, so a rhythm held across a pause is
        not read as a new one.

        Args:
            previous: The group before this one, if any.
            hit_objects: The notes of this group, in time order.
        """
        self.Previous = previous
        self.HitObjects = hit_objects

        normalised = DeltaTimeNormaliser.Normalise(hit_objects, SNAP_TOLERANCE)
        normalised_deltas = [normalised[h] for h in hit_objects[1:]]

        modal_delta = round(normalised_deltas[0]) if normalised_deltas else 0

        self.HitObjectInterval: float | None = None
        if normalised_deltas:
            previous_delta = previous.HitObjectInterval if previous else None
            if (
                previous_delta is not None
                and abs(modal_delta - previous_delta) <= SNAP_TOLERANCE
            ):
                self.HitObjectInterval = previous_delta
            else:
                self.HitObjectInterval = modal_delta

        previous_interval = previous.HitObjectInterval if previous else None
        self.HitObjectIntervalRatio: float = (
            self.HitObjectInterval / previous_interval
            if previous_interval is not None and self.HitObjectInterval is not None
            else 1.0
        )

        self.Interval: float = math.inf
        if previous is not None:
            if abs(self.StartTime - previous.StartTime) <= SNAP_TOLERANCE:
                self.Interval = 0.0
            else:
                self.Interval = self.StartTime - previous.StartTime

    @property
    def FirstHitObject(self):
        """Return the note the group opens on."""
        return self.HitObjects[0]

    @property
    def StartTime(self) -> float:
        """Return when the group begins."""
        return self.HitObjects[0].StartTime

    @property
    def Duration(self) -> float:
        """Return how long the group lasts."""
        return self.HitObjects[-1].StartTime - self.HitObjects[0].StartTime
