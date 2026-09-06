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
from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmap import GetPalpableObjects
from parsecore.Rulesets.Catch.Objects.Banana import Banana, BananaShower
from parsecore.Rulesets.Catch.Objects.CatchHitObject import CatchHitObject
from parsecore.Rulesets.Catch.Objects.Droplet import Droplet, TinyDroplet
from parsecore.Rulesets.Catch.Objects.Fruit import Fruit
from parsecore.Rulesets.Catch.Objects.JuiceStream import JuiceStream
from parsecore.Rulesets.Catch.UI.Catcher import (
    ALLOWED_CATCH_RANGE,
    BASE_DASH_SPEED,
    CalculateCatchWidth,
)
from parsecore.Rulesets.Catch.UI.CatchPlayfield import WIDTH as PLAYFIELD_WIDTH
from parsecore.Utils.LegacyRandom import LegacyRandom
from parsecore.Utils.Vector2 import f32

# The seed osu!stable scattered every beatmap's bananas from.
RNG_SEED = 1337

HYPER_DASH_GRACE = f32(f32(1000.0 / 60.0) / 4)


class CatchBeatmapProcessor(BeatmapProcessor):
    """Scatters catch objects and marks the dashes that cannot be walked."""

    def __init__(self, beatmap) -> None:
        """Create a processor for a beatmap.

        Args:
            beatmap: The converted catch beatmap.
        """
        super().__init__(beatmap)
        # Hard rock nudges fruit sideways; the mod turns this on.
        self.HardRockOffsets = False

    def PreProcess(self) -> None:
        """Force a new combo wherever a banana shower breaks the run."""
        last_object = None

        for hit_object in self.Beatmap.HitObjects:
            if not isinstance(hit_object, CatchHitObject):
                continue

            if not isinstance(hit_object, BananaShower) and (
                last_object is None or isinstance(last_object, BananaShower)
            ):
                hit_object.NewCombo = True

            last_object = hit_object

        super().PreProcess()

    def PostProcess(self) -> None:
        """Scatter the objects, then number them and find the hyper-dashes."""
        super().PostProcess()

        self.ApplyPositionOffsets(self.Beatmap)

        for index, hit_object in enumerate(
            h for h in self.Beatmap.HitObjects if isinstance(h, CatchHitObject)
        ):
            hit_object.IndexInBeatmap = index
            for nested in hit_object.NestedHitObjects:
                if isinstance(nested, CatchHitObject):
                    nested.IndexInBeatmap = index

            if hit_object.LastInCombo and hit_object.NestedHitObjects:
                last_nested = hit_object.NestedHitObjects[-1]
                if isinstance(last_nested, CatchHitObject):
                    last_nested.LastInCombo = True

    def ApplyPositionOffsets(self, beatmap) -> None:
        """Scatter bananas and droplets from a fixed-seed generator.

        The generator is drawn from in beatmap order, including for values
        osu!stable used and osu!lazer no longer does, because skipping those
        would shift every later object.

        Args:
            beatmap: The beatmap to scatter.
        """
        rng = LegacyRandom(RNG_SEED)

        last_position: float | None = None
        last_start_time = 0.0

        for hit_object in beatmap.HitObjects:
            if not isinstance(hit_object, CatchHitObject):
                continue

            hit_object.XOffset = 0.0

            if isinstance(hit_object, Fruit):
                if self.HardRockOffsets:
                    last_position, last_start_time = _apply_hard_rock_offset(
                        hit_object, last_position, last_start_time, rng
                    )

            elif isinstance(hit_object, BananaShower):
                for banana in hit_object.NestedHitObjects:
                    if not isinstance(banana, Banana):
                        continue
                    banana.XOffset = f32(rng.NextDouble() * PLAYFIELD_WIDTH)
                    # osu!stable drew a type, a rotation and a colour here.
                    rng.Next()
                    rng.Next()
                    rng.Next()

            elif isinstance(hit_object, JuiceStream):
                last_position = (
                    hit_object.OriginalX
                    + hit_object.Path.ControlPoints[-1].Position.X
                )
                last_start_time = hit_object.StartTime

                for nested in hit_object.NestedHitObjects:
                    if not isinstance(nested, CatchHitObject):
                        continue
                    nested.XOffset = 0.0

                    if isinstance(nested, TinyDroplet):
                        nested.XOffset = min(
                            max(rng.Next(-20, 20), -nested.OriginalX),
                            PLAYFIELD_WIDTH - nested.OriginalX,
                        )
                    elif isinstance(nested, Droplet):
                        # osu!stable drew a rotation here.
                        rng.Next()

        _initialise_hyper_dash(beatmap)


