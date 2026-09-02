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

from dataclasses import dataclass, replace

HIT_NORMAL = "hitnormal"
HIT_WHISTLE = "hitwhistle"
HIT_FINISH = "hitfinish"
HIT_CLAP = "hitclap"

BANK_NORMAL = "normal"
BANK_SOFT = "soft"
BANK_DRUM = "drum"

ALL_ADDITIONS = (HIT_WHISTLE, HIT_FINISH, HIT_CLAP)
ALL_BANKS = (BANK_NORMAL, BANK_SOFT, BANK_DRUM)


@dataclass(frozen=True, slots=True)
class HitSampleInfo:
    """One sample: which sound, from which bank, at which volume."""

    Name: str = HIT_NORMAL
    Bank: str = BANK_NORMAL
    Suffix: str | None = None
    Volume: int = 0
    EditorAutoBank: bool = True

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
    ) -> HitSampleInfo:
        """Return a copy with the given fields replaced.

        Args:
            Name: The new sample name, or ``None`` to keep the current one.
            Bank: The new bank, or ``None`` to keep the current one.
            Suffix: The new suffix, or ``None`` to keep the current one.
            Volume: The new volume, or ``None`` to keep the current one.
            EditorAutoBank: The new auto-bank flag, or ``None`` to keep it.

        Returns:
            The modified copy.
        """
        return replace(
            self,
            Name=self.Name if Name is None else Name,
            Bank=self.Bank if Bank is None else Bank,
            Suffix=self.Suffix if Suffix is None else Suffix,
            Volume=self.Volume if Volume is None else Volume,
            EditorAutoBank=(
                self.EditorAutoBank if EditorAutoBank is None else EditorAutoBank
            ),
        )


@dataclass(frozen=True, slots=True)
class FileHitSampleInfo(HitSampleInfo):
    """A sample the beatmap names by file rather than by bank and sound.

    osu! still calls this a normal hit sound -- :attr:`Name` stays
    ``hitnormal`` -- and :meth:`With` refuses to rename it, because the file is
    what identifies it. That refusal is visible in gameplay: asking such a
    sample to become a finish sound silently returns a normal one, which is how
    a converted note can fail to turn strong.
    """

    Filename: str = ""

    # osu! forces a custom bank of one so that a beatmap's own skin cannot
    # fall back to the user's sounds for a sample the beatmap named by file.
    CustomSampleBank: int = 1
    IsLayered: bool = False
    BankSpecified: bool = True

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
    ) -> FileHitSampleInfo:
        """Return a copy, keeping everything but the volume.

        Args:
            Name: Ignored; the file decides what this sample is.
            Bank: Ignored.
            Suffix: Ignored.
            Volume: The new volume, or ``None`` to keep the current one.
            EditorAutoBank: Ignored.

        Returns:
            The copy.
        """
        return replace(self, Volume=self.Volume if Volume is None else Volume)
