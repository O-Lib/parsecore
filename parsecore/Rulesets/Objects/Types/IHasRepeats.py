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

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration

if TYPE_CHECKING:
    from parsecore.Audio.HitSampleInfo import HitSampleInfo


@runtime_checkable
class IHasRepeats(IHasDuration, Protocol):
    """An object that repeats a number of times."""

    RepeatCount: int
    NodeSamples: list[list[HitSampleInfo]]
    # IHasRepeats.Samples will be used to recognize HitObject.Samples.
    Samples: list[HitSampleInfo]


def SpanCount(obj: IHasRepeats) -> int:
    """Calculate the total number of spans (repeats + 1) for a repeating object.

    Args:
        obj: The repeating object.

    Returns:
        The total span count.
    """
    return obj.RepeatCount + 1


def GetNodeSamples(obj: IHasRepeats, node_index: int) -> list[HitSampleInfo]:
    """Get the list of sample infos for a specific node index.

    Args:
        obj: The repeating object.
        node_index: The index of the node.

    Returns:
        The list of HitSampleInfo for the node, or the object's default samples if out of range.
    """
    return obj.NodeSamples[node_index] if node_index < len(obj.NodeSamples) else obj.Samples


def PopulateNodeSamples(obj: IHasRepeats) -> None:
    """Populate node samples for a repeating object if not already sufficiently populated.

    Args:
        obj: The repeating object to populate node samples for.
    """
    if len(obj.NodeSamples) >= obj.RepeatCount + 2:
        return

    while len(obj.NodeSamples) < obj.RepeatCount + 2:
        obj.NodeSamples.append([o.With() for o in obj.Samples])