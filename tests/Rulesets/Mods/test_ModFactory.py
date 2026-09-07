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

import pytest

from parsecore.Beatmaps.Formats.LegacyBeatmapDecoder import LegacyBeatmapDecoder
from parsecore.Beatmaps.WorkingBeatmap import WorkingBeatmap
from parsecore.Rulesets.Catch.Mods.CatchModEasy import CatchModEasy
from parsecore.Rulesets.Catch.Mods.CatchModHardRock import CatchModHardRock
from parsecore.Rulesets.Mania.Mods.IManiaRateAdjustmentMod import (
    IManiaRateAdjustmentMod,
)
from parsecore.Rulesets.Mania.Mods.ManiaKeyMod import ManiaModKey4
from parsecore.Rulesets.Mania.Mods.ManiaModDaycore import ManiaModDaycore
from parsecore.Rulesets.Mania.Mods.ManiaModDoubleTime import ManiaModDoubleTime
from parsecore.Rulesets.Mania.Mods.ManiaModEasy import ManiaModEasy
from parsecore.Rulesets.Mania.Mods.ManiaModHalfTime import ManiaModHalfTime
from parsecore.Rulesets.Mania.Mods.ManiaModHardRock import ManiaModHardRock
from parsecore.Rulesets.Mania.Mods.ManiaModNightcore import ManiaModNightcore
from parsecore.Rulesets.Mods.Mod import Mod
from parsecore.Rulesets.Mods.ModDoubleTime import ModDoubleTime
from parsecore.Rulesets.Mods.ModFactory import (
    CreateModFromAcronym,
    CreateModsFromAcronyms,
    GetModsFor,
    UnknownModError,
)
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapConverter import OsuBeatmapConverter
from parsecore.Rulesets.Osu.Beatmaps.OsuBeatmapProcessor import OsuBeatmapProcessor
from parsecore.Rulesets.Osu.Difficulty.OsuDifficultyCalculator import (
    OsuDifficultyCalculator,
)
from parsecore.Rulesets.Osu.Mods.OsuModClassic import OsuModClassic
from parsecore.Rulesets.Osu.Mods.OsuModEasy import OsuModEasy
from parsecore.Rulesets.Osu.Mods.OsuModHardRock import OsuModHardRock
from parsecore.Rulesets.Osu.Mods.OsuModHidden import OsuModHidden
from parsecore.Rulesets.Taiko.Mods.TaikoModEasy import TaikoModEasy
from parsecore.Rulesets.Taiko.Mods.TaikoModHardRock import TaikoModHardRock

RULESETS = (0, 1, 2, 3)


@pytest.mark.parametrize("ruleset_id", RULESETS)
def test_every_entry_is_a_mod_carrying_its_own_key(ruleset_id):
    """A table entry is a mod class whose acronym is the key it sits under.

    This is what catches a table written by hand drifting from the classes it
    names, which is the one way this can silently return the wrong mod.
    """
    for acronym, mod_type in GetModsFor(ruleset_id).items():
        assert issubclass(mod_type, Mod)
        assert mod_type.Acronym == acronym


@pytest.mark.parametrize("ruleset_id", RULESETS)
def test_every_entry_can_be_built(ruleset_id):
    """Every registered mod builds with no arguments."""
    for acronym in GetModsFor(ruleset_id):
        mod = CreateModFromAcronym(acronym, ruleset_id)
        assert isinstance(mod, Mod)
        assert mod.Acronym == acronym


@pytest.mark.parametrize(
    ("acronym", "ruleset_id", "expected"),
    [
        ("HR", 0, OsuModHardRock),
        ("HR", 1, TaikoModHardRock),
        ("HR", 2, CatchModHardRock),
        ("HR", 3, ManiaModHardRock),
        ("EZ", 0, OsuModEasy),
        ("EZ", 1, TaikoModEasy),
        ("EZ", 2, CatchModEasy),
        ("EZ", 3, ManiaModEasy),
        ("DT", 0, ModDoubleTime),
        ("DT", 3, ManiaModDoubleTime),
        ("HT", 3, ManiaModHalfTime),
        ("NC", 3, ManiaModNightcore),
        ("DC", 3, ManiaModDaycore),
        ("HD", 0, OsuModHidden),
        ("CL", 0, OsuModClassic),
        ("4K", 3, ManiaModKey4),
    ],
)
def test_acronym_resolves_to_the_ruleset_s_own_mod(acronym, ruleset_id, expected):
    """An acronym gives the class that ruleset means by it."""
    assert type(CreateModFromAcronym(acronym, ruleset_id)) is expected


