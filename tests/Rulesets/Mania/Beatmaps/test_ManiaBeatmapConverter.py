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

from parsecore.Rulesets.Mania.Beatmaps.ManiaBeatmapConverter import (
    ManiaBeatmapConverter,
)
from parsecore.Rulesets.Mania.Mods.ManiaKeyMod import (
    ManiaModKey4,
    ManiaModKey7,
    ManiaModKey9,
)
from parsecore.Rulesets.Mania.Mods.ManiaModDualStages import ManiaModDualStages
from parsecore.Rulesets.Mania.Objects.HoldNote import HoldNote
from parsecore.Rulesets.Mania.Objects.Note import Note
from parsecore.Rulesets.Scoring.Legacy.LegacyBeatmapConversionDifficultyInfo import (
    LegacyBeatmapConversionDifficultyInfo,
)
from tests.Rulesets.Mania.conftest import (
    convert,
    decode_mania,
    decode_osu,
    hold,
    notes_in,
)

MANIA_RULESET_ID = 3


WANDERING = (60, 180, 300, 420, 150, 380)


def circles(count: int, gap: float = 250.0, positions=(256,)) -> str:
    """Return hit object lines for a run of osu! circles.

    Args:
        count: How many circles to write.
        gap: How long to leave between them.
        positions: The positions to place them at, cycled through.
    """
    return "".join(
        f"{positions[i % len(positions)]},192,{1000 + int(i * gap)},1,0\n"
        for i in range(count)
    )


def _columns(difficulty_kwargs) -> int:
    """Return how many columns a beatmap with given settings converts to.

    Args:
        difficulty_kwargs: The settings to build the conversion info from.
    """
    info = LegacyBeatmapConversionDifficultyInfo(**difficulty_kwargs)
    return ManiaBeatmapConverter(_EmptyBeatmap(), info).TotalColumns


class _EmptyBeatmap:
    """A beatmap with nothing in it, for testing the column count alone."""

    HitObjects: list = []


def test_a_mania_beatmap_takes_its_columns_from_its_circle_size():
    """A beatmap written for mania says how many columns it has."""
    for keys in (4, 5, 7):
        beatmap = convert(decode_mania(notes_in(0, keys=keys), keys=keys))
        assert beatmap.TotalColumns == keys


def test_a_beatmap_of_mostly_circles_becomes_seven_keys():
    """Under a fifth of held objects, osu! always picks seven columns."""
    assert (
        _columns(
            {
                "SourceRulesetID": 0,
                "CircleSize": 4,
                "OverallDifficulty": 7,
                "TotalObjectCount": 100,
                "EndTimeObjectCount": 10,
            }
        )
        == 7
    )


def test_a_beatmap_of_mostly_held_objects_becomes_four_or_five_keys():
    """Above three fifths of held objects, the difficulty picks four or five."""
    common = {"SourceRulesetID": 0, "CircleSize": 4, "TotalObjectCount": 100}

    assert _columns({**common, "OverallDifficulty": 3, "EndTimeObjectCount": 70}) == 4
    assert _columns({**common, "OverallDifficulty": 7, "EndTimeObjectCount": 70}) == 5


def test_a_high_circle_size_pushes_the_column_count_up():
    """A large circle size is read as a busier beatmap."""
    common = {
        "SourceRulesetID": 0,
        "TotalObjectCount": 100,
        "EndTimeObjectCount": 25,
    }

    assert _columns({**common, "CircleSize": 2, "OverallDifficulty": 3}) == 6
    assert _columns({**common, "CircleSize": 5, "OverallDifficulty": 7}) == 7


def test_an_empty_beatmap_falls_back_to_the_difficulty():
    """With nothing to measure, the overall difficulty picks the columns."""
    common = {"SourceRulesetID": 0, "CircleSize": 4, "TotalObjectCount": 0}

    assert _columns({**common, "OverallDifficulty": 0}) == 4
    assert _columns({**common, "OverallDifficulty": 5}) == 6
    assert _columns({**common, "OverallDifficulty": 9}) == 7


def test_a_mania_beatmap_never_has_fewer_than_one_column():
    """A circle size of zero would leave nothing to play on."""
    assert (
        _columns({"SourceRulesetID": MANIA_RULESET_ID, "CircleSize": 0}) == 1
    )


def test_a_converted_beatmap_always_comes_out_the_same():
    """The columns are drawn at random from a seed the beatmap itself sets."""
    decoded = decode_osu(circles(40))

    first = [h.Column for h in convert(decoded).HitObjects]
    second = [h.Column for h in convert(decoded).HitObjects]

    assert first == second


