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

from parsecore.Rulesets.Difficulty.Utils import DiffUtils
from parsecore.Rulesets.Osu.Objects.Spinner import Spinner

# Streams faster than 200 BPM (1/4) start earning a bonus.
MIN_SPEED_BONUS = 200.0
SPEED_BALANCING_FACTOR = 40.0

# Derived so 260 BPM OD8 streams are not nerfed harshly, while still limiting
# the effect of capping delta time to the hit window.
HIT_WINDOW_CAP_FACTOR = 0.93
HIT_WINDOW_CAP_MIN = 0.92


def EvaluateDifficultyOf(current) -> float:
    """Return how hard ``current`` is to tap.

    Args:
        current: The object being evaluated.

    Returns:
        The tapping difficulty of this object.
    """
    if isinstance(current.BaseObject, Spinner):
        return 0.0

    osu_curr_obj = current

    strain_time = osu_curr_obj.AdjustedDeltaTime

    double_tap_feasibility = 1.0 - osu_curr_obj.CalculateDoubleTapFeasibility(
        osu_curr_obj.Next()
    )

    # Delta time is capped at the great hit window: past that point, tapping
    # faster no longer helps, because the window itself is the limit.
    if osu_curr_obj.HitWindowGreat:
        strain_time /= min(
            max(
                (strain_time / osu_curr_obj.HitWindowGreat) / HIT_WINDOW_CAP_FACTOR,
                HIT_WINDOW_CAP_MIN,
            ),
            1.0,
        )

    speed_bonus = 0.0
    if DiffUtils.MillisecondsToBPM(strain_time) > MIN_SPEED_BONUS:
        speed_bonus = 0.75 * DiffUtils.Pow(
            (DiffUtils.BPMToMilliseconds(MIN_SPEED_BONUS) - strain_time)
            / SPEED_BALANCING_FACTOR,
            2,
        )

    speed_difficulty = (1 + speed_bonus) * 1000 / strain_time
    speed_difficulty *= _high_bpm_bonus(osu_curr_obj.AdjustedDeltaTime)

    return speed_difficulty * double_tap_feasibility


def _high_bpm_bonus(ms: float) -> float:
    """Return the bonus applied because fast rhythms leave no recovery time.

    Args:
        ms: The time available for the tap, in milliseconds.
    """
    return 1 / (1 - DiffUtils.Pow(0.3, ms / 1000))