def test_case_and_spacing_are_ignored():
    """An acronym is read as written, however it was typed."""
    assert type(CreateModFromAcronym(" hd ", 0)) is OsuModHidden


def test_a_list_keeps_its_order():
    """Mods come back in the order they were asked for.

    The conversion pipeline applies them in list order, so this is not merely
    cosmetic.
    """
    mods = CreateModsFromAcronyms(["DT", "HD", "CL"], 0)
    assert [m.Acronym for m in mods] == ["DT", "HD", "CL"]


def test_no_acronyms_means_no_mods():
    """An empty list is how a score with no mods is described."""
    assert CreateModsFromAcronyms([], 0) == []


def test_settings_reach_the_constructor():
    """A mod that takes a setting is built with it."""
    mod = CreateModFromAcronym("CL", 0, no_slider_head_accuracy=False)
    assert mod.NoSliderHeadAccuracy is False

    (built,) = CreateModsFromAcronyms(
        ["CL"], 0, settings={"CL": {"no_slider_head_accuracy": False}}
    )
    assert built.NoSliderHeadAccuracy is False


def test_a_mod_the_ruleset_lacks_is_refused():
    """An acronym without a mod behind it raises rather than disappearing.

    A mod dropped in silence is only noticed later, as a value that is wrong by
    an amount nobody can place.
    """
    with pytest.raises(UnknownModError):
        CreateModFromAcronym("XY", 0)

    with pytest.raises(UnknownModError):
        CreateModFromAcronym("SO", 3)
    with pytest.raises(UnknownModError):
        CreateModFromAcronym("RX", 3)

    with pytest.raises(UnknownModError):
        GetModsFor(7)


def test_the_same_mod_twice_is_refused():
    """Naming a mod twice is a mistake, not a request for two of them."""
    with pytest.raises(UnknownModError):
        CreateModsFromAcronyms(["HD", "hd"], 0)


@pytest.mark.parametrize("ruleset_id", RULESETS)
def test_the_table_cannot_be_changed_from_outside(ruleset_id):
    """A caller holding the table cannot alter what the next one gets."""
    table = GetModsFor(ruleset_id)
    table.clear()
    assert GetModsFor(ruleset_id)


@pytest.mark.parametrize(
    ("acronyms", "classes"),
    [
        ([], []),
        (["HD"], [OsuModHidden]),
        (["HR"], [OsuModHardRock]),
        (["EZ"], [OsuModEasy]),
        (["DT"], [ModDoubleTime]),
        (["HR", "DT", "HD"], [OsuModHardRock, ModDoubleTime, OsuModHidden]),
    ],
)
def test_both_ways_of_naming_a_mod_rate_the_same(beatmap_files, acronyms, classes):
    """An acronym and its class produce the same rating, to the last bit.

    This is the point of the whole thing: the factory must be another way of
    saying the same, never another way of arriving somewhere else.
    """
    def rate(decoded, mods):
        playable = WorkingBeatmap(decoded).GetPlayableBeatmap(
            OsuBeatmapConverter, OsuBeatmapProcessor, mods
        )
        return OsuDifficultyCalculator(playable, decoded).Calculate(mods).StarRating

    rated = 0
    for path in beatmap_files:
        decoded = LegacyBeatmapDecoder.FromPath(str(path))
        if decoded.BeatmapInfo.RulesetID != 0:
            continue
        by_acronym = rate(decoded, CreateModsFromAcronyms(acronyms, 0))
        by_class = rate(decoded, [cls() for cls in classes])
        assert by_acronym == by_class
        rated += 1

    assert rated, "no osu! beatmaps among the test files"


@pytest.mark.parametrize("acronym", ["DT", "HT", "NC", "DC"])
def test_every_mania_rate_mod_scales_the_hit_windows(acronym):
    """Mania's rate mods all move the judgement windows with the rate.

    Each is its own class purely for that. Nothing in the current rating reads
    those windows, so today the shared mod of the same acronym would give the
    same number; this pins the mod a mania score is actually set with, so that
    the day something does read them the answer is already right.
    """
    mod = CreateModFromAcronym(acronym, 3)
    assert isinstance(mod, IManiaRateAdjustmentMod)
