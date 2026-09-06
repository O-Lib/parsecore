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

from parsecore.Rulesets.Mania.Objects.HeadNote import HeadNote
from parsecore.Rulesets.Mania.Objects.HoldNoteBody import HoldNoteBody
from parsecore.Rulesets.Mania.Objects.ManiaHitObject import ManiaHitObject
from parsecore.Rulesets.Mania.Objects.TailNote import TailNote
from parsecore.Rulesets.Scoring.EmptyHitWindows import EmptyHitWindows


class HoldNote(ManiaHitObject):
    """A note held down for a duration."""

    def __init__(
        self,
        start_time: float = 0.0,
        column: int = 0,
        duration: float = 0.0,
        play_sliding_samples: bool = False,
        node_samples: list | None = None,
    ) -> None:
        """Create a hold note.

        Args:
            start_time: When the hold begins.
            column: The column it is played in.
            duration: How long it is held for.
            play_sliding_samples: Whether the beatmap sounds it while held.
            node_samples: The samples of each end, if the beatmap gave any.
        """
        self._duration = duration
        self.Head: HeadNote | None = None
        self.Tail: TailNote | None = None
        self.Body: HoldNoteBody | None = None
        super().__init__(start_time, column)
        self.PlaySlidingSamples = play_sliding_samples
        self.NodeSamples = node_samples

    @property
    def StartTime(self) -> float:
        """Return when the hold begins."""
        return self._start_time

    @StartTime.setter
    def StartTime(self, value: float) -> None:
        """Move the hold, dragging its ends along.

        Args:
            value: The time to move it to.
        """
        self._start_time = value

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
        return self._column

    @Column.setter
    def Column(self, value: int) -> None:
        """Move the hold to another column, dragging its ends along.

        Args:
            value: The column to move it to.
        """
        self._column = value

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

        # The converter normally supplies these, but an object built by hand
        # still needs something sane to sound.
        if self.NodeSamples is None:
            self.NodeSamples = CreateDefaultNodeSamples(self)

        self.Head = HeadNote(self.StartTime, self.Column)
        self.Head.Samples = self.GetNodeSamples(0)
        self.AddNested(self.Head)

        self.Tail = TailNote(self.EndTime, self.Column)
        self.Tail.Samples = self.GetNodeSamples(len(self.NodeSamples) - 1)
        self.AddNested(self.Tail)

        self.Body = HoldNoteBody(self.StartTime, self.Column, self.Duration)
        self.AddNested(self.Body)

    def GetNodeSamples(self, node_index: int) -> list:
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


def CreateDefaultNodeSamples(hit_object) -> list:
    """Return the samples a hold note falls back on.

    An osu!mania beatmap sounds a hold only where it starts, so the tail is
    given nothing to play.

    Args:
        hit_object: The object to take the head's sound from.
    """
    return [hit_object.Samples, []]
