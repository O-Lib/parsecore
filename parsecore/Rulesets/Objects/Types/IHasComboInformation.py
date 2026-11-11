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

from typing import Protocol, runtime_checkable

from parsecore.Rulesets.Objects.Types.IHasCombo import IHasCombo


@runtime_checkable
class IHasComboInformation(IHasCombo, Protocol):
    """
    A HitObject that is part of a combo and has extended information
    about its position relative to other combo objects.
    """

    IndexInCurrentCombo: int
    ComboIndex: int
    ComboIndexWithOffsets: int
    LastInCombo: bool

    def UpdateComboInformation(self, last_object: IHasComboInformation | None) -> None:
        ...

def UpdateComboInformation(obj: IHasComboInformation, last_obj: IHasComboInformation | None) -> None:
    """Update combo information for a hit object based on the previous object in the sequence.

    Args:
        obj: The current hit object to update.
        last_obj: The previous hit object, if any.
    """
    index = last_obj.ComboIndex if last_obj is not None else 0
    index_with_offsets = last_obj.ComboIndexWithOffsets if last_obj is not None else 0
    in_current_combo = last_obj.IndexInCurrentCombo + 1 if last_obj is not None else 0

    if obj.NewCombo or last_obj is None:
        in_current_combo = 0
        index += 1
        index_with_offsets += obj.ComboOffset + 1

        if last_obj is not None:
            last_obj.LastInCombo = True

    obj.ComboIndex = index
    obj.ComboIndexWithOffsets = index_with_offsets
    obj.IndexInCurrentCombo = in_current_combo
