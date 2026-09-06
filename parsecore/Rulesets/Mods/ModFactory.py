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

from collections.abc import Mapping, Sequence
from typing import Any

from parsecore.Rulesets.Catch.Mods.CatchModEasy import CatchModEasy
from parsecore.Rulesets.Catch.Mods.CatchModHardRock import CatchModHardRock
from parsecore.Rulesets.Mania.Mods.ManiaKeyMod import (
    ManiaModKey1,
    ManiaModKey2,
    ManiaModKey3,
    ManiaModKey4,
    ManiaModKey5,
    ManiaModKey6,
    ManiaModKey7,
    ManiaModKey8,
    ManiaModKey9,
    ManiaModKey10,
)
from parsecore.Rulesets.Mania.Mods.ManiaModDaycore import ManiaModDaycore
from parsecore.Rulesets.Mania.Mods.ManiaModDoubleTime import ManiaModDoubleTime
from parsecore.Rulesets.Mania.Mods.ManiaModDualStages import ManiaModDualStages
from parsecore.Rulesets.Mania.Mods.ManiaModEasy import ManiaModEasy
from parsecore.Rulesets.Mania.Mods.ManiaModHalfTime import ManiaModHalfTime
from parsecore.Rulesets.Mania.Mods.ManiaModHardRock import ManiaModHardRock
from parsecore.Rulesets.Mania.Mods.ManiaModNightcore import ManiaModNightcore
from parsecore.Rulesets.Mods.Mod import Mod
from parsecore.Rulesets.Mods.ModAutoplay import ModAutoplay
from parsecore.Rulesets.Mods.ModClassic import ModClassic
from parsecore.Rulesets.Mods.ModDaycore import ModDaycore
from parsecore.Rulesets.Mods.ModDoubleTime import ModDoubleTime
from parsecore.Rulesets.Mods.ModFlashlight import ModFlashlight
from parsecore.Rulesets.Mods.ModHalfTime import ModHalfTime
from parsecore.Rulesets.Mods.ModHidden import ModHidden
from parsecore.Rulesets.Mods.ModMirror import ModMirror
from parsecore.Rulesets.Mods.ModNightcore import ModNightcore
from parsecore.Rulesets.Mods.ModNoFail import ModNoFail
from parsecore.Rulesets.Mods.ModPerfect import ModPerfect
from parsecore.Rulesets.Mods.ModRelax import ModRelax
from parsecore.Rulesets.Mods.ModScoreV2 import ModScoreV2
from parsecore.Rulesets.Mods.ModSuddenDeath import ModSuddenDeath
from parsecore.Rulesets.Osu.Mods.OsuModAutopilot import OsuModAutopilot
from parsecore.Rulesets.Osu.Mods.OsuModBlinds import OsuModBlinds
from parsecore.Rulesets.Osu.Mods.OsuModClassic import OsuModClassic
from parsecore.Rulesets.Osu.Mods.OsuModDeflate import OsuModDeflate
from parsecore.Rulesets.Osu.Mods.OsuModEasy import OsuModEasy
from parsecore.Rulesets.Osu.Mods.OsuModFlashlight import OsuModFlashlight
from parsecore.Rulesets.Osu.Mods.OsuModHardRock import OsuModHardRock
from parsecore.Rulesets.Osu.Mods.OsuModHidden import OsuModHidden
from parsecore.Rulesets.Osu.Mods.OsuModMagnetised import OsuModMagnetised
from parsecore.Rulesets.Osu.Mods.OsuModNoFail import OsuModNoFail
from parsecore.Rulesets.Osu.Mods.OsuModRelax import OsuModRelax
from parsecore.Rulesets.Osu.Mods.OsuModSpunOut import OsuModSpunOut
from parsecore.Rulesets.Osu.Mods.OsuModTouchDevice import OsuModTouchDevice
from parsecore.Rulesets.Osu.Mods.OsuModTraceable import OsuModTraceable
from parsecore.Rulesets.Taiko.Mods.TaikoModEasy import TaikoModEasy
from parsecore.Rulesets.Taiko.Mods.TaikoModHardRock import TaikoModHardRock


class UnknownModError(ValueError):
    """Raised for an acronym the requested ruleset has no mod for."""


_OSU_MODS: dict[str, type[Mod]] = {
    "EZ": OsuModEasy,
    "NF": OsuModNoFail,
    "HT": ModHalfTime,
    "DC": ModDaycore,
    "HR": OsuModHardRock,
    "SD": ModSuddenDeath,
    "PF": ModPerfect,
    "DT": ModDoubleTime,
    "NC": ModNightcore,
    "HD": OsuModHidden,
    "TC": OsuModTraceable,
    "FL": OsuModFlashlight,
    "BL": OsuModBlinds,
    "CL": OsuModClassic,
    "MR": ModMirror,
    "AT": ModAutoplay,
    "RX": OsuModRelax,
    "AP": OsuModAutopilot,
    "SO": OsuModSpunOut,
    "DF": OsuModDeflate,
    "MG": OsuModMagnetised,
    "TD": OsuModTouchDevice,
}

