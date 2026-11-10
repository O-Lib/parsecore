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

from typing import cast

from parsecore.Beatmaps.Beatmap import Beatmap
from parsecore.Beatmaps.BeatmapConverter import BeatmapConverter
from parsecore.Beatmaps.Legacy.LegacyControlPointInfo import LegacyControlPointInfo
from parsecore.Rulesets.Catch.Objects.Banana import BananaShower
from parsecore.Rulesets.Catch.Objects.CatchHitObject import (
    DEFAULT_LEGACY_CONVERT_Y,
)
from parsecore.Rulesets.Catch.Objects.Fruit import Fruit
from parsecore.Rulesets.Catch.Objects.JuiceStream import JuiceStream
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Objects.Types.IHasCombo import IHasCombo
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
from parsecore.Rulesets.Objects.Types.IHasPathWithRepeats import IHasPathWithRepeats
from parsecore.Rulesets.Objects.Types.IHasSliderVelocity import IHasSliderVelocity
from parsecore.Rulesets.Objects.Types.IHasXPosition import IHasXPosition
from parsecore.Rulesets.Objects.Types.IHasYPosition import IHasYPosition

# Beatmaps before this format scaled tick spacing with the slider velocity.
FIRST_UNSCALED_TICK_VERSION = 8


class CatchBeatmapConverter(BeatmapConverter):
    """Turns decoded objects into catch fruit, streams and banana showers."""
    
    def __init__(self, beatmap: Beatmap) -> None:
        """Create a catch beatmap converter.

        Args:
            beatmap: The beatmap to convert.
        """
        super().__init__(beatmap)

    def CanConvert(self) -> bool:
        """Return whether every object has a horizontal position."""
        return all(isinstance(h, IHasXPosition) for h in self.Beatmap.HitObjects)

    def CreateBeatmap(self):
        """Return an empty catch beatmap."""
        from parsecore.Rulesets.Catch.Beatmaps.CatchBeatmap import CatchBeatmap

        return CatchBeatmap()

    def ConvertHitObject(self, original: HitObject, beatmap: Beatmap) -> list[HitObject]:
        """Convert one decoded object into its catch counterpart.

        Args:
            original: The decoded object.
            beatmap: The beatmap being converted.

        Returns:
            The catch object it becomes.
        """
        x_position_data = original if isinstance(original, IHasXPosition) else None
        y_position_data = original if isinstance(original, IHasYPosition) else None
        combo_data = original if isinstance(original, IHasCombo) else None
        slider_velocity_data = original if isinstance(original, IHasSliderVelocity) else None

        new_combo = combo_data.NewCombo if combo_data is not None else False
        combo_offset = combo_data.ComboOffset if combo_data is not None else 0
        x = x_position_data.X if x_position_data is not None else 0.0
        y = y_position_data.Y if y_position_data is not None else DEFAULT_LEGACY_CONVERT_Y
        slider_velocity_multiplier = (
            slider_velocity_data.SliderVelocityMultiplier if slider_velocity_data is not None else 1.0
        )
        if isinstance(original, IHasPathWithRepeats):
            curve_data = original
            stream = JuiceStream()
            stream.StartTime = original.StartTime
            stream.Samples = original.Samples
            stream.Path = curve_data.Path
            stream.NodeSamples = curve_data.NodeSamples
            stream.RepeatCount = curve_data.RepeatCount
            stream.X = x
            stream.NewCombo = new_combo
            stream.ComboOffset = combo_offset
            stream.LegacyConvertedY = y
            stream.TickDistanceMultiplier = self._tick_distance_multiplier(
                original, beatmap
            )
            stream.SliderVelocityMultiplier = slider_velocity_multiplier
            return [stream]

        if isinstance(original, IHasDuration):
            end_time = original
            shower = BananaShower()
            shower.StartTime = original.StartTime
            shower.Samples = original.Samples
            shower.Duration = end_time.Duration
            shower.NewCombo = new_combo
            shower.ComboOffset = combo_offset
            return [shower]

        fruit = Fruit()
        fruit.StartTime = original.StartTime
        fruit.Samples = original.Samples
        fruit.NewCombo = new_combo
        fruit.ComboOffset = combo_offset
        fruit.X = x
        fruit.LegacyConvertedY = y
        return [fruit]

    @staticmethod
    def _tick_distance_multiplier(original: HitObject, beatmap: Beatmap) -> float:
        """Return the tick spacing correction for older beatmap formats.

        Args:
            original: The slider being converted.
            beatmap: The beatmap being converted.

        Returns:
            ``1`` for modern beatmaps, otherwise the inverse slider velocity.
        """
        if beatmap.BeatmapInfo.BeatmapVersion >= FIRST_UNSCALED_TICK_VERSION:
            return 1.0

        if isinstance(beatmap.ControlPointInfo, LegacyControlPointInfo):
            legacy_cp = beatmap.ControlPointInfo
            velocity = legacy_cp.DifficultyPointAt(original.StartTime).SliderVelocity
            return 1.0 / velocity if velocity else 1.0

        return 1.0
