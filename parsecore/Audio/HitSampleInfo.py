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

from parsecore.Beatmaps.ControlPoints.SampleControlPoint import DEFAULT_BANK
from parsecore.Beatmaps.Formats import Parsing

HIT_NORMAL = "hitnormal"
HIT_WHISTLE = "hitwhistle"
HIT_FINISH = "hitfinish"
HIT_CLAP = "hitclap"

BANK_NORMAL = "normal"
BANK_SOFT = "soft"
BANK_DRUM = "drum"

ALL_ADDITIONS = (HIT_WHISTLE, HIT_FINISH, HIT_CLAP)
ALL_BANKS = (BANK_NORMAL, BANK_SOFT, BANK_DRUM)


class HitSampleInfo:
    """One sample: which sound, from which bank, at which volume."""

    def __init__(
            self,
            name: str,
            bank: str = DEFAULT_BANK,
            suffix: str | None = None,
            volume: int = 100,
            editor_auto_bank = True,
            use_beatmap_samples: bool = False
    ) -> None:
        """Create a sample.

        Args:
            name: The sample name, for example ``hitnormal``.
            bank: The bank the sample comes from.
            suffix: The custom sample bank suffix, or ``None`` for none.
            volume: The playback volume, from 0 to 100.
            editor_auto_bank: Whether the editor may pick the bank itself.
            use_beatmap_samples: Whether the beatmap's own samples are used.
        """
        self.Name = name
        self.Bank = bank
        self.Suffix = suffix
        self.Volume = volume
        self.EditorAutoBank = editor_auto_bank
        self.UseBeatmapSamples = use_beatmap_samples

    @property
    def LookupNames(self) -> list[str]:
        """Return the sample file names to try, most specific first."""
        names = []
        if self.Suffix:
            names.append(f"Gameplay/{self.Bank}-{self.Name}{self.Suffix}")
        names.append(f"Gameplay/{self.Bank}-{self.Name}")
        names.append(f"Gameplay/{self.Name}")
        return names

    def With(
            self,
            Name: str | None = None,
            Bank: str | None = None,
            Suffix: str | None = None,
            Volume: int | None = None,
            EditorAutoBank: bool | None = None,
            UseBeatmapSamples: bool | None = None
    ) -> HitSampleInfo:
        """Return a copy with the given fields replaced.

        Args:
            Name: The new sample name, or ``None`` to keep the current one.
            Bank: The new bank, or ``None`` to keep the current one.
            Suffix: The new suffix, or ``None`` to keep the current one.
            Volume: The new volume, or ``None`` to keep the current one.
            EditorAutoBank: The new auto-bank flag, or ``None`` to keep it.
            UseBeatmapSamples: The new beatmap samples flags or ``None`` to keep it.

        Returns:
            The modified copy.
        """
        return HitSampleInfo(
            Name if Name is not None else self.Name,
            Bank if Bank is not None else self.Bank,
            Suffix if Suffix is not None else self.Suffix,
            Volume if Volume is not None else self.Volume,
            EditorAutoBank if EditorAutoBank is not None else self.EditorAutoBank,
            UseBeatmapSamples if UseBeatmapSamples is not None else self.UseBeatmapSamples
        )


