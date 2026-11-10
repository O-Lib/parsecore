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
from parsecore.Rulesets.Mania.Objects.HeadNote import HeadNote
from parsecore.Rulesets.Mania.Objects.HoldNoteBody import HoldNoteBody
from parsecore.Rulesets.Mania.Objects.ManiaHitObject import ManiaHitObject
from parsecore.Rulesets.Mania.Objects.TailNote import TailNote
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows


class HoldNote(ManiaHitObject, IHasDuration):
    """A note held down for a duration."""

    def __init__(self) -> None:
        """Create a hold note."""
        super().__init__()
        self._duration = 0.0
        self.Head: HeadNote | None = None
        self.Tail: TailNote | None = None
        self.Body: HoldNoteBody | None = None
        self.PlaySlidingSamples = False
        self.NodeSamples: list[list[HitSampleInfo]] | None = None

    @property
    def StartTime(self) -> float:
        """Return when the hold begins."""
        return super().StartTime

    @StartTime.setter
    def StartTime(self, value: float) -> None:
        """Move the hold, dragging its ends along.

        Args:
            value: The time to move it to.
        """
        HitObject.StartTime.fset(self, value)

        if self.Head is not None:
            self.Head.StartTime = value
        if self.Tail is not None:
            self.Tail.StartTime = self.EndTime

    @property
    def Duration(self) -> float:
        """Return how long the hold lasts."""
        return self._duration

    @Duration.setter
    def Duration(self, value: float) -> None:
        """Resize the hold, moving its tail.

        Args:
            value: The new duration.
        """
        self._duration = value

        if self.Tail is not None:
            self.Tail.StartTime = self.EndTime

    @property
    def EndTime(self) -> float:
        """Return when the hold ends."""
        return self.StartTime + self.Duration

    @EndTime.setter
    def EndTime(self, value: float) -> None:
        """Move the end of the hold, keeping its start.

        Args:
            value: The time the hold should end.
        """
        self.Duration = value - self.StartTime

    @property
    def Column(self) -> int:
        """Return the column this hold is played in."""
        return super().Column

    @Column.setter
    def Column(self, value: int) -> None:
        """Move the hold to another column, dragging its ends along.

        Args:
            value: The column to move it to.
        """
        ManiaHitObject.Column.fset(self, value)

        if self.Head is not None:
            self.Head.Column = value
        if self.Tail is not None:
            self.Tail.Column = value

    @property
    def MaximumJudgementOffset(self) -> float:
        """Return how late this hold can still be judged, which is its tail's."""
        return self.Tail.MaximumJudgementOffset

    def CreateNestedHitObjects(self) -> None:
        """Build the head, tail and body the hold is judged through."""
        super().CreateNestedHitObjects()

        node_samples = self.NodeSamples
        # The converter normally supplies these, but an object built by hand
        # still needs something sane to sound.
        if node_samples is None:
            node_samples = CreateDefaultNodeSamples(self)

        head = HeadNote()
        head.StartTime = self.StartTime
        head.Column = self.Column
        head.Samples = self.GetNodeSamples(0)
        self.Head = head
        self.AddNested(head)

        tail = TailNote()
        tail.StartTime = self.EndTime
        tail.Column = self.Column
        tail.Samples = self.GetNodeSamples(len(node_samples) - 1)
        self.Tail = tail
        self.AddNested(tail)

        body = HoldNoteBody()
        body.StartTime = self.StartTime
        body.Column = self.Column
        body.Duration = self.Duration
        self.Body = body
        self.AddNested(body)

    def GetNodeSamples(self, node_index: int) -> list[HitSampleInfo]:
        """Return the samples of one end of the hold.

        Args:
            node_index: Which end to read, counted from the head.
        """
        if self.NodeSamples is not None and node_index < len(self.NodeSamples):
            return self.NodeSamples[node_index]
        return self.Samples

    def CreateHitWindows(self):
        """Return no windows; a hold is judged through its head and tail."""
        return EmptyHitWindows()

    def CreateJudgement(self):
        """Return the judgement this object is scored with."""
        from parsecore.Rulesets.Judgements.IgnoreJudgement import IgnoreJudgement

        return IgnoreJudgement()


def CreateDefaultNodeSamples(hit_object: HitObject) -> list[list[HitSampleInfo]]:
    """Return the samples a hold note falls back on.

    An osu!mania beatmap sounds a hold only where it starts, so the tail is
    given nothing to play.

    Args:
        hit_object: The object to take the head's sound from.
    """
    return [hit_object.Samples, []]
