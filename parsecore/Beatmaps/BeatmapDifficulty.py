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

from parsecore.Utils.Vector2 import f32

DEFAULT_DIFFICULTY = 5.0

# The four settings osu! declares as ``float``.
_SINGLE_PRECISION_SETTINGS = frozenset(
    {"DrainRate", "CircleSize", "OverallDifficulty", "ApproachRate"}
)


class BeatmapDifficulty:
    """The HP, CS, OD, AR and slider settings of a beatmap."""

    __slots__ = (
        "DrainRate",
        "CircleSize",
        "OverallDifficulty",
        "ApproachRate",
        "SliderMultiplier",
        "SliderTickRate",
    )

    def __init__(
        self,
        DrainRate: float = DEFAULT_DIFFICULTY,
        CircleSize: float = DEFAULT_DIFFICULTY,
        OverallDifficulty: float = DEFAULT_DIFFICULTY,
        ApproachRate: float = DEFAULT_DIFFICULTY,
        SliderMultiplier: float = 1.4,
        SliderTickRate: float = 1.0,
    ) -> None:
        """Create a set of difficulty settings.

        Args:
            DrainRate: The HP drain rate.
            CircleSize: The circle size.
            OverallDifficulty: The overall difficulty.
            ApproachRate: The approach rate.
            SliderMultiplier: The slider velocity multiplier.
            SliderTickRate: How many ticks a slider places per beat.
        """
        self.DrainRate = DrainRate
        self.CircleSize = CircleSize
        self.OverallDifficulty = OverallDifficulty
        self.ApproachRate = ApproachRate
        self.SliderMultiplier = SliderMultiplier
        self.SliderTickRate = SliderTickRate

    def __setattr__(self, name: str, value: float) -> None:
        """Store a setting, narrowing the four single-precision ones.

        Args:
            name: The setting to write.
            value: The value to store.
        """
        if name in _SINGLE_PRECISION_SETTINGS:
            value = f32(value)
        object.__setattr__(self, name, value)

    def __repr__(self) -> str:
        """Return an unambiguous representation."""
        return (
            f"BeatmapDifficulty(DrainRate={self.DrainRate!r}, "
            f"CircleSize={self.CircleSize!r}, "
            f"OverallDifficulty={self.OverallDifficulty!r}, "
            f"ApproachRate={self.ApproachRate!r}, "
            f"SliderMultiplier={self.SliderMultiplier!r}, "
            f"SliderTickRate={self.SliderTickRate!r})"
        )

    def __eq__(self, other: object) -> bool:
        """Return whether every setting matches."""
        if not isinstance(other, BeatmapDifficulty):
            return NotImplemented
        return all(
            getattr(self, name) == getattr(other, name) for name in self.__slots__
        )

    def CopyFrom(self, other: BeatmapDifficulty) -> None:
        """Copy every value from another difficulty.

        Args:
            other: The difficulty to copy.
        """
        self.DrainRate = other.DrainRate
        self.CircleSize = other.CircleSize
        self.OverallDifficulty = other.OverallDifficulty
        self.ApproachRate = other.ApproachRate
        self.SliderMultiplier = other.SliderMultiplier
        self.SliderTickRate = other.SliderTickRate

    def Clone(self) -> BeatmapDifficulty:
        """Return an independent copy of this difficulty."""
        copy = BeatmapDifficulty()
        copy.CopyFrom(self)
        return copy

    @staticmethod
    def InverseDifficultyRange(
        difficulty_value: float, diff0: float, diff5: float, diff10: float
    ) -> float:
        """Return the difficulty a mapped value came from.

        The inverse of :meth:`DifficultyRange`; used to express a rate-adjusted
        preempt time back as an approach rate.

        Args:
            difficulty_value: The mapped value.
            diff0: The value at difficulty ``0``.
            diff5: The value at difficulty ``5``.
            diff10: The value at difficulty ``10``.

        Returns:
            The difficulty that maps onto ``difficulty_value``.
        """
        import math

        same_side = math.copysign(1, difficulty_value - diff5) == math.copysign(
            1, diff10 - diff5
        )
        if same_side:
            return (difficulty_value - diff5) / (diff10 - diff5) * 5 + 5
        return (difficulty_value - diff5) / (diff5 - diff0) * 5 + 5

    @staticmethod
    def DifficultyRange(difficulty: float, mid: float = 0.0, *args: float) -> float:
        """Map a difficulty value onto a range, the way osu! does.

        With no bounds given, maps ``0``-``10`` onto ``-1``-``1``. With three
        bounds, maps onto ``min``-``mid``-``max`` with ``5`` at the midpoint.

        Args:
            difficulty: The difficulty value, ``0`` to ``10``.
            mid: The value at difficulty ``5`` when bounds are given.
            *args: Optionally ``min`` and ``max`` bounds.

        Returns:
            The mapped value.
        """
        if not args:
            return (difficulty - 5.0) / 5.0
        min_val, mid_val, max_val = mid, args[0], args[1]
        if difficulty > 5.0:
            return mid_val + (max_val - mid_val) * (difficulty - 5.0) / 5.0
        if difficulty < 5.0:
            return mid_val + (mid_val - min_val) * (difficulty - 5.0) / 5.0
        return mid_val
