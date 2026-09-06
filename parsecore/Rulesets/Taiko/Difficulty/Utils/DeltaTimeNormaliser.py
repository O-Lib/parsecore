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


def Normalise(hit_objects: list, margin_of_error: float) -> dict:
    """Return each object's spacing, replaced by its neighbourhood's median.

    Spacings are collected, sorted, and split wherever the next one is further
    than the margin from the one that opened the current set. Every spacing in
    a set is then reported as that set's median.

    Args:
        hit_objects: The objects whose spacings to flatten.
        margin_of_error: How far two spacings may differ and still be one.

    Returns:
        A lookup from object to its flattened spacing.
    """
    delta_times = sorted({h.DeltaTime for h in hit_objects})

    sets: list[list[float]] = []
    current: list[float] | None = None

    for value in delta_times:
        if current is not None and abs(value - current[0]) <= margin_of_error:
            current.append(value)
            continue

        current = [value]
        sets.append(current)

    median_lookup: dict[float, float] = {}

    for group in sets:
        group.sort()
        mid = len(group) // 2
        median = (
            group[mid]
            if len(group) % 2 == 1
            else (group[mid - 1] + group[mid]) / 2
        )
        for value in group:
            median_lookup[value] = median

    return {h: median_lookup.get(h.DeltaTime, h.DeltaTime) for h in hit_objects}
