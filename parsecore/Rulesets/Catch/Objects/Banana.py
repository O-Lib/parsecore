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

from parsecore.Audio.HitSampleInfo import HitSampleInfo
from parsecore.Beatmaps.ControlPoints.SampleControlPoint import DEFAULT_BANK
from parsecore.Rulesets.Catch.Objects.CatchHitObject import CatchHitObject
from parsecore.Rulesets.Catch.Objects.PalpableCatchHitObject import (
    PalpableCatchHitObject,
)
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows
from parsecore.Utils.Vector2 import f32

# The longest a shower waits between bananas.
MAX_BANANA_SPACING = 100.0

LOOKUP_NAMES = ["Gameplay/metronomelow", "Gameplay/catch-banana"]


class Banana(PalpableCatchHitObject):
    """One banana from a shower."""

    def __init__(self) -> None:
        """Create a banana."""

        super().__init__()
        self.BananaIndex: int = 0
        self.Samples = DEFAULT_BANANAS_SAMPLES

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Catch.Judgements.CatchJudgement import (
            CatchBananaJudgement,
        )

        return CatchBananaJudgement()


class BananaShower(CatchHitObject, IHasDuration):
    """A burst of bananas raining across the playfield."""

    def __init__(self) -> None:
        """Create a banana shower."""

        super().__init__()
        self.Duration: float = 0.0
        self.LastInCombo = True

    @property
    def EndTime(self) -> float:
        """Return when the shower ends."""
        return self.StartTime + self.Duration

    @EndTime.setter
    def EndTime(self, value: float) -> None:
        self.Duration = value - self.StartTime

    def CreateNestedHitObjects(self) -> None:
        """Drop bananas evenly across the shower."""
        super().CreateNestedHitObjects()
        self._create_bananas()

    def _create_bananas(self) -> None:
        """Place bananas at an interval short enough to feel like a shower."""
        start_time = int(self.StartTime)
        end_time = int(self.EndTime)

        spacing = f32(self.EndTime - self.StartTime)
        while spacing > MAX_BANANA_SPACING:
            spacing = f32(spacing / 2)

        if spacing <= 0:
            return

        count = 0
        time = f32(start_time)
        while time <= end_time:
            banana = Banana()
            banana.StartTime = time
            banana.BananaIndex = count
            self.AddNested(banana)

            count += 1
            time = f32(time + spacing)

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Catch.Judgements.CatchJudgement import (
            CatchIgnoreJudgement,
        )

        return CatchIgnoreJudgement()

    def CreateHitWindows(self):
        """Return no windows; a shower is judged through its bananas."""
        return EmptyHitWindows()


class BananaHitSampleInfo(HitSampleInfo):
    """Hit sample information for banana objects."""
    
    def __init__(
            self,
            name_or_info: str | HitSampleInfo | None = None,
            bank: str = DEFAULT_BANK,
            suffix: str | None = None,
            volume: int = 100,
            editor_auto_bank: bool = True,
            use_beatmap_samples: bool = False
    ) -> None:
        """Create a banana hit sample info.

        Args:
            name_or_info: The sample name or an existing HitSampleInfo to copy from.
            bank: The sample bank.
            suffix: The sample suffix.
            volume: The audio volume percentage.
            editor_auto_bank: Whether the editor automatically sets the bank.
            use_beatmap_samples: Whether to load custom beatmap samples.
        """
        if isinstance(name_or_info, HitSampleInfo):
            super().__init__(
                name=name_or_info.Name,
                bank=name_or_info.Bank,
                suffix=name_or_info.Suffix,
                volume=name_or_info.Volume,
                editor_auto_bank=name_or_info.EditorAutoBank,
                use_beatmap_samples=name_or_info.UseBeatmapSamples
            )
        else:
            super().__init__(
                name="" if name_or_info is None else name_or_info,
                bank=bank,
                suffix=suffix,
                volume=volume,
                editor_auto_bank=editor_auto_bank,
                use_beatmap_samples=use_beatmap_samples
            )

    @property
    def LookupNames(self) -> list[str]:
        """Return the audio lookup resource names for banana sounds."""
        return LOOKUP_NAMES

    def With(
            self,
            Name: str | None = None,
            Bank: str | None = None,
            Suffix: str | None = None,
            Volume: int | None = None,
            EditorAutoBank: bool | None = None,
            UseBeatmapSamples: bool | None = None
    ) -> HitSampleInfo:
        """Return a copy of this sample info with updated properties."""
        return BananaHitSampleInfo(
            name_or_info=Name if Name is not None else self.Name,
            bank=Bank if Bank is not None else self.Bank,
            suffix=Suffix if Suffix is not None else self.Suffix,
            volume=Volume if Volume is not None else self.Volume,
            editor_auto_bank=EditorAutoBank if EditorAutoBank is not None else self.EditorAutoBank,
            use_beatmap_samples=UseBeatmapSamples if UseBeatmapSamples is not None else self.UseBeatmapSamples
        )

    def __eq__(self, value: object | None) -> bool:
        """Check equality with another sample info object."""
        if not isinstance(value, BananaHitSampleInfo):
            raise NotImplementedError

        return value is not None


DEFAULT_BANANAS_SAMPLES = [BananaHitSampleInfo()]
