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


class BeatmapProcessor:
    """Runs before and after a beatmap's objects have their defaults applied."""

    def __init__(self, beatmap) -> None:
        """Create a processor for a beatmap.

        Args:
            beatmap: The beatmap to process.
        """
        self.Beatmap = beatmap

    def PreProcess(self) -> None:
        """Assign combo indices to every object that carries them."""
        last_obj = None
        index = 0
        combo_index = 0
        force_new_combo = False

        for obj in self.Beatmap.HitObjects:
            if not hasattr(obj, "NewCombo"):
                continue

            if last_obj is None:
                # The first object always starts a combo.
                obj.NewCombo = True

            if obj.NewCombo or force_new_combo:
                index = 0
                combo_index += 1 + getattr(obj, "ComboOffset", 0)
                force_new_combo = False

            obj.IndexInCurrentCombo = index
            obj.ComboIndex = combo_index

            index += 1
            last_obj = obj

    def PostProcess(self) -> None:
        """Apply any ruleset-specific adjustments after defaults are applied."""
