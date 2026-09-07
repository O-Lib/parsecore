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

from enum import IntEnum


class HitResult(IntEnum):
    """The outcome of a judgement."""

    None_ = 0
    Miss = 1
    Meh = 2
    Ok = 3
    Good = 4
    Great = 5
    Perfect = 6

    SmallTickMiss = 7
    SmallTickHit = 8
    LargeTickMiss = 9
    LargeTickHit = 10

    SmallBonus = 11
    LargeBonus = 12

    IgnoreMiss = 13
    IgnoreHit = 14

    ComboBreak = 15
    SliderTailHit = 16

    LegacyComboIncrease = 99


def IsHit(result: HitResult) -> bool:
    """Return whether a result counts as a successful hit.

    Args:
        result: The result to test.
    """
    match result:
        case HitResult.None_ | HitResult.IgnoreMiss | HitResult.Miss:
            return False
        case HitResult.SmallTickMiss | HitResult.LargeTickMiss | HitResult.ComboBreak:
            return False
        case _:
            return True


def IsScorable(result: HitResult) -> bool:
    """Return whether a result contributes to the score.

    Args:
        result: The result to test.
    """
    if result == HitResult.LegacyComboIncrease:
        return True
    if result == HitResult.ComboBreak:
        return True
    if result == HitResult.SliderTailHit:
        return True
    return HitResult.Miss <= result < HitResult.IgnoreMiss


def IsBonus(result: HitResult) -> bool:
    """Return whether a result is a bonus judgement.

    Args:
        result: The result to test.
    """
    return result in (HitResult.SmallBonus, HitResult.LargeBonus)


def IsBasic(result: HitResult) -> bool:
    """Return whether a result comes from a normal (non-tick) object.

    Args:
        result: The result to test.
    """
    return IsScorable(result) and not IsTick(result) and not IsBonus(result)


def IsTick(result: HitResult) -> bool:
    """Return whether a result comes from a tick object.

    Args:
        result: The result to test.
    """
    return result in (
        HitResult.LargeTickHit,
        HitResult.LargeTickMiss,
        HitResult.SmallTickHit,
        HitResult.SmallTickMiss,
        HitResult.SliderTailHit,
    )


def AffectsCombo(result: HitResult) -> bool:
    """Return whether a result increases or breaks combo.

    Args:
        result: The result to test.
    """
    if result in (
        HitResult.Miss,
        HitResult.Meh,
        HitResult.Ok,
        HitResult.Good,
        HitResult.Great,
        HitResult.Perfect,
        HitResult.LargeTickHit,
        HitResult.LargeTickMiss,
        HitResult.LegacyComboIncrease,
        HitResult.ComboBreak,
        HitResult.SliderTailHit,
    ):
        return True
    return False


def AffectsAccuracy(result: HitResult) -> bool:
    """Return whether a result is counted in the accuracy calculation.

    Args:
        result: The result to test.
    """
    if result in (HitResult.LegacyComboIncrease, HitResult.ComboBreak):
        return False
    return IsScorable(result) and not IsBonus(result)


def BreaksCombo(result: HitResult) -> bool:
    """Return whether a result resets the combo to zero.

    Args:
        result: The result to test.
    """
    if result in (
        HitResult.Miss,
        HitResult.LargeTickMiss,
        HitResult.ComboBreak,
    ):
        return True
    return False


def IncreasesCombo(result: HitResult) -> bool:
    """Return whether a result adds one to the combo.

    Args:
        result: The result to test.
    """
    return AffectsCombo(result) and IsHit(result)