_TAIKO_MODS: dict[str, type[Mod]] = {
    "EZ": TaikoModEasy,
    "NF": ModNoFail,
    "HT": ModHalfTime,
    "DC": ModDaycore,
    "HR": TaikoModHardRock,
    "SD": ModSuddenDeath,
    "PF": ModPerfect,
    "DT": ModDoubleTime,
    "NC": ModNightcore,
    "HD": ModHidden,
    "FL": ModFlashlight,
    "CL": ModClassic,
    "AT": ModAutoplay,
    "RX": ModRelax,
}

_CATCH_MODS: dict[str, type[Mod]] = {
    "EZ": CatchModEasy,
    "NF": ModNoFail,
    "HT": ModHalfTime,
    "DC": ModDaycore,
    "HR": CatchModHardRock,
    "SD": ModSuddenDeath,
    "PF": ModPerfect,
    "DT": ModDoubleTime,
    "NC": ModNightcore,
    "HD": ModHidden,
    "FL": ModFlashlight,
    "CL": ModClassic,
    "MR": ModMirror,
    "AT": ModAutoplay,
    "RX": ModRelax,
}

_MANIA_MODS: dict[str, type[Mod]] = {
    "EZ": ManiaModEasy,
    "NF": ModNoFail,
    "HT": ManiaModHalfTime,
    "DC": ManiaModDaycore,
    "HR": ManiaModHardRock,
    "SD": ModSuddenDeath,
    "PF": ModPerfect,
    "DT": ManiaModDoubleTime,
    "NC": ManiaModNightcore,
    "HD": ModHidden,
    "FL": ModFlashlight,
    "DS": ManiaModDualStages,
    "MR": ModMirror,
    "CL": ModClassic,
    "AT": ModAutoplay,
    "SV2": ModScoreV2,
    "1K": ManiaModKey1,
    "2K": ManiaModKey2,
    "3K": ManiaModKey3,
    "4K": ManiaModKey4,
    "5K": ManiaModKey5,
    "6K": ManiaModKey6,
    "7K": ManiaModKey7,
    "8K": ManiaModKey8,
    "9K": ManiaModKey9,
    "10K": ManiaModKey10,
}

_MODS_BY_RULESET: dict[int, dict[str, type[Mod]]] = {
    0: _OSU_MODS,
    1: _TAIKO_MODS,
    2: _CATCH_MODS,
    3: _MANIA_MODS,
}


def GetModsFor(ruleset_id: int) -> dict[str, type[Mod]]:
    """Return the mods a ruleset can be played with, by acronym.

    Args:
        ruleset_id: Ruleset id, ``0`` to ``3``.

    Returns:
        A copy of the ruleset's table, so a caller cannot change it.

    Raises:
        UnknownModError: If there is no such ruleset.
    """
    table = _MODS_BY_RULESET.get(ruleset_id)
    if table is None:
        raise UnknownModError(f"no ruleset with id {ruleset_id}")
    return dict(table)


def CreateModFromAcronym(acronym: str, ruleset_id: int, **settings: Any) -> Mod:
    """Return the mod a ruleset means by an acronym.

    Args:
        acronym: The mod's acronym, such as ``"HD"``. Case does not matter.
        ruleset_id: Ruleset id, ``0`` to ``3``.
        **settings: Anything the mod's constructor takes, such as
            ``no_slider_head_accuracy=False`` for osu!'s classic mod.

    Returns:
        A new mod, the same one its class would have built.

    Raises:
        UnknownModError: If the ruleset has no mod with that acronym.
    """
    table = GetModsFor(ruleset_id)
    mod_type = table.get(acronym.strip().upper())
    if mod_type is None:
        raise UnknownModError(
            f"ruleset {ruleset_id} has no mod {acronym!r}; "
            f"it has {', '.join(sorted(table))}"
        )
    return mod_type(**settings)


def CreateModsFromAcronyms(
    acronyms: Sequence[str],
    ruleset_id: int,
    settings: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[Mod]:
    """Return the mods a ruleset means by a list of acronyms.

    The order is kept, because the conversion pipeline applies mods in the
    order it is given them.

    Args:
        acronyms: The mods' acronyms, such as ``["HD", "DT"]``. An empty list
            means no mods, which is how a score with none is described.
        ruleset_id: Ruleset id, ``0`` to ``3``.
        settings: Constructor arguments per acronym, such as
            ``{"CL": {"no_slider_head_accuracy": False}}``.

    Returns:
        A new mod per acronym, in the order they were given.

    Raises:
        UnknownModError: If the ruleset has no mod for one of the acronyms, or
            if the same mod is named twice.
    """
    settings = settings or {}
    mods: list[Mod] = []
    seen: set[str] = set()

    for acronym in acronyms:
        key = acronym.strip().upper()
        if key in seen:
            raise UnknownModError(f"{key} is named more than once")
        seen.add(key)
        mods.append(
            CreateModFromAcronym(key, ruleset_id, **dict(settings.get(key, {})))
        )

    return mods
