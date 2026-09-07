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

# How far two intervals may differ and still count as the same rhythm.
MARGIN_OF_ERROR = 5.0


def GroupByInterval(objects: list) -> list[list]:
    """Split a run of objects into groups that share a spacing.

    Args:
        objects: The objects to group, in time order.

    Returns:
        The groups, in order.
    """
    groups: list[list] = []

    index = 0
    while index < len(objects):
        group, index = _create_next_group(objects, index)
        groups.append(group)

    return groups


def _create_next_group(objects: list, index: int) -> tuple[list, int]:
    """Take objects from ``index`` for as long as their spacing holds.

    A group runs until the spacing changes. Where the spacing grows, the object
    that ends the group still belongs to it, because the gap after a note is
    what the player feels, not the gap before it.

    Args:
        objects: The objects to group.
        index: Where to start.

    Returns:
        The group, and the index the next one starts at.
    """
    grouped = [objects[index]]
    index += 1

    while index < len(objects) - 1:
        if abs(objects[index].Interval - objects[index + 1].Interval) > MARGIN_OF_ERROR:
            if objects[index + 1].Interval > objects[index].Interval + MARGIN_OF_ERROR:
                grouped.append(objects[index])
                index += 1

            return grouped, index

        grouped.append(objects[index])
        index += 1

    if (
        len(objects) > 2
        and index < len(objects)
        and abs(objects[-1].Interval - objects[-2].Interval) <= MARGIN_OF_ERROR
    ):
        grouped.append(objects[index])
        index += 1

    return grouped, index
