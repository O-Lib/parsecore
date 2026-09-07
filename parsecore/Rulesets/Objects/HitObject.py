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

from parsecore.Audio.HitSampleInfo import HIT_NORMAL, HitSampleInfo

# A leniency applied when looking up control points, so an object sitting a
# fraction before a timing point still picks that point up.
CONTROL_POINT_LENIENCY = 5.0


class HitObject:
    """Something the player interacts with at a point in time."""

    def __init__(self, start_time: float = 0.0) -> None:
        """Create a hit object at a start time.

        Args:
            start_time: The object's time in milliseconds.
        """
        self.StartTime: float = start_time
        self.Samples: list[HitSampleInfo] = []
        self._nested_hit_objects: list[HitObject] = []
        self.HitWindows = None
        self._judgement = None

    @property
    def NestedHitObjects(self) -> list[HitObject]:
        """Return the objects generated inside this one."""
        return self._nested_hit_objects

    def GetEndTime(self) -> float:
        """Return the time this object stops being active."""
        end_time = getattr(self, "EndTime", None)
        return self.StartTime if end_time is None else end_time

    def ApplyDefaults(self, control_point_info, difficulty) -> None:
        """Apply beatmap-wide settings and rebuild the nested objects.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        self.ApplyDefaultsToSelf(control_point_info, difficulty)

        self._nested_hit_objects = []
        self.CreateNestedHitObjects()

        for nested in self._nested_hit_objects:
            nested.ApplyDefaults(control_point_info, difficulty)

        self._nested_hit_objects.sort(key=lambda h: h.StartTime)

    def ApplyDefaultsToSelf(self, control_point_info, difficulty) -> None:
        """Apply beatmap-wide settings to this object only.

        Args:
            control_point_info: The beatmap's control points.
            difficulty: The beatmap's difficulty settings.
        """
        if self.HitWindows is None:
            self.HitWindows = self.CreateHitWindows()
        if self.HitWindows is not None:
            self.HitWindows.SetDifficulty(difficulty.OverallDifficulty)

    @property
    def MaximumJudgementOffset(self) -> float:
        """Return how late this object can be hit and still be judged."""
        from parsecore.Rulesets.Scoring.HitResult import HitResult

        if self.HitWindows is None:
            return 0.0
        return self.HitWindows.WindowFor(HitResult.Miss)

    @property
    def Judgement(self):
        """Return what this object is worth when hit."""
        if self._judgement is None:
            self._judgement = self.CreateJudgement()
        return self._judgement

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Judgements.Judgement import Judgement

        return Judgement()

    def CreateHitWindows(self):
        """Return the hit windows this object is judged with."""
        from parsecore.Rulesets.Scoring.DefaultHitWindows import DefaultHitWindows

        return DefaultHitWindows()

    def CreateNestedHitObjects(self) -> None:
        """Generate the objects nested inside this one, if any."""

    def CreateHitSampleInfo(self, sample_name: str = HIT_NORMAL):
        """Return a sample of the given kind, styled like this object's own.

        osu! copies the object's normal hit sound and renames it, so the new
        sample keeps the beatmap's bank and volume. A sample the beatmap named
        by file refuses to be renamed, and the caller gets a normal sound back.

        Args:
            sample_name: The sound to create, such as ``hitfinish``.

        Returns:
            The sample to add.
        """
        existing = next((s for s in self.Samples if s.Name == HIT_NORMAL), None)
        if existing is not None:
            return existing.With(Name=sample_name)

        return HitSampleInfo(sample_name)

    def AddNested(self, hit_object: HitObject) -> None:
        """Add a nested hit object.

        Args:
            hit_object: The object to nest inside this one.
        """
        self._nested_hit_objects.append(hit_object)

    def __repr__(self) -> str:
        """Return an unambiguous representation."""
        return f"{type(self).__name__}(StartTime={self.StartTime})"
