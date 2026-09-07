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

from parsecore.Beatmaps.BeatmapConverter import BeatmapConverter
from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Beatmaps.ControlPoints.EffectControlPoint import EffectControlPoint
from parsecore.Rulesets.Objects.HitObject import HitObject
from parsecore.Rulesets.Objects.Legacy.LegacyRulesetExtensions import (
    GetPrecisionAdjustedBeatLength,
)
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
from parsecore.Rulesets.Taiko.Objects.DrumRoll import DrumRoll
from parsecore.Rulesets.Taiko.Objects.Hit import Hit
from parsecore.Rulesets.Taiko.Objects.Swell import Swell
from parsecore.Rulesets.Taiko.Objects.TaikoStrongableHitObject import (
    TaikoStrongableHitObject,
)
from parsecore.Utils.Vector2 import f32

# Taiko scrolls faster than osu! for the same slider multiplier. osu! writes
# this as a ``float``, which is a shade under 1.4.
VELOCITY_MULTIPLIER = f32(1.4)

# How many hits a swell asks for, per second, at difficulty five.
SWELL_HIT_MULTIPLIER = f32(1.65)

# The distance an osu! slider covers per beat before any multipliers.
OSU_BASE_SCORING_DISTANCE = 100.0

# Beatmaps from this format on read the tick spacing off the timing point.
FIRST_UNSCALED_TICK_VERSION = 8

TAIKO_RULESET_ID = 1
OSU_RULESET_ID = 0
MANIA_RULESET_ID = 3

# How close two scroll speeds must be before osu! treats them as unchanged.
SCROLL_SPEED_PRECISION = 0.01

# What osu! accepts as zero for a double.
ALMOST_ZERO = 1e-7


def RequiredSwellHitsPerSecond(overall_difficulty: float) -> float:
    """Return how many hits a swell asks for per second.

    Args:
        overall_difficulty: The beatmap's overall difficulty.
    """
    return (
        BeatmapDifficulty.DifficultyRange(overall_difficulty, 3.0, 5.0, 7.5)
        * SWELL_HIT_MULTIPLIER
    )


