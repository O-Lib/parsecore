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

import math

from parsecore.Utils.Vector2 import f32

MAX_COORDINATE_VALUE = 131072
MAX_PARSE_VALUE = 2147483647  # int.MaxValue


class ParsingError(ValueError):
    """Raised when a beatmap value cannot be parsed or is out of range."""


def _parse(text: str, parse_limit: float, allow_nan: bool, single: bool) -> float:
    """Parse a number and check it against the bounds osu! enforces.

    Args:
        text: The raw value.
        parse_limit: The largest magnitude accepted.
        allow_nan: Whether ``NaN`` is a valid result.
        single: Whether to narrow the result to single precision first.

    Returns:
        The parsed value.

    Raises:
        ParsingError: If the value is malformed or out of range.
    """
    try:
        output = float(text)
    except (TypeError, ValueError) as exc:
        raise ParsingError(f"not a number: {text!r}") from exc

    # The narrowing comes before the bounds check, because osu! parses straight
    # into the narrower type and checks that.
    if single:
        output = f32(output)

    if output < -parse_limit:
        raise ParsingError("value is too low")
    if output > parse_limit:
        raise ParsingError("value is too high")
    if not allow_nan and math.isnan(output):
        raise ParsingError("not a number")
    return output


def ParseFloat(
    text: str, parse_limit: float = MAX_PARSE_VALUE, allow_nan: bool = False
) -> float:
    """Parse a single-precision value, rejecting out-of-range input.

    osu! parses these into a ``float``, so the value is narrowed here too.

    Args:
        text: The raw value.
        parse_limit: The largest magnitude accepted.
        allow_nan: Whether ``NaN`` is a valid result.

    Returns:
        The parsed value.

    Raises:
        ParsingError: If the value is malformed or out of range.
    """
    return _parse(text, parse_limit, allow_nan, single=True)


def ParseDouble(
    text: str, parse_limit: float = MAX_PARSE_VALUE, allow_nan: bool = False
) -> float:
    """Parse a double-precision value, rejecting out-of-range input.

    Args:
        text: The raw value.
        parse_limit: The largest magnitude accepted.
        allow_nan: Whether ``NaN`` is a valid result.

    Returns:
        The parsed value.

    Raises:
        ParsingError: If the value is malformed or out of range.
    """
    return _parse(text, parse_limit, allow_nan, single=False)


def ParseInt(text: str, parse_limit: int = MAX_PARSE_VALUE) -> int:
    """Parse an integer, rejecting out-of-range input.

    Args:
        text: The raw value.
        parse_limit: The largest magnitude accepted.

    Returns:
        The parsed value.

    Raises:
        ParsingError: If the value is malformed or out of range.
    """
    try:
        output = int(text.strip())
    except (TypeError, ValueError) as exc:
        raise ParsingError(f"not an integer: {text!r}") from exc

    if output < -parse_limit:
        raise ParsingError("value is too low")
    if output > parse_limit:
        raise ParsingError("value is too high")
    return output


def TryParseInt(text: str) -> int | None:
    """Return a value as an integer, or ``None`` if it is not one.

    Unlike :func:`ParseInt` this refuses to raise: osu! reads a few lists,
    such as the editor's bookmarks, by simply skipping whatever does not
    parse.

    Args:
        text: The raw value.
    """
    try:
        return int(text.strip())
    except (AttributeError, TypeError, ValueError):
        return None


def TryParseDouble(text: str) -> float | None:
    """Return a value as a double, or ``None`` if it is not one.

    Args:
        text: The raw value.
    """
    try:
        output = float(text.strip())
    except (AttributeError, TypeError, ValueError):
        return None

    return None if math.isnan(output) or math.isinf(output) else output
