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

# How deep the quicksort may recurse before it falls back to a heapsort.
QUICK_SORT_DEPTH_THRESHOLD = 32


def Sort(keys: list, comparer) -> None:
    """Sort a list in place, exactly the way osu! does.

    Args:
        keys: The list to sort.
        comparer: Returns a negative number, zero or a positive number for a
            pair of items in the way ``cmp`` did.
    """
    if not keys:
        return

    _depth_limited_quick_sort(
        keys, 0, len(keys) - 1, comparer, QUICK_SORT_DEPTH_THRESHOLD
    )


def _depth_limited_quick_sort(
    keys: list, left: int, right: int, comparer, depth_limit: int
) -> None:
    """Sort one stretch of the list, falling back once it recurses too deep.

    Args:
        keys: The list being sorted.
        left: The first index of the stretch.
        right: The last index of the stretch.
        comparer: How to order two items.
        depth_limit: How much further the quicksort may recurse.
    """
    while True:
        if depth_limit == 0:
            _heapsort(keys, left, right, comparer)
            return

        i = left
        j = right

        # Pre-sorting the low, middle and high values keeps this fast on data
        # that is already sorted, or made of sorted runs stuck together.
        middle = i + ((j - i) >> 1)
        _swap_if_greater(keys, comparer, i, middle)
        _swap_if_greater(keys, comparer, i, j)
        _swap_if_greater(keys, comparer, middle, j)

        x = keys[middle]

        while True:
            while comparer(keys[i], x) < 0:
                i += 1
            while comparer(x, keys[j]) < 0:
                j -= 1

            if i > j:
                break

            if i < j:
                keys[i], keys[j] = keys[j], keys[i]

            i += 1
            j -= 1

            if i > j:
                break

        # The loop below sorts the larger half, so the limit is lowered here
        # for both that and the recursive call on the smaller half.
        depth_limit -= 1

        if j - left <= right - i:
            if left < j:
                _depth_limited_quick_sort(keys, left, j, comparer, depth_limit)
            left = i
        else:
            if i < right:
                _depth_limited_quick_sort(keys, i, right, comparer, depth_limit)
            right = j

        if left >= right:
            return


def _heapsort(keys: list, lo: int, hi: int, comparer) -> None:
    """Sort one stretch of the list as a heap.

    Args:
        keys: The list being sorted.
        lo: The first index of the stretch.
        hi: The last index of the stretch.
        comparer: How to order two items.
    """
    n = hi - lo + 1

    for i in range(n // 2, 0, -1):
        _down_heap(keys, i, n, lo, comparer)

    for i in range(n, 1, -1):
        _swap(keys, lo, lo + i - 1)
        _down_heap(keys, 1, i - 1, lo, comparer)


def _down_heap(keys: list, i: int, n: int, lo: int, comparer) -> None:
    """Push one item down the heap until it sits below its children.

    Args:
        keys: The list being sorted.
        i: The one-based place in the heap to push down from.
        n: How many items the heap holds.
        lo: Where the heap starts in the list.
        comparer: How to order two items.
    """
    d = keys[lo + i - 1]

    while i <= n // 2:
        child = 2 * i

        if child < n and comparer(keys[lo + child - 1], keys[lo + child]) < 0:
            child += 1

        if not comparer(d, keys[lo + child - 1]) < 0:
            break

        keys[lo + i - 1] = keys[lo + child - 1]
        i = child

    keys[lo + i - 1] = d


def _swap(items: list, i: int, j: int) -> None:
    """Exchange two items.

    Args:
        items: The list being sorted.
        i: The first index.
        j: The second index.
    """
    if i != j:
        items[i], items[j] = items[j], items[i]


def _swap_if_greater(keys: list, comparer, a: int, b: int) -> None:
    """Exchange two items if the first sorts after the second.

    Args:
        keys: The list being sorted.
        comparer: How to order two items.
        a: The index that should hold the smaller item.
        b: The index that should hold the larger.
    """
    if a != b and comparer(keys[a], keys[b]) > 0:
        keys[a], keys[b] = keys[b], keys[a]
