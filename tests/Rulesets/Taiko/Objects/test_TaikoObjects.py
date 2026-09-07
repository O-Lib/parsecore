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

from parsecore.Audio.HitSampleInfo import (
    HIT_CLAP,
    HIT_FINISH,
    HIT_NORMAL,
    FileHitSampleInfo,
    HitSampleInfo,
)
from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Beatmaps.ControlPoints.ControlPointInfo import ControlPointInfo
from parsecore.Beatmaps.ControlPoints.TimingControlPoint import TimingControlPoint
from parsecore.Rulesets.Taiko.Objects.DrumRoll import DrumRoll
from parsecore.Rulesets.Taiko.Objects.DrumRollTick import DrumRollTick
from parsecore.Rulesets.Taiko.Objects.Hit import Hit
from parsecore.Rulesets.Taiko.Objects.HitType import HitType
from parsecore.Rulesets.Taiko.Objects.StrongNestedHitObject import (
    StrongNestedHitObject,
)
from parsecore.Rulesets.Taiko.Objects.Swell import Swell
from parsecore.Rulesets.Taiko.Objects.SwellTick import SwellTick


def test_the_drum_side_comes_from_the_samples():
    """A clap or whistle makes a note a rim note; anything else is centre."""
    centre = Hit(1000.0)
    centre.Samples = [HitSampleInfo(HIT_NORMAL)]
    assert centre.Type == HitType.Centre

    rim = Hit(1000.0)
    rim.Samples = [HitSampleInfo(HIT_NORMAL), HitSampleInfo(HIT_CLAP)]
    assert rim.Type == HitType.Rim


def test_a_finish_sample_makes_a_note_strong():
    """Strength is read off the samples, and a strong note nests a second hit."""
    note = Hit(1000.0)
    note.Samples = [HitSampleInfo(HIT_NORMAL), HitSampleInfo(HIT_FINISH)]
    assert note.IsStrong

    note.ApplyDefaults(ControlPointInfo(), BeatmapDifficulty())
    assert len(note.NestedHitObjects) == 1
    assert isinstance(note.NestedHitObjects[0], StrongNestedHitObject)


def test_marking_a_note_strong_adds_the_sample():
    """Writing the flag writes a finish sample, so the two never disagree."""
    note = Hit(1000.0)
    note.Samples = [HitSampleInfo(HIT_NORMAL)]
    assert not note.IsStrong

    note.IsStrong = True

    assert note.IsStrong
    assert any(s.Name == HIT_FINISH for s in note.Samples)


def test_a_note_with_its_own_sample_file_cannot_be_made_strong():
    """A file-named sample refuses to be renamed, so the flag falls back.

    osu! adds a finish sample by copying the note's normal one and renaming it.
    A sample the beatmap named by file keeps its name through that copy, so the
    note is left without a finish sound and reads back as weak. Converted
    beatmaps rely on this: it is why simultaneous mania notes on such a map do
    not turn into strong taiko notes.
    """
    note = Hit(1000.0)
    note.Samples = [FileHitSampleInfo(Filename="normal-hitnormal.wav")]
    assert not note.IsStrong

    note.IsStrong = True

    assert not note.IsStrong, "a file sample cannot carry the finish sound"
    assert not any(s.Name == HIT_FINISH for s in note.Samples)


def test_a_drum_roll_places_a_tick_per_beat_subdivision():
    """Tick spacing follows the beat length divided by the tick rate."""
    control_points = ControlPointInfo()
    control_points.Add(0.0, TimingControlPoint(BeatLength=500.0))

    roll = DrumRoll(0.0, 1000.0)
    roll.Samples = [HitSampleInfo(HIT_NORMAL)]
    roll.ApplyDefaults(control_points, BeatmapDifficulty(SliderTickRate=1))

    assert roll.TickRate == 4
    ticks = [n for n in roll.NestedHitObjects if isinstance(n, DrumRollTick)]
    assert len(ticks) == 9
    assert ticks[0].FirstTick is True
    assert all(t.FirstTick is False for t in ticks[1:])
    assert ticks[1].StartTime - ticks[0].StartTime == pytest.approx(125.0)


def test_only_a_tick_rate_of_three_is_honoured():
    """Every tick rate other than three rolls at four ticks a beat."""
    control_points = ControlPointInfo()
    control_points.Add(0.0, TimingControlPoint(BeatLength=500.0))

    for rate, expected in [(1, 4), (2, 4), (3, 3), (4, 4)]:
        roll = DrumRoll(0.0, 500.0)
        roll.ApplyDefaults(control_points, BeatmapDifficulty(SliderTickRate=rate))
        assert roll.TickRate == expected, f"tick rate {rate}"


def test_a_swell_nests_one_tick_per_required_hit():
    """Every hit a swell asks for is its own nested object."""
    swell = Swell(0.0, 2000.0)
    swell.RequiredHits = 7
    swell.ApplyDefaults(ControlPointInfo(), BeatmapDifficulty())

    ticks = [n for n in swell.NestedHitObjects if isinstance(n, SwellTick)]
    assert len(ticks) == 7
    assert all(t.StartTime == swell.StartTime for t in ticks)
