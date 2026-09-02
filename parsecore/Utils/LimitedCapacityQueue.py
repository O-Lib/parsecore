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


class LimitedCapacityQueue:
    """A first-in first-out queue with a fixed capacity."""

    def __init__(self, capacity: int) -> None:
        """Create an empty queue.

        Args:
            capacity: How many items the queue can hold.

        Raises:
            ValueError: If the capacity is negative.
        """
        if capacity < 0:
            raise ValueError("capacity cannot be negative")

        self._capacity = capacity
        self._items: list = [None] * capacity
        self.Clear()

    def Clear(self) -> None:
        """Remove every item from the queue."""
        self._start = 0
        self._end = -1
        self.Count = 0

    @property
    def Full(self) -> bool:
        """Return whether adding another item would drop one."""
        return self.Count == self._capacity

    def Enqueue(self, item) -> None:
        """Add an item, dropping the oldest if the queue is full.

        Args:
            item: The item to add.
        """
        self._end = (self._end + 1) % self._capacity

        if self.Count == self._capacity:
            self._start = (self._start + 1) % self._capacity
        else:
            self.Count += 1

        self._items[self._end] = item

    def Dequeue(self):
        """Remove and return the oldest item.

        Raises:
            IndexError: If the queue is empty.
        """
        if self.Count == 0:
            raise IndexError("queue is empty")

        result = self._items[self._start]
        self._start = (self._start + 1) % self._capacity
        self.Count -= 1
        return result

    def __len__(self) -> int:
        """Return how many items the queue holds."""
        return self.Count

    def __getitem__(self, index: int):
        """Return an item by its place in the queue, oldest first.

        Args:
            index: The place to read, counted from the oldest.

        Raises:
            IndexError: If the index is past either end.
        """
        if index < 0:
            index += self.Count
        if index < 0 or index >= self.Count:
            raise IndexError("index out of range")

        return self._items[(self._start + index) % self._capacity]
