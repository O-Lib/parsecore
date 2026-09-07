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

from parsecore.Rulesets.Mods.ModType import ModType


class Mod:
    """Something the player switches on to change how a beatmap plays."""

    Name: str = ""
    Acronym: str = ""
    Description: str = ""
    Type: ModType = ModType.Fun
    ScoreMultiplier: float = 1.0
    Ranked: bool = False
    IncompatibleMods: tuple[str, ...] = ()

    def __eq__(self, other: object) -> bool:
        """Return whether two mods are the same mod."""
        if isinstance(other, Mod):
            return type(self) is type(other)
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash consistent with equality."""
        return hash(type(self))

    def __repr__(self) -> str:
        """Return the mod's acronym."""
        return self.Acronym or type(self).__name__