def _apply_hard_rock_offset(
    hit_object, last_position: float | None, last_start_time: float, rng: LegacyRandom
) -> tuple[float | None, float]:
    """Nudge a fruit sideways the way hard rock does.

    A fruit repeating the last one's position is jittered; one that has already
    moved is pushed further in the same direction, but only where the movement
    was small enough that the player would not have committed to it.

    Args:
        hit_object: The fruit to move.
        last_position: Where the last fruit ended up, if any.
        last_start_time: When that fruit was.
        rng: The generator to draw from.

    Returns:
        The position and time to carry to the next fruit.
    """
    offset_position = hit_object.OriginalX
    start_time = hit_object.StartTime

    if last_position is None or last_position == 0:
        return offset_position, start_time

    position_diff = offset_position - last_position
    time_diff = int(start_time - last_start_time)

    if time_diff > 1000:
        return offset_position, start_time

    if position_diff == 0:
        offset_position = _apply_random_offset(offset_position, time_diff / 4, rng)
        hit_object.XOffset = offset_position - hit_object.OriginalX
        # A jittered fruit deliberately does not become the new reference.
        return last_position, last_start_time

    # osu! divides two whole numbers here, so the threshold steps.
    if abs(position_diff) < int(time_diff / 3):
        offset_position = _apply_offset(offset_position, position_diff)

    hit_object.XOffset = offset_position - hit_object.OriginalX

    return offset_position, start_time


def _apply_random_offset(position: float, max_offset: float, rng: LegacyRandom) -> float:
    """Jitter a position to either side, staying on the playfield.

    Args:
        position: Where the object sits.
        max_offset: The furthest it may move.
        rng: The generator to draw from.

    Returns:
        The new position.
    """
    right = rng.NextBool()
    amount = min(20.0, f32(rng.Next(0, max(0.0, max_offset))))

    if right:
        if position + amount <= PLAYFIELD_WIDTH:
            return f32(position + amount)
        return f32(position - amount)

    if position - amount >= 0:
        return f32(position - amount)
    return f32(position + amount)


def _apply_offset(position: float, amount: float) -> float:
    """Push a position further along, but never off the playfield.

    Args:
        position: Where the object sits.
        amount: How far to push it, signed.

    Returns:
        The new position.
    """
    if amount > 0:
        if position + amount < PLAYFIELD_WIDTH:
            return f32(position + amount)
    elif position + amount > 0:
        return f32(position + amount)

    return position


def _initialise_hyper_dash(beatmap) -> None:
    """Mark every fruit the plate cannot reach the next one from.

    A dash covers one osu! pixel per millisecond. Where even that is not
    enough, the object becomes a hyper-dash; where it is, how much room was to
    spare is remembered, because a dash that only just works is its own kind of
    hard.

    Args:
        beatmap: The beatmap to mark.
    """
    palpable = [
        h
        for h in GetPalpableObjects(beatmap.HitObjects)
        if isinstance(h, Fruit) or (isinstance(h, Droplet) and not isinstance(h, TinyDroplet))
    ]

    half_catcher_width = CalculateCatchWidth(beatmap.Difficulty) / 2
    half_catcher_width /= ALLOWED_CATCH_RANGE

    last_direction = 0
    last_excess = half_catcher_width

    for i in range(len(palpable) - 1):
        current = palpable[i]
        following = palpable[i + 1]

        current.HyperDashTarget = None
        current.DistanceToHyperDash = 0.0

        this_direction = 1 if following.EffectiveX > current.EffectiveX else -1

        # Two whole millisecond counts less a single-precision grace period,
        # which osu! works out at single precision before widening it.
        time_to_next = f32(
            int(following.StartTime) - int(current.StartTime) - HYPER_DASH_GRACE
        )
        # Both positions are single precision, so their difference is too.
        distance_to_next = abs(f32(following.EffectiveX - current.EffectiveX)) - (
            last_excess if last_direction == this_direction else half_catcher_width
        )
        distance_to_hyper = f32(time_to_next * BASE_DASH_SPEED - distance_to_next)

        if distance_to_hyper < 0:
            current.HyperDashTarget = following
            last_excess = half_catcher_width
        else:
            current.DistanceToHyperDash = distance_to_hyper
            last_excess = min(max(distance_to_hyper, 0.0), half_catcher_width)

        last_direction = this_direction
