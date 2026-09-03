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

from enum import Enum


class Section(Enum):
    """A ``[Section]`` of a legacy beatmap file."""

    None_ = "None"
    General = "General"
    Editor = "Editor"
    Metadata = "Metadata"
    Difficulty = "Difficulty"
    Events = "Events"
    TimingPoints = "TimingPoints"
    Colours = "Colours"
    HitObjects = "HitObjects"
    Variables = "Variables"
    Fonts = "Fonts"
    CatchTheBeat = "CatchTheBeat"
    Mania = "Mania"


class LegacyDecoder:
    """Walks a legacy file line by line, dispatching each to its section."""

    def __init__(self, format_version: int) -> None:
        """Create a decoder for a given file format version.

        Args:
            format_version: The version from the ``osu file format v..`` header.
        """
        self.FormatVersion = format_version

    def ParseStreamInto(self, lines: list[str], output) -> None:
        """Parse every line of a file into ``output``.

        Args:
            lines: The file's lines, without line endings.
            output: The object being populated.
        """
        section = Section.General

        for line in lines:
            if self.ShouldSkipLine(line):
                continue

            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                name = stripped[1:-1]
                try:
                    section = Section(name)
                except ValueError:
                    section = Section.None_
                self.OnBeginNewSection(section)
                continue

            try:
                self.ParseLine(output, section, line)
            except Exception:
                # A single malformed line never invalidates the whole beatmap.
                continue

    def ShouldSkipLine(self, line: str) -> bool:
        """Return whether a line carries no data.

        Args:
            line: The raw line.
        """
        return not line.strip() or line.lstrip().startswith("//")

    def OnBeginNewSection(self, section: Section) -> None:
        """React to entering a new section.

        Args:
            section: The section just entered.
        """

    def ParseLine(self, output, section: Section, line: str) -> None:
        """Handle one line of a section.

        Args:
            output: The object being populated.
            section: The section the line belongs to.
            line: The raw line.
        """

    @staticmethod
    def StripComments(line: str) -> str:
        """Return the line with any trailing ``//`` comment removed.

        Args:
            line: The raw line.
        """
        index = line.find("//")
        if index > 0:
            return line[:index]
        return line

    @staticmethod
    def SplitKeyVal(line: str, separator: str = ":") -> tuple[str, str]:
        """Split a ``key: value`` line.

        Args:
            line: The raw line.
            separator: The character separating key from value.

        Returns:
            The key and value, both stripped of surrounding whitespace.
        """
        split = line.split(separator, 1)
        key = split[0].strip()
        value = split[1].strip() if len(split) > 1 else ""
        return key, value