def test_the_seed_comes_from_the_beatmap_s_own_settings():
    """Two beatmaps differing only in difficulty convert differently.

    The circles have to move about for this to show: a run of circles on one
    spot is mirrored from the row before rather than drawn, so the seed never
    comes into it.
    """
    objects = circles(40, positions=WANDERING)

    lenient = [h.Column for h in convert(decode_osu(objects, od=3.0)).HitObjects]
    strict = [h.Column for h in convert(decode_osu(objects, od=9.0)).HitObjects]

    assert lenient != strict


def test_a_run_of_circles_on_one_spot_is_mirrored_rather_than_drawn():
    """A low density stream is generated by reversing the row before it.

    Nothing is drawn from the generator for these, which is why they convert
    the same way whatever the beatmap's settings are.
    """
    objects = circles(40)

    lenient = [h.Column for h in convert(decode_osu(objects, od=3.0)).HitObjects]
    strict = [h.Column for h in convert(decode_osu(objects, od=9.0)).HitObjects]

    assert lenient == strict


def test_a_key_mod_sets_the_column_count_of_a_convert():
    """A key mod overrides what the beatmap would have been given."""
    decoded = decode_osu(circles(30))

    assert convert(decoded, [ManiaModKey4()]).TotalColumns == 4
    assert convert(decoded, [ManiaModKey7()]).TotalColumns == 7
    assert convert(decoded, [ManiaModKey9()]).TotalColumns == 9


def test_a_key_mod_leaves_a_mania_beatmap_alone():
    """The columns of a mania beatmap are part of the beatmap, not a setting."""
    decoded = decode_mania(notes_in(0, 1, 2, 3, keys=4), keys=4)

    assert convert(decoded, [ManiaModKey7()]).TotalColumns == 4


def test_dual_stages_doubles_a_convert():
    """The dual stages mod lays a converted beatmap across two stages."""
    beatmap = convert(decode_osu(circles(30)), [ManiaModDualStages()])

    assert len(beatmap.Stages) == 2
    assert beatmap.TotalColumns == beatmap.Stages[0].Columns * 2


def test_dual_stages_leaves_a_mania_beatmap_alone():
    """A beatmap written for mania keeps the stage it was made for."""
    beatmap = convert(
        decode_mania(notes_in(0, 1, keys=4), keys=4), [ManiaModDualStages()]
    )

    assert len(beatmap.Stages) == 1


def test_every_note_lands_on_the_stage():
    """No generated note may fall outside the columns that exist."""
    for keys in (4, 5, 6, 7, 8, 9):
        beatmap = convert(
            decode_osu(circles(60, gap=140.0, positions=WANDERING)),
            [_key_mod(keys)],
        )

        assert beatmap.TotalColumns == keys
        assert all(0 <= h.Column < keys for h in beatmap.HitObjects)


def _key_mod(keys: int):
    """Return the key mod for a number of columns.

    Args:
        keys: How many columns to convert onto.
    """
    from parsecore.Rulesets.Mania.Mods import ManiaKeyMod as module

    return getattr(module, f"ManiaModKey{keys}")()


def test_a_spinner_becomes_a_hold_when_it_is_long_enough():
    """A spinner of at least a tenth of a second is held rather than tapped."""
    long_spinner = convert(decode_osu("256,192,1000,12,0,2000\n"))
    short_spinner = convert(decode_osu("256,192,1000,12,0,1050\n"))

    assert isinstance(long_spinner.HitObjects[0], HoldNote)
    assert isinstance(short_spinner.HitObjects[0], Note)
    assert not isinstance(short_spinner.HitObjects[0], HoldNote)


def test_a_slider_becomes_more_than_one_object():
    """A slider long enough to hold turns into notes across the stage."""
    beatmap = convert(decode_osu("100,192,1000,2,0,L|300:192,1,200\n"))

    assert beatmap.HitObjects


def test_an_osu_beatmap_is_playable_by_mania():
    """Every osu! object carries a position, which is all mania needs."""
    assert ManiaBeatmapConverter(decode_osu(circles(3))).CanConvert()


@pytest.mark.parametrize("keys", [4, 7])
def test_a_hold_written_for_mania_survives_a_round_trip(keys):
    """A mania hold keeps its column, start and end through conversion."""
    beatmap = convert(
        decode_mania(hold(1, 1000, 2000, keys=keys), keys=keys), []
    )
    held = beatmap.HitObjects[0]

    assert isinstance(held, HoldNote)
    assert held.Column == 1
    assert (held.StartTime, held.EndTime) == (1000, 2000)