class TaikoBeatmapConverter(BeatmapConverter):
    """Turns decoded objects into taiko notes, rolls and swells."""

    def __init__(self, beatmap) -> None:
        """Create a converter for a beatmap.

        Args:
            beatmap: The decoded beatmap to convert.
        """
        super().__init__(beatmap)
        self._is_for_current_ruleset = (
            beatmap.BeatmapInfo.RulesetID == TAIKO_RULESET_ID
        )

    def CanConvert(self) -> bool:
        """Return whether taiko can play the beatmap; it always can."""
        return True

    def CreateBeatmap(self):
        """Return an empty taiko beatmap."""
        from parsecore.Rulesets.Taiko.Beatmaps.TaikoBeatmap import TaikoBeatmap

        return TaikoBeatmap()

    def ConvertBeatmap(self, original):
        """Convert the beatmap, then fix up what only the whole map shows.

        Args:
            original: A private copy of the decoded beatmap.

        Returns:
            The converted taiko beatmap.
        """
        converted = super().ConvertBeatmap(original)

        ruleset_id = original.BeatmapInfo.RulesetID

        if ruleset_id == OSU_RULESET_ID:
            self._add_scroll_speed_points(original, converted)

        if ruleset_id == MANIA_RULESET_ID:
            converted.HitObjects = _collapse_simultaneous_notes(converted.HitObjects)

        return converted

    @staticmethod
    def _add_scroll_speed_points(original, converted) -> None:
        """Turn each slider's own velocity into a scroll speed change.

        osu! stores a slider's velocity on the object; taiko has no such thing
        and reads its scroll speed from the control points, so every change has
        to become one.

        Args:
            original: The decoded beatmap.
            converted: The taiko beatmap being built.
        """
        last_scroll_speed = 1.0

        for hit_object in original.HitObjects:
            next_scroll_speed = getattr(
                hit_object, "SliderVelocityMultiplier", None
            )
            if next_scroll_speed is None:
                continue

            current = converted.ControlPointInfo.EffectPointAt(hit_object.StartTime)

            if abs(last_scroll_speed - next_scroll_speed) > SCROLL_SPEED_PRECISION:
                last_scroll_speed = next_scroll_speed
                converted.ControlPointInfo.Add(
                    hit_object.StartTime,
                    EffectControlPoint(
                        KiaiMode=current.KiaiMode, ScrollSpeed=next_scroll_speed
                    ),
                )

    def ConvertHitObject(self, original: HitObject, beatmap) -> list[HitObject]:
        """Convert one decoded object into its taiko counterpart.

        Args:
            original: The decoded object.
            beatmap: The beatmap being converted.

        Returns:
            The taiko objects it becomes, which for a slider may be several.
        """
        samples = original.Samples

        if hasattr(original, "Path"):
            return self._convert_path(original, beatmap, samples)

        if isinstance(original, IHasDuration):
            hits_per_second = RequiredSwellHitsPerSecond(
                beatmap.Difficulty.OverallDifficulty
            )
            swell = Swell(original.StartTime, original.Duration)
            swell.Samples = samples
            swell.RequiredHits = int(
                max(1.0, original.Duration / 1000 * hits_per_second)
            )
            return [swell]

        hit = Hit(original.StartTime)
        hit.Samples = samples
        return [hit]

    def _convert_path(self, original, beatmap, samples) -> list[HitObject]:
        """Convert a slider into either single notes or a drum roll.

        Args:
            original: The decoded slider.
            beatmap: The beatmap being converted.
            samples: The slider's samples.

        Returns:
            The taiko objects the slider becomes.
        """
        as_hits, taiko_duration, tick_spacing = self._should_convert_slider_to_hits(
            original, beatmap
        )

        if not as_hits:
            roll = DrumRoll(original.StartTime, taiko_duration)
            roll.Samples = samples
            return [roll]

        node_samples = getattr(original, "NodeSamples", None)
        all_samples = node_samples if node_samples else [samples]

        objects: list[HitObject] = []
        index = 0
        time = original.StartTime
        # The eighth-of-a-tick slack lets a note land on the slider's very end.
        end = original.StartTime + taiko_duration + tick_spacing / 8
        while time <= end:
            hit = Hit(time)
            hit.Samples = all_samples[index]
            objects.append(hit)

            index = (index + 1) % len(all_samples)

            # A slider with no spacing left to give yields a single note.
            if abs(tick_spacing) <= ALMOST_ZERO:
                break

            time += tick_spacing

        return objects

    def _should_convert_slider_to_hits(
        self, original, beatmap
    ) -> tuple[bool, int, float]:
        """Decide whether a slider is drummed out as single notes.

        A slider becomes notes when the player could realistically hit each
        one; otherwise it stays a roll. A beatmap written for taiko always
        keeps its rolls.

        Args:
            original: The decoded slider.
            beatmap: The beatmap being converted.

        Returns:
            Whether to emit notes, the slider's length in taiko milliseconds,
            and how far apart the notes would sit.
        """
        spans = getattr(original, "SpanCount", 1)
        expected = original.Path.ExpectedDistance
        distance = expected if expected is not None else 0.0

        distance *= VELOCITY_MULTIPLIER
        distance *= spans

        timing_point = beatmap.ControlPointInfo.TimingPointAt(original.StartTime)

        if hasattr(original, "SliderVelocityMultiplier"):
            beat_length = GetPrecisionAdjustedBeatLength(
                original, timing_point, "taiko"
            )
        else:
            beat_length = timing_point.BeatLength

        slider_scoring_point_distance = (
            OSU_BASE_SCORING_DISTANCE
            * (beatmap.Difficulty.SliderMultiplier * VELOCITY_MULTIPLIER)
            / beatmap.Difficulty.SliderTickRate
        )
        taiko_velocity = slider_scoring_point_distance * beatmap.Difficulty.SliderTickRate
        taiko_duration = int(distance / taiko_velocity * beat_length)

        if self._is_for_current_ruleset:
            return False, taiko_duration, 0.0

        osu_velocity = taiko_velocity * (1000.0 / beat_length)

        if beatmap.BeatmapInfo.BeatmapVersion >= FIRST_UNSCALED_TICK_VERSION:
            beat_length = timing_point.BeatLength

        tick_spacing = min(
            beat_length / beatmap.Difficulty.SliderTickRate,
            taiko_duration / spans,
        )
        as_hits = (
            tick_spacing > 0 and distance / osu_velocity * 1000 < 2 * beat_length
        )
        return as_hits, taiko_duration, tick_spacing


def _collapse_simultaneous_notes(hit_objects: list[HitObject]) -> list[HitObject]:
    """Keep one note per moment, marking it strong if others shared it.

    A mania beatmap can hold several notes at the same time; taiko has one
    drum, so they become a single note struck with both hands.

    Args:
        hit_objects: The converted objects, in time order.

    Returns:
        One object per distinct start time.
    """
    collapsed: list[HitObject] = []

    for hit_object in hit_objects:
        if collapsed and collapsed[-1].StartTime == hit_object.StartTime:
            first = collapsed[-1]
            if isinstance(first, TaikoStrongableHitObject):
                first.IsStrong = True
            continue
        collapsed.append(hit_object)

    return collapsed

