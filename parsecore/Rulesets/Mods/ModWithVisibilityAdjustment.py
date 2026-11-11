""""
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
from parsecore.Rulesets.Mods.IApplicableToBeatmap import IApplicableToBeatmap
from parsecore.Rulesets.Mods.Mod import Mod
from parsecore.Rulesets.Objects.HitObject import HitObject


class ModWithVisibilityAdjustment(Mod, IApplicableToBeatmap):
    """Base class for mods that adjust the visibility of hit objects."""
    FirstObject: HitObject | None = None

    @staticmethod
    def IsFirstAdjustableObject(hit_object: HitObject) -> bool:
        """Determine whether the given hit object is eligible to be marked as the first object.

        Args:
            hit_object: The hit object to test.

        Returns:
            True if the hit object can be adjusted, False otherwise.
        """
        return True

    def ApplyToBeatmap(self, beatmap: Beatmap) -> None:
        """Find and store the first adjustable hit object in the beatmap.

        Args:
            beatmap: The beatmap to search.
        """
        def get_first_adjustable_object_recursive(hit_objects: list[HitObject]) -> HitObject | None:
            for hit_object in hit_objects:
                if self.IsFirstAdjustableObject(hit_object):
                    return hit_object

                nested = get_first_adjustable_object_recursive(hit_object.NestedHitObjects)
                if nested is not None:
                    return nested

            return None

        self.FirstObject = get_first_adjustable_object_recursive(beatmap.HitObjects)