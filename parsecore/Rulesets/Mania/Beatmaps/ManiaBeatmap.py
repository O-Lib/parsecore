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

from parsecore.Beatmaps.Beatmap import Beatmap
from parsecore.Rulesets.Mania.Beatmaps.StageDefinition import StageDefinition


class ManiaBeatmap(Beatmap):
    """A beatmap played on one or two mania stages."""

    def __init__(self, default_stage: StageDefinition) -> None:
        """Create a mania beatmap with one stage.

        Args:
            default_stage: The stage the beatmap starts with.
        """
        super().__init__()
        self.Stages: list[StageDefinition] = [default_stage]

    @property
    def TotalColumns(self) -> int:
        """Return how many columns every stage has between them."""
        return sum(stage.Columns for stage in self.Stages)

    def GetStageForColumnIndex(self, column: int) -> StageDefinition:
        """Return the stage a column belongs to.

        Args:
            column: The column to look up, counted across all stages.

        Raises:
            IndexError: If the column is past the last stage.
        """
        for stage in self.Stages:
            if column < stage.Columns:
                return stage
            column -= stage.Columns

        raise IndexError("provided index exceeds all available stages")
