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

import pytest

from parsecore.Rulesets.Scoring import HitResult as HR
from parsecore.Rulesets.Scoring.DefaultHitWindows import DefaultHitWindows
from parsecore.Rulesets.Scoring.HitResult import HitResult


def test_windows_narrow_as_difficulty_rises():
    """A higher overall difficulty gives a tighter great window."""
    easy = DefaultHitWindows()
    easy.SetDifficulty(0)
    hard = DefaultHitWindows()
    hard.SetDifficulty(10)
    assert hard.WindowFor(HitResult.Great) < easy.WindowFor(HitResult.Great)


def test_window_at_od5_is_the_average():
    """Overall difficulty five gives exactly the middle window."""
    windows = DefaultHitWindows()
    windows.SetDifficulty(5)
    assert windows.WindowFor(HitResult.Great) == pytest.approx(49.0)


def test_result_for_offset():
    """A timing offset resolves to the judgement whose window contains it."""
    windows = DefaultHitWindows()
    windows.SetDifficulty(5)
    assert windows.ResultFor(0) == HitResult.Great
    assert windows.ResultFor(60) == HitResult.Ok
    assert windows.ResultFor(1000) == HitResult.None_


def test_disallowed_results_are_skipped():
    """The default windows never award a perfect or good judgement."""
    windows = DefaultHitWindows()
    windows.SetDifficulty(5)
    assert windows.WindowFor(HitResult.Perfect) == 0.0
    assert windows.WindowFor(HitResult.Good) == 0.0


def test_hit_result_predicates():
    """The judgement predicates agree with how osu! classifies results."""
    assert HR.IsHit(HitResult.Great)
    assert not HR.IsHit(HitResult.Miss)
    assert HR.BreaksCombo(HitResult.Miss)
    assert HR.BreaksCombo(HitResult.LargeTickMiss)
    assert not HR.BreaksCombo(HitResult.SmallTickMiss)
    assert HR.AffectsAccuracy(HitResult.Great)
    assert not HR.AffectsAccuracy(HitResult.LargeBonus)
    assert HR.IsBonus(HitResult.SmallBonus)
    assert HR.IsTick(HitResult.LargeTickHit)
    assert HR.IncreasesCombo(HitResult.Great)
    assert not HR.IncreasesCombo(HitResult.Miss)
