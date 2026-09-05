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
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    CalculateScaleFromCircleSize,
)
from parsecore.Utils.Vector2 import Vector2, f32

# The radius of a circle at scale 1.
OBJECT_RADIUS = 64.0

# The distance a slider travels in one beat at slider multiplier 1.
BASE_SCORING_DISTANCE = 100.0

PREEMPT_MIN = 450.0
PREEMPT_MID = 1200.0
PREEMPT_MAX = 1800.0

# How far each level of stacking shifts an object, before scaling.
STACK_OFFSET_MULTIPLIER = -6.4


class OsuHitObject(HitObject):
    """Something the player clicks, at a position on the playfield."""

    def __init__(self, start_time: float = 0.0, position: Vector2 | None = None) -> None:
        """Create an osu! object.

        Args:
            start_time: The object's time in milliseconds.
            position: The object's position on the playfield.
        """
        super().__init__(start_time)
        self.Position: Vector2 = position or Vector2()

        self.TimePreempt: float = 600.0
        self.TimeFadeIn: float = 400.0
        self.Scale: float = 1.0

        self._stack_height: int = 0

        self.NewCombo: bool = False
        self.ComboOffset: int = 0
        self.IndexInCurrentCombo: int = 0
        self.ComboIndex: int = 0
        self.LastInCombo: bool = False

    @property
    def StackHeight(self) -> int:
        """Return how many objects this one is stacked on top of."""
        return self._stack_height

    @StackHeight.setter
    def StackHeight(self, value: int) -> None:
        """Set the stack height, passing it on to every nested object.

        osu! propagates this through a bindable, so a slider's ticks, repeats
        and ends move with it. Without that, a stacked slider's cursor path is
        measured from unshifted positions and its aim difficulty comes out
        wrong.

        Args:
            value: The new stack height.
        """
        self._stack_height = value
        for nested in self.NestedHitObjects:
            if isinstance(nested, OsuHitObject):
                nested.StackHeight = value

    @property
    def X(self) -> float:
        """Return the object's x position."""
        return self.Position.X

    @property
    def Y(self) -> float:
        """Return the object's y position."""
        return self.Position.Y

    @property
    def Radius(self) -> float:
        """Return the object's radius in osu! pixels.

        Kept at double precision: osu! narrows this to a ``float`` only where
        the difficulty distances are scaled, while the slider cursor walk uses
        the full-precision value.
        """
        return OBJECT_RADIUS * self.Scale

    @property
    def StackOffset(self) -> Vector2:
        """Return how far this object is shifted by stacking."""
        shift = f32(f32(self.StackHeight * self.Scale) * f32(STACK_OFFSET_MULTIPLIER))
        return Vector2(shift, shift)

    @property
    def StackedPosition(self) -> Vector2:
        """Return the object's position after stacking is applied."""
        return self.Position + self.StackOffset

    @property
    def EndPosition(self) -> Vector2:
        """Return where the object ends; the same as its start for most."""
        return self.Position

    @property
    def StackedEndPosition(self) -> Vector2:
        """Return the object's end position after stacking is applied."""
        return self.EndPosition + self.StackOffset

    def ApplyDefaultsToSelf(self, control_point_info, difficulty) -> None:
        """Derive preempt time, fade-in and scale from the beatmap.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        super().ApplyDefaultsToSelf(control_point_info, difficulty)

        # osu! truncates the preempt window to whole milliseconds.
        self.TimePreempt = int(
            BeatmapDifficulty.DifficultyRange(
                difficulty.ApproachRate, PREEMPT_MAX, PREEMPT_MID, PREEMPT_MIN
            )
        )

        # Preempt can fall below the minimum through rate-changing mods; the
        # fade-in shrinks with it so objects still fade in fully.
        self.TimeFadeIn = 400.0 * min(1.0, self.TimePreempt / PREEMPT_MIN)

        self.Scale = CalculateScaleFromCircleSize(difficulty.CircleSize, True)

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Osu.Judgements.OsuJudgement import OsuJudgement

        return OsuJudgement()

    def CreateHitWindows(self):
        """Return the hit windows osu! judges this object with."""
        from parsecore.Rulesets.Osu.Scoring.OsuHitWindows import OsuHitWindows

        return OsuHitWindows()
