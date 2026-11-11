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
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Objects.Types.IHasCombo import IHasCombo
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
from parsecore.Rulesets.Objects.Types.IHasGenerateTicks import IHasGenerateTicks
from parsecore.Rulesets.Objects.Types.IHasPathWithRepeats import IHasPathWithRepeats
from parsecore.Rulesets.Objects.Types.IHasPosition import IHasPosition
from parsecore.Rulesets.Objects.Types.IHasSliderVelocity import IHasSliderVelocity
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle
from parsecore.Rulesets.Osu.Objects.OsuHitObject import OsuHitObject
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner
from parsecore.Utils.Vector2 import Vector2

# The osu! playfield, in osu! pixels.
PLAYFIELD_SIZE = Vector2(512, 384)

# Tick spacing stopped depending on slider velocity from this format on.
FIRST_TICK_SCALING_VERSION = 8


class OsuBeatmapConverter(BeatmapConverter):
    """Turns decoded objects into osu! circles, sliders and spinners."""

    def CanConvert(self) -> bool:
        """Return whether every object carries a playfield position."""
        return all(isinstance(h, IHasPosition) for h in self.Beatmap.HitObjects)

    def CreateBeatmap(self):
        """Return an empty osu! beatmap."""
        from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmap import OsuBeatmap

        return OsuBeatmap()

    def ConvertHitObject(self, original: HitObject, beatmap: Beatmap) -> list[OsuHitObject]:
        """Convert one decoded object into its osu! counterpart.

        Args:
            original: The decoded object.
            beatmap: The beatmap being converted.

        Returns:
            A single osu! object.
        """
        position_data = original if isinstance(original, IHasPosition) else None
        combo_data = original if isinstance(original, IHasCombo) else None
        slider_velocity_data = original if isinstance(original, IHasSliderVelocity) else None
        generate_ticks_data = original if isinstance(original, IHasGenerateTicks) else None

        position = position_data.Position if position_data is not None else Vector2()
        new_combo = combo_data.NewCombo if combo_data is not None else False
        combo_offset = combo_data.ComboOffset if combo_data is not None else 0
        slider_velocity_multiplier = (
            slider_velocity_data.SliderVelocityMultiplier if slider_velocity_data is not None else 1.0
        )
        generate_ticks = generate_ticks_data.GenerateTicks if generate_ticks_data is not None else True
        if isinstance(original, IHasPathWithRepeats):
            curve_data = original
            slider = Slider()
            slider.StartTime = original.StartTime
            slider.Position = position
            slider.Samples = original.Samples
            slider.Path = curve_data.Path
            slider.NodeSamples = curve_data.NodeSamples
            slider.RepeatCount = curve_data.RepeatCount
            slider.SliderVelocityMultiplier = slider_velocity_multiplier
            slider.GenerateTicks = generate_ticks
            slider.NewCombo = new_combo
            slider.ComboOffset = combo_offset
            slider.TickDistanceMultiplier = self._tick_distance_multiplier(
                original, beatmap
            )
            return [slider]

        if isinstance(original, IHasDuration):
            # Anything with a duration becomes a spinner, which on a converted
            # beatmap includes a mania hold note. It keeps the position it was
            # decoded with rather than being centred.
            end_time_data = original
            spinner = Spinner()
            spinner.StartTime = original.StartTime
            spinner.EndTime = end_time_data.EndTime
            spinner.Position = position_data.Position if position_data else PLAYFIELD_SIZE / 2
            spinner.Samples = original.Samples
            spinner.NewCombo = new_combo
            spinner.ComboOffset = combo_offset
            return [spinner]

        circle = HitCircle()
        circle.StartTime = original.StartTime
        circle.Position = position
        circle.Samples = original.Samples
        circle.NewCombo = new_combo
        circle.ComboOffset = combo_offset
        return [circle]

    @staticmethod
    def _tick_distance_multiplier(original: HitObject, beatmap: Beatmap) -> float:
        """Return the tick spacing correction for older beatmap formats.

        Args:
            original: The slider being converted.
            beatmap: The beatmap being converted.

        Returns:
            ``1`` for modern beatmaps, otherwise the inverse slider velocity.
        """
        if beatmap.BeatmapInfo.BeatmapVersion >= FIRST_TICK_SCALING_VERSION:
            return 1.0

        if isinstance(beatmap.ControlPointInfo, LegacyControlPointInfo):
            legacy_cp = beatmap.ControlPointInfo
            velocity = legacy_cp.DifficultyPointAt(original.StartTime).SliderVelocity
            return 1.0 / velocity if velocity else 1.0

        return 1.0