class LegacyHitSampleInfo(HitSampleInfo):
    """A sample that remembers what the beatmap said about it.

    Which of its fields the beatmap set and which it left open decides what a
    sample control point is allowed to fill in later.
    """

    def __init__(
            self,
            name: str,
            bank: str | None = None,
            volume: int = 0,
            editor_auto_bank: bool = False,
            custom_sample_bank: int = 0,
            is_layered: bool = False
    ) -> None:
        """Create a legacy sample, decoding the custom sample bank.

        A custom bank of 2 or higher becomes the sample suffix; any custom
        bank of 1 or higher implies the beatmap's own samples are in use.

        Args:
            name: The sample name, for example ``hitnormal``.
            bank: The bank the beatmap set, or ``None`` if it left it open.
            volume: The volume the beatmap set, or 0 if it left it open.
            editor_auto_bank: Whether the editor may pick the bank itself.
            custom_sample_bank: The legacy custom sample bank number.
            is_layered: Whether this sample plays on top of others.
        """
        super().__init__(
            name,
            bank if bank is not None else DEFAULT_BANK,
            f"{custom_sample_bank}" if custom_sample_bank >= 2 else None,
            volume,
            editor_auto_bank,
            custom_sample_bank >= 1
        )
        self.BankSpecified = bank
        self.IsLayered = is_layered

    @property
    def CustomSampleBank(self) -> int:
        """Return the legacy custom sample bank number, 0 when unset."""
        if self.Suffix is not None:
            return int(self.Suffix)
        return 1 if self.UseBeatmapSamples else 0

    def WithCustomBank(
            self,
            Name: str | None = None,
            Bank: str | None = None,
            Volume: int | None = None,
            EditorAutoBank: bool | None = None,
            CustomSampleBank: int | None = None,
            IsLayered: bool | None = None
    ) -> LegacyHitSampleInfo:
        """Return a copy with the given legacy fields replaced.

        Args:
            Name: The new sample name, or ``None`` to keep the current one.
            Bank: The new bank, or ``None`` to keep the current one.
            Volume: The new volume, or ``None`` to keep the current one.
            EditorAutoBank: The new auto-bank flag, or ``None`` to keep it.
            CustomSampleBank: The new custom sample bank, or ``None`` to keep it.
            IsLayered: The new layered flag, or ``None`` to keep it.

        Returns:
            The modified copy.
        """
        return LegacyHitSampleInfo(
            Name if Name is not None else self.Name,
            Bank if Bank is not None else self.Bank,
            Volume if Volume is not None else self.Volume,
            EditorAutoBank if EditorAutoBank is not None else self.EditorAutoBank,
            CustomSampleBank if CustomSampleBank is not None else self.CustomSampleBank,
            IsLayered if IsLayered is not None else self.IsLayered
        )

    def With(
            self,
            Name: str | None = None,
            Bank: str | None = None,
            Suffix: str | None = None,
            Volume: int | None = None,
            EditorAutoBank: bool | None = None,
            UseBeatmapSamples: bool | None = None
    ) -> HitSampleInfo:
        """Return a copy with the given fields replaced.

        The suffix and the beatmap-samples flag fold back into the legacy
        custom sample bank, which is what the returned copy stores.

        Args:
            Name: The new sample name, or ``None`` to keep the current one.
            Bank: The new bank, or ``None`` to keep the current one.
            Suffix: The new suffix, or ``None`` to keep the current one.
            Volume: The new volume, or ``None`` to keep the current one.
            EditorAutoBank: The new auto-bank flag, or ``None`` to keep it.
            UseBeatmapSamples: The new beatmap-samples flag, or ``None`` to keep it.

        Returns:
            The modified copy.
        """
        suffix = Suffix if Suffix is not None else self.Suffix
        use_beatmap_samples = UseBeatmapSamples if UseBeatmapSamples is not None else self.UseBeatmapSamples
        new_custom_sample_bank = 0

        if suffix is not None:
            new_custom_sample_bank = Parsing.TryParseInt(suffix)

        if new_custom_sample_bank == 0 and use_beatmap_samples:
            new_custom_sample_bank = 1

        return self.WithCustomBank(Name, Bank, Volume, EditorAutoBank, new_custom_sample_bank)


class FileHitSampleInfo(LegacyHitSampleInfo):
    """A sample the beatmap names by file rather than by bank and sound.

    osu! still calls this a normal hit sound -- :attr:`Name` stays
    ``hitnormal`` -- and :meth:`With` refuses to rename it, because the file is
    what identifies it. That refusal is visible in gameplay: asking such a
    sample to become a finish sound silently returns a normal one, which is how
    a converted note can fail to turn strong.
    """

    def __init__(self, filename: str, volume: int) -> None:
        """Create a file-based hit sample info object.

        Args:
            filename: The audio filename associated with this sample.
            volume: The playback volume, from 0 to 100.
        """
        LegacyHitSampleInfo.__init__(self, HIT_NORMAL, DEFAULT_BANK, custom_sample_bank=1, volume=volume)
        self.Filename = filename

    @property
    def LookupNames(self) -> list[str]:
        """Return the file to play, then the usual bank lookups."""
        stem = self.Filename.rsplit(".", 1)[0] if "." in self.Filename else self.Filename
        # ``super()`` cannot be used here: the slotted dataclass decorator
        # builds a replacement class, and the implicit reference still
        # points at the original one.
        return [self.Filename, stem, *HitSampleInfo.LookupNames.fget(self)]

    def With(
            self,
            Name: str | None = None,
            Bank: str | None = None,
            Suffix: str | None = None,
            Volume: int | None = None,
            EditorAutoBank: bool | None = None,
            UseBeatmapSamples: bool | None = None
    ) -> FileHitSampleInfo:
        """Return a copy, keeping everything but the volume.

        Args:
            Name: Ignored; the file decides what this sample is.
            Bank: Ignored.
            Suffix: Ignored.
            Volume: The new volume, or ``None`` to keep the current one.
            EditorAutoBank: Ignored.
            UseBeatmapSamples: Ignored.

        Returns:
            The copy.
        """
        return FileHitSampleInfo(self.Filename, Volume if Volume is not None else self.Volume)
