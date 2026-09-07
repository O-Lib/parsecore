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
from parsecore.Utils.Vector2 import f32

# The plate's half-width, once every beatmap is scaled onto one measure.
NORMALIZED_HALF_CATCHER_WIDTH = f32(41.0)

# How far off the player is assumed to be even when playing perfectly.
ABSOLUTE_PLAYER_POSITIONING_ERROR = f32(16.0)

# The shortest gap between objects the calculation will consider.
MINIMUM_STRAIN_TIME = 40.0


class CatchDifficultyHitObject(DifficultyHitObject):
    """A catchable object, with the plate movement it demands."""

    def __init__(
        self,
        hit_object,
        last_object,
        clock_rate: float,
        half_catcher_width: float,
        objects: list,
        index: int,
    ) -> None:
        """Create a difficulty object and work out the movement it needs.

        Args:
            hit_object: The object to catch.
            last_object: The object before it.
            clock_rate: The rate the beatmap is played at.
            half_catcher_width: Half the plate's width on this beatmap.
            objects: Every difficulty object built so far.
            index: This object's place among them.
        """
        super().__init__(hit_object, last_object, clock_rate, objects, index)

        scaling_factor = f32(NORMALIZED_HALF_CATCHER_WIDTH / half_catcher_width)
        self.NormalizedPosition = f32(hit_object.EffectiveX * scaling_factor)
        self.LastNormalizedPosition = f32(last_object.EffectiveX * scaling_factor)

        self.StrainTime = max(MINIMUM_STRAIN_TIME, self.DeltaTime)

        self.PlayerPosition = 0.0
        self.LastPlayerPosition = 0.0
        self.DistanceMoved = 0.0
        self.ExactDistanceMoved = 0.0

        self._set_movement_state()

    def _set_movement_state(self) -> None:
        """Work out how far the plate has to move to reach this object."""
        previous = self.Previous(0)
        self.LastPlayerPosition = (
            self.LastNormalizedPosition if self.Index == 0 else previous.PlayerPosition
        )

        # The plate only moves as far as it must: anywhere within its own edge
        # of the fruit will do.
        reach = NORMALIZED_HALF_CATCHER_WIDTH - ABSOLUTE_PLAYER_POSITIONING_ERROR
        self.PlayerPosition = min(
            max(self.LastPlayerPosition, f32(self.NormalizedPosition - reach)),
            f32(self.NormalizedPosition + reach),
        )

        self.DistanceMoved = f32(self.PlayerPosition - self.LastPlayerPosition)
        self.ExactDistanceMoved = f32(
            self.NormalizedPosition - self.LastPlayerPosition
        )

        # A hyper-dash throws the plate all the way onto the fruit.
        if self.LastObject.HyperDash:
            self.PlayerPosition = self.NormalizedPosition
