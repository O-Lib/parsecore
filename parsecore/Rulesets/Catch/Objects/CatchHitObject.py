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

from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Rulesets.Catch.UI.CatchPlayfield import WIDTH as PLAYFIELD_WIDTH
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    CalculateScaleFromCircleSize,
)
from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows
from parsecore.Utils.Vector2 import f32

OBJECT_RADIUS = 64.0

# What a converted beatmap's objects are given for a vertical position, which
# catch itself never reads.
DEFAULT_LEGACY_CONVERT_Y = 192.0

# How long an object is visible before it must be caught, at difficulty 0, 5
# and 10.
PREEMPT_MAX = 1800.0
PREEMPT_MID = 1200.0
PREEMPT_MIN = 450.0


class CatchHitObject(HitObject):
    """Something falling towards the plate."""

    def __init__(self, start_time: float = 0.0, x: float = 0.0) -> None:
        """Create a catch object.

        Args:
            start_time: The object's time in milliseconds.
            x: Where the beatmap places it across the playfield.
        """
        super().__init__(start_time)
        self.OriginalX = x
        self.XOffset = 0.0
        self.LegacyConvertedY: float = DEFAULT_LEGACY_CONVERT_Y

        self.TimePreempt: float = 1000.0
        self.Scale: float = 1.0

        self.IndexInBeatmap: int = 0
        self.NewCombo: bool = False
        self.ComboOffset: int = 0
        self.IndexInCurrentCombo: int = 0
        self.ComboIndex: int = 0
        self.ComboIndexWithOffsets: int = 0
        self._last_in_combo: bool = False

    @property
    def OriginalX(self) -> float:
        """Return where the beatmap places this object."""
        return self._original_x

    @OriginalX.setter
    def OriginalX(self, value: float) -> None:
        """Move the object, keeping it at the precision osu! stores it in.

        Args:
            value: The new position.
        """
        self._original_x = f32(value)

    @property
    def XOffset(self) -> float:
        """Return how far the processor has nudged this object."""
        return self._x_offset

    @XOffset.setter
    def XOffset(self, value: float) -> None:
        """Nudge the object sideways.

        Args:
            value: The new offset.
        """
        self._x_offset = f32(value)

    @property
    def Scale(self) -> float:
        """Return how large the object is drawn."""
        return self._scale

    @Scale.setter
    def Scale(self, value: float) -> None:
        """Resize the object.

        Args:
            value: The new scale.
        """
        self._scale = f32(value)

    @property
    def X(self) -> float:
        """Return where the beatmap places this object."""
        return self.OriginalX

    @X.setter
    def X(self, value: float) -> None:
        """Move the object across the playfield.

        Args:
            value: The new position.
        """
        self.OriginalX = value

    @property
    def EffectiveX(self) -> float:
        """Return where the object actually falls, offset and all."""
        return min(max(f32(self.OriginalX + self.XOffset), 0.0), PLAYFIELD_WIDTH)

    @property
    def LastInCombo(self) -> bool:
        """Return whether this object closes its combo."""
        return self._last_in_combo

    @LastInCombo.setter
    def LastInCombo(self, value: bool) -> None:
        """Set whether this object closes its combo.

        Args:
            value: Whether it does.
        """
        self._last_in_combo = value

    @property
    def RandomSeed(self) -> int:
        """Return the seed osu!stable derived from this object's time."""
        return int(self.StartTime)

    def ApplyDefaultsToSelf(self, control_point_info, difficulty) -> None:
        """Derive the object's visibility and size from the beatmap.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        super().ApplyDefaultsToSelf(control_point_info, difficulty)

        self.TimePreempt = int(
            BeatmapDifficulty.DifficultyRange(
                difficulty.ApproachRate, PREEMPT_MAX, PREEMPT_MID, PREEMPT_MIN
            )
        )
        self.Scale = CalculateScaleFromCircleSize(difficulty.CircleSize)

    def UpdateComboInformation(self, last_object) -> None:
        """Place this object in the beatmap's run of combos.

        A banana shower never starts a combo of its own, and the object after
        one always does.

        Args:
            last_object: The object before this one, if any.
        """
        from parsecore.Rulesets.Catch.Objects.BananaShower import BananaShower

        index = last_object.ComboIndex if last_object else 0
        index_with_offsets = last_object.ComboIndexWithOffsets if last_object else 0
        in_current_combo = (
            last_object.IndexInCurrentCombo + 1 if last_object else 0
        )

        if not isinstance(self, BananaShower) and (
            self.NewCombo or last_object is None or isinstance(last_object, BananaShower)
        ):
            in_current_combo = 0
            index += 1
            index_with_offsets += self.ComboOffset + 1

            if last_object is not None:
                last_object.LastInCombo = True

        self.ComboIndex = index
        self.ComboIndexWithOffsets = index_with_offsets
        self.IndexInCurrentCombo = in_current_combo

    def CreateHitWindows(self):
        """Return no windows; catch judges by position, not timing."""
        return EmptyHitWindows()
