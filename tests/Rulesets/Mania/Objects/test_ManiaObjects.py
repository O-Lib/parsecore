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

from parsecore.Rulesets.Mania.Objects.HeadNote import HeadNote
from parsecore.Rulesets.Mania.Objects.HoldNote import (
    CreateDefaultNodeSamples,
    HoldNote,
)
from parsecore.Rulesets.Mania.Objects.HoldNoteBody import HoldNoteBody
from parsecore.Rulesets.Mania.Objects.Note import Note
from parsecore.Rulesets.Mania.Objects.TailNote import TailNote
from parsecore.Rulesets.Scoring.HitResult import HitResult
from tests.Rulesets.Mania.conftest import convert, decode_mania, hold, notes_in


def _applied(hold_note: HoldNote) -> HoldNote:
    """Return a hold note with its ends built, as the pipeline would.

    Args:
        hold_note: The hold to prepare.
    """
    from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
    from parsecore.Beatmaps.ControlPoints.ControlPointInfo import ControlPointInfo

    hold_note.ApplyDefaults(ControlPointInfo(), BeatmapDifficulty())
    return hold_note


def test_a_note_belongs_to_a_column():
    """A mania note is nothing but a time and a column."""
    note = Note()
    note.StartTime = 1000.0
    note.Column = 3

    assert note.StartTime == 1000.0
    assert note.Column == 3


def test_a_column_is_written_out_as_a_position():
    """osu! stores the column in the x position column of the file."""
    note = Note()
    note.StartTime = 0.0
    note.Column = 5

    assert note.X == 5.0


def test_a_hold_note_is_played_through_its_ends():
    """A hold builds a head, a tail and a body, and is judged through them."""
    hold_note = HoldNote()
    hold_note.StartTime = 1000.0
    hold_note.Duration = 500.0
    hold_note.Column = 2
    held = _applied(hold_note)

    assert isinstance(held.Head, HeadNote)
    assert isinstance(held.Tail, TailNote)
    assert isinstance(held.Body, HoldNoteBody)

    assert held.Head.StartTime == 1000.0
    assert held.Tail.StartTime == 1500.0
    assert held.Body.Duration == 500.0
    assert held.EndTime == 1500.0


def test_moving_a_hold_drags_its_ends_along():
    """Changing a hold's time moves its head and tail with it."""
    hold_note = HoldNote()
    hold_note.StartTime = 1000.0
    hold_note.Duration = 500.0
    hold_note.Column = 2
    held = _applied(hold_note)

    held.StartTime = 2000.0

    assert held.Head.StartTime == 2000.0
    assert held.Tail.StartTime == 2500.0


def test_resizing_a_hold_moves_its_tail():
    """Changing a hold's duration moves its tail but not its head."""
    hold_note = HoldNote()
    hold_note.StartTime = 1000.0
    hold_note.Duration = 500.0
    hold_note.Column = 2
    held = _applied(hold_note)

    held.Duration = 900.0

    assert held.Head.StartTime == 1000.0
    assert held.Tail.StartTime == 1900.0


def test_moving_a_hold_sideways_drags_its_ends_along():
    """Changing a hold's column moves its head and tail with it."""
    hold_note = HoldNote()
    hold_note.StartTime = 1000.0
    hold_note.Duration = 500.0
    hold_note.Column = 2
    held = _applied(hold_note)

    held.Column = 5

    assert held.Head.Column == 5
    assert held.Tail.Column == 5


def test_a_release_is_judged_more_leniently_than_a_press():
    """A release timed alongside other presses would be awkward to judge."""
    note = Note()
    note.StartTime = 0.0
    note.Column = 0

    tail_note = TailNote()
    tail_note.StartTime = 0.0
    tail_note.Column = 0

    press = note
    release = tail_note
    for note in (press, release):
        note.HitWindows = note.CreateHitWindows()
        note.HitWindows.SetDifficulty(5.0)

    assert release.MaximumJudgementOffset == pytest.approx(
        press.MaximumJudgementOffset * 1.5
    )


def test_a_hold_only_sounds_where_it_starts():
    """The default samples give the head the sound and the tail nothing."""
    hold_note = HoldNote()
    hold_note.StartTime = 0.0
    hold_note.Duration = 100.0
    hold_note.Column = 0

    held = hold_note
    held.Samples = ["a sample"]

    assert CreateDefaultNodeSamples(held) == [["a sample"], []]


def test_a_hold_body_is_never_hit_on_its_own():
    """The body carries no windows; letting go is what it judges."""
    hold_note_body = HoldNoteBody()
    hold_note_body.StartTime = 0.0
    hold_note_body.Duration = 500.0
    hold_note_body.Column = 0
    body = hold_note_body

    assert body.CreateJudgement().MaxResult == HitResult.IgnoreHit
    assert body.CreateJudgement().MinResult == HitResult.ComboBreak


def test_a_hold_itself_is_never_hit_either():
    """The hold is scored through its ends, so it earns nothing of its own."""
    hold_note = HoldNote()
    hold_note.StartTime = 0.0
    hold_note.Duration = 500.0
    hold_note.Column = 0
    held = hold_note

    assert held.CreateJudgement().MaxResult == HitResult.IgnoreHit


def test_a_mania_beatmap_keeps_the_columns_it_was_written_for():
    """Notes in a mania beatmap pass through into the column they name."""
    beatmap = convert(decode_mania(notes_in(0, 1, 2, 3), keys=4), [])

    assert beatmap.TotalColumns == 4
    assert [h.Column for h in beatmap.HitObjects] == [0, 1, 2, 3]
    assert all(isinstance(h, Note) for h in beatmap.HitObjects)


def test_a_mania_hold_passes_through_as_a_hold():
    """A hold written for mania keeps its column and its length."""
    beatmap = convert(decode_mania(hold(2, 1000, 1800, keys=4), keys=4), [])
    held = beatmap.HitObjects[0]

    assert isinstance(held, HoldNote)
    assert held.Column == 2
    assert held.StartTime == 1000
    assert held.EndTime == 1800
