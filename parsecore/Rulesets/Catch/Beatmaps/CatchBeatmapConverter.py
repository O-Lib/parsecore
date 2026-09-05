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

from parsecore.Beatmaps.BeatmapConverter import BeatmapConverter
from parsecore.Rulesets.Catch.Objects.Banana import BananaShower
from parsecore.Rulesets.Catch.Objects.CatchHitObject import (
    DEFAULT_LEGACY_CONVERT_Y,
)
from parsecore.Rulesets.Catch.Objects.Fruit import Fruit
from parsecore.Rulesets.Catch.Objects.JuiceStream import JuiceStream
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration

# Beatmaps before this format scaled tick spacing with the slider velocity.
FIRST_UNSCALED_TICK_VERSION = 8


class CatchBeatmapConverter(BeatmapConverter):
    """Turns decoded objects into catch fruit, streams and banana showers."""

    def CanConvert(self) -> bool:
        """Return whether every object has a horizontal position."""
        return all(hasattr(h, "X") for h in self.Beatmap.HitObjects)

    def CreateBeatmap(self):
        """Return an empty catch beatmap."""
        from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmap import CatchBeatmap

        return CatchBeatmap()

    def ConvertHitObject(self, original: HitObject, beatmap) -> list[HitObject]:
        """Convert one decoded object into its catch counterpart.

        Args:
            original: The decoded object.
            beatmap: The beatmap being converted.

        Returns:
            The catch object it becomes.
        """
        x = getattr(original, "X", 0.0)
        y = getattr(original, "Y", DEFAULT_LEGACY_CONVERT_Y)
        new_combo = getattr(original, "NewCombo", False)
        combo_offset = getattr(original, "ComboOffset", 0)

        if hasattr(original, "Path"):
            stream = JuiceStream(original.StartTime, x)
            stream.Samples = original.Samples
            stream.Path = original.Path
            stream.NodeSamples = getattr(original, "NodeSamples", []) or []
            stream.RepeatCount = original.RepeatCount
            stream.NewCombo = new_combo
            stream.ComboOffset = combo_offset
            stream.LegacyConvertedY = y
            stream.TickDistanceMultiplier = self._tick_distance_multiplier(
                original, beatmap
            )
            stream.SliderVelocityMultiplier = getattr(
                original, "SliderVelocityMultiplier", 1.0
            )
            return [stream]

        if isinstance(original, IHasDuration):
            shower = BananaShower(original.StartTime, original.Duration)
            shower.Samples = original.Samples
            shower.NewCombo = new_combo
            shower.ComboOffset = combo_offset
            return [shower]

        fruit = Fruit(original.StartTime, x)
        fruit.Samples = original.Samples
        fruit.NewCombo = new_combo
        fruit.ComboOffset = combo_offset
        fruit.LegacyConvertedY = y
        return [fruit]

    @staticmethod
    def _tick_distance_multiplier(original, beatmap) -> float:
        """Return the tick spacing correction for older beatmap formats.

        Args:
            original: The slider being converted.
            beatmap: The beatmap being converted.

        Returns:
            ``1`` for modern beatmaps, otherwise the inverse slider velocity.
        """
        if beatmap.BeatmapInfo.BeatmapVersion >= FIRST_UNSCALED_TICK_VERSION:
            return 1.0

        velocity = getattr(original, "SliderVelocityMultiplier", 1.0)
        return 1.0 / velocity if velocity else 1.0
