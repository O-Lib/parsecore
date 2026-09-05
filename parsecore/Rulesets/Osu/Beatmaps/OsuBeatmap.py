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
from parsecore.Rulesets.Osu.Objects.HitCircle import HitCircle
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner


class OsuBeatmap(Beatmap):
    """A beatmap converted to osu! circles, sliders and spinners."""

    @property
    def CircleCount(self) -> int:
        """Return how many hit circles the beatmap has."""
        return sum(1 for h in self.HitObjects if isinstance(h, HitCircle))

    @property
    def SliderCount(self) -> int:
        """Return how many sliders the beatmap has."""
        return sum(1 for h in self.HitObjects if isinstance(h, Slider))

    @property
    def SpinnerCount(self) -> int:
        """Return how many spinners the beatmap has."""
        return sum(1 for h in self.HitObjects if isinstance(h, Spinner))
