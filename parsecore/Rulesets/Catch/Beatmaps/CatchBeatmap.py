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

from parsecore.Beatmaps.Beatmap import Beatmap
from parsecore.Rulesets.Catch.Objects.Banana import BananaShower
from parsecore.Rulesets.Catch.Objects.Fruit import Fruit
from parsecore.Rulesets.Catch.Objects.JuiceStream import JuiceStream
from parsecore.Rulesets.Catch.Objects.PalpableCatchHitObject import (
    PalpableCatchHitObject,
)


class CatchBeatmap(Beatmap):
    """A beatmap converted to catch fruit, streams and banana showers."""

    @property
    def FruitCount(self) -> int:
        """Return how many loose fruit the beatmap has."""
        return sum(1 for h in self.HitObjects if isinstance(h, Fruit))

    @property
    def JuiceStreamCount(self) -> int:
        """Return how many juice streams the beatmap has."""
        return sum(1 for h in self.HitObjects if isinstance(h, JuiceStream))

    @property
    def BananaShowerCount(self) -> int:
        """Return how many banana showers the beatmap has."""
        return sum(1 for h in self.HitObjects if isinstance(h, BananaShower))


def GetPalpableObjects(hit_objects: list) -> list:
    """Return everything the plate can catch, in time order.

    A juice stream or banana shower contributes only what it drops; a loose
    fruit contributes itself.

    Args:
        hit_objects: The beatmap's objects.

    Returns:
        The catchable objects, sorted by when they land.
    """
    palpable: list = []

    for hit_object in hit_objects:
        if isinstance(hit_object, PalpableCatchHitObject):
            palpable.append(hit_object)

        for nested in hit_object.NestedHitObjects:
            if isinstance(nested, PalpableCatchHitObject):
                palpable.append(nested)

    palpable.sort(key=lambda h: h.StartTime)
    return palpable
