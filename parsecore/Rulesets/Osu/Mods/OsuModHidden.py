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
from parsecore.Rulesets.Mods.ModHidden import ModHidden
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Osu.Objects.OsuHitObject import OsuHitObject
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner
from parsecore.Rulesets.Osu.Objects.SpinnerTick import SpinnerTick

# The fraction of an object's preempt time it spends fading in under hidden.
FADE_IN_DURATION_MULTIPLIER = 0.4

# The fraction of an object's preempt time it spends fading out.
FADE_OUT_DURATION_MULTIPLIER = 0.3


class OsuModHidden(ModHidden):
    """Objects fade out before they are hit, and approach circles are gone."""

    Description = "Play with no approach circles and fading circles/sliders."
    OnlyFadeApproachCircles: bool = False

    @staticmethod
    def IsFirstAdjustableObject(hit_object: HitObject) -> bool:
        """Check if a hit object is eligible for hidden fade-in adjustments.

        Args:
            hit_object: The hit object to test.
        """
        return not (isinstance(hit_object, Spinner) or isinstance(hit_object, SpinnerTick))

    def ApplyToBeatmap(self, beatmap: Beatmap) -> None:
        """Shorten the fade-in of every object on the beatmap.

        Args:
            beatmap: The beatmap to modify.
        """
        super().ApplyToBeatmap(beatmap)

        def apply_fade_in_adjustment(osu_object: OsuHitObject) -> None:
            if not isinstance(osu_object, Slider):
                osu_object.TimeFadeIn = osu_object.TimePreempt * FADE_IN_DURATION_MULTIPLIER

            for nested in osu_object.NestedHitObjects:
                if isinstance(nested, OsuHitObject):
                    apply_fade_in_adjustment(nested)

        for hit_object in beatmap.HitObjects:
            if isinstance(hit_object, OsuHitObject):
                apply_fade_in_adjustment(hit_object)
