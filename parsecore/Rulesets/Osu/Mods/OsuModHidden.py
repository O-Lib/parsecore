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

from parsecore.Rulesets.Mods.ModHidden import ModHidden
from parsecore.Rulesets.Osu.Objects.OsuHitObject import OsuHitObject
from parsecore.Rulesets.Osu.Objects.Slider import Slider

# The fraction of an object's preempt time it spends fading in under hidden.
FADE_IN_DURATION_MULTIPLIER = 0.4

# The fraction of an object's preempt time it spends fading out.
FADE_OUT_DURATION_MULTIPLIER = 0.3


class OsuModHidden(ModHidden):
    """Objects fade out before they are hit, and approach circles are gone."""

    Name = "Hidden"
    Acronym = "HD"
    Description = "Play with no approach circles and fading objects."

    def __init__(self, only_fade_approach_circles: bool = False) -> None:
        """Create the mod.

        Args:
            only_fade_approach_circles: Whether only approach circles fade,
                leaving the objects themselves fully visible.
        """
        self.OnlyFadeApproachCircles = only_fade_approach_circles

    def ApplyToBeatmap(self, beatmap) -> None:
        """Shorten the fade-in of every object on the beatmap.

        Args:
            beatmap: The beatmap to modify.
        """
        for hit_object in beatmap.HitObjects:
            if isinstance(hit_object, OsuHitObject):
                _apply_fade_in_adjustment(hit_object)


def _apply_fade_in_adjustment(osu_object: OsuHitObject) -> None:
    """Shorten one object's fade-in, and its nested objects' too.

    Args:
        osu_object: The object to adjust.
    """
    # Sliders keep their default fade-in, to match osu!stable.
    if not isinstance(osu_object, Slider):
        osu_object.TimeFadeIn = osu_object.TimePreempt * FADE_IN_DURATION_MULTIPLIER

    for nested in osu_object.NestedHitObjects:
        if isinstance(nested, OsuHitObject):
            _apply_fade_in_adjustment(nested)
