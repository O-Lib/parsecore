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
from parsecore.Beatmaps.Legacy.LegacyHitObjectType import LegacyHitObjectType
from parsecore.Rulesets.Mania.Beatmaps.ManiaBeatmap import ManiaBeatmap
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.HitCirclePatternGenerator import (
    HitCirclePatternGenerator,
)
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.PassThroughPatternGenerator import (
    PassThroughPatternGenerator,
)
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.PatternType import PatternType
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.SliderPatternGenerator import (
    SliderPatternGenerator,
)
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Legacy.SpinnerPatternGenerator import (
    SpinnerPatternGenerator,
)
from parsecore.Rulesets.Mania.Beatmaps.Patterns.Pattern import Pattern
from parsecore.Rulesets.Mania.Beatmaps.StageDefinition import StageDefinition
from parsecore.Rulesets.Mania.Objects.ManiaHitObject import ManiaHitObject
from parsecore.Rulesets.Mods.IApplicableToBeatmapConverter import (
    IApplicableToBeatmapConverter,
)
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
from parsecore.Rulesets.Scoring.Legacy.LegacyBeatmapConversionDifficultyInfo import (
    LegacyBeatmapConversionDifficultyInfo,
)
from parsecore.Utils.LegacyRandom import LegacyRandom
from parsecore.Utils.LimitedCapacityQueue import LimitedCapacityQueue
from parsecore.Utils.Vector2 import Vector2, f32

MANIA_RULESET_ID = 3

# The widest stage osu! will put on one side of the screen.
MAX_STAGE_KEYS = 10

# How many earlier objects the density is measured over.
MAX_NOTES_FOR_DENSITY = 7

# Where a spinner is treated as sitting, for the purpose of density.
PLAYFIELD_CENTRE = Vector2(256, 192)


class ManiaBeatmapConverter(BeatmapConverter):
    """Turns a beatmap into the notes and holds mania plays."""

    def __init__(self, beatmap, difficulty=None) -> None:
        """Create a converter for a beatmap.

        Args:
            beatmap: The decoded beatmap to convert.
            difficulty: The settings to convert against, read from the beatmap
                when not given.
        """
        super().__init__(beatmap)

        if difficulty is None:
            difficulty = LegacyBeatmapConversionDifficultyInfo.FromBeatmap(beatmap)

        self.IsForCurrentRuleset = difficulty.SourceRulesetID == MANIA_RULESET_ID

        # The whole conversion is drawn from this one generator, seeded from
        # settings that osu! rounds in three different ways.
        self.Random = LegacyRandom(
            int(round(f32(f32(difficulty.DrainRate) + f32(difficulty.CircleSize)))) * 20
            + int(difficulty.OverallDifficulty * 41.2)
            + int(round(f32(difficulty.ApproachRate)))
        )

        self.TargetColumns = _get_column_count(difficulty)
        self.Dual = False

        if self.IsForCurrentRuleset and self.TargetColumns > MAX_STAGE_KEYS:
            # osu!stable never supported odd key counts above ten outside of
            # files edited by hand, so neither does this.
            self.TargetColumns //= 2
            self.Dual = True

        self._last_pattern = Pattern()
        self._previous_note_times = LimitedCapacityQueue(MAX_NOTES_FOR_DENSITY)
        self._density = float(2**31 - 1)
        self._last_time = 0.0
        self._last_position = Vector2()
        self._last_stair = PatternType.Stair

    @property
    def TotalColumns(self) -> int:
        """Return how many columns are played across every stage."""
        return self.TargetColumns * (2 if self.Dual else 1)

    def CanConvert(self) -> bool:
        """Return whether mania can play the beatmap."""
        return all(hasattr(h, "X") for h in self.Beatmap.HitObjects)

    def CreateBeatmap(self) -> ManiaBeatmap:
        """Return an empty mania beatmap with the right number of stages."""
        beatmap = ManiaBeatmap(StageDefinition(self.TargetColumns))

        if self.Dual:
            beatmap.Stages.append(StageDefinition(self.TargetColumns))

        return beatmap

    def ConvertHitObject(self, original, beatmap) -> list:
        """Convert one object into the mania objects it becomes.

        Args:
            original: The decoded object.
            beatmap: The beatmap being converted.

        Returns:
            The notes and holds this object becomes.

        Raises:
            ValueError: If the object has no legacy type mania understands.
        """
        if isinstance(original, ManiaHitObject):
            return [original]

        legacy_type = _legacy_type_of(original)

        start_time = original.StartTime
        end_time = original.EndTime if isinstance(original, IHasDuration) else start_time
        position = getattr(original, "Position", None) or Vector2()

        if legacy_type == LegacyHitObjectType.Circle:
            if self.IsForCurrentRuleset:
                conversion = PassThroughPatternGenerator(
                    self.Random, original, beatmap, self.TotalColumns, self._last_pattern
                )
                self._record_note(start_time, position)
            else:
                # The density is read while the generator is being built, so it
                # is deliberately computed first.
                self._compute_density(start_time)
                conversion = HitCirclePatternGenerator(
                    self.Random,
                    original,
                    beatmap,
                    self.TotalColumns,
                    self._last_pattern,
                    self._last_time,
                    self._last_position,
                    self._density,
                    self._last_stair,
                )
                self._record_note(start_time, position)

        elif legacy_type == LegacyHitObjectType.Slider:
            if self.IsForCurrentRuleset:
                conversion = PassThroughPatternGenerator(
                    self.Random, original, beatmap, self.TotalColumns, self._last_pattern
                )
                self._record_note(original.StartTime, position)
            else:
                conversion = SliderPatternGenerator(
                    self.Random, original, beatmap, self.TotalColumns, self._last_pattern
                )

                for i in range(conversion.SpanCount + 1):
                    time = original.StartTime + conversion.SegmentDuration * i

                    self._record_note(time, position)
                    self._compute_density(time)

        elif legacy_type == LegacyHitObjectType.Spinner:
            # Some older mania beatmaps carry spinners that are converted
            # rather than passed through; newer ones use the hold type below.
            conversion = SpinnerPatternGenerator(
                self.Random, original, beatmap, self.TotalColumns, self._last_pattern
            )
            self._record_note(end_time, PLAYFIELD_CENTRE)
            self._compute_density(end_time)

        elif legacy_type == LegacyHitObjectType.Hold:
            conversion = PassThroughPatternGenerator(
                self.Random, original, beatmap, self.TotalColumns, self._last_pattern
            )
            self._record_note(end_time, position)
            self._compute_density(end_time)

        else:
            raise ValueError(f"invalid legacy object type: {legacy_type}")

        converted = []

        for new_pattern in conversion.Generate():
            if isinstance(conversion, HitCirclePatternGenerator):
                self._last_stair = conversion.StairType

            if isinstance(
                conversion, (HitCirclePatternGenerator, SliderPatternGenerator)
            ):
                self._last_pattern = new_pattern

            converted.extend(new_pattern.HitObjects)

        return converted

    def _compute_density(self, new_note_time: float) -> None:
        """Note when an object was, and re-measure how dense the beatmap is.

        Args:
            new_note_time: When the object is.
        """
        self._previous_note_times.Enqueue(new_note_time)

        if self._previous_note_times.Count >= 2:
            self._density = (
                self._previous_note_times[-1] - self._previous_note_times[0]
            ) / self._previous_note_times.Count

    def _record_note(self, time: float, position: Vector2) -> None:
        """Note where and when the last object was.

        Args:
            time: When the object is.
            position: Where it is in the source beatmap.
        """
        self._last_time = time
        self._last_position = position


def GetColumnCount(difficulty, mods: list | None = None) -> int:
    """Return how many columns a beatmap would be converted onto.

    This answers the question without converting anything, which is what the
    score multiplier for the key mods needs.

    Args:
        difficulty: The settings the beatmap would be converted against.
        mods: The mods in effect, if any.
    """
    converter = ManiaBeatmapConverter(None, difficulty)

    for mod in mods or []:
        if isinstance(mod, IApplicableToBeatmapConverter):
            mod.ApplyToBeatmapConverter(converter)

    return converter.TotalColumns


def _legacy_type_of(original) -> LegacyHitObjectType:
    """Return which osu!stable object type an object stands in for.

    Args:
        original: The decoded object.
    """
    legacy_type = getattr(original, "LegacyType", None)
    if legacy_type is not None:
        return legacy_type & LegacyHitObjectType.ObjectTypes

    if hasattr(original, "Path"):
        return LegacyHitObjectType.Slider

    if isinstance(original, IHasDuration):
        return LegacyHitObjectType.Hold

    return LegacyHitObjectType.Circle


def _get_column_count(difficulty) -> int:
    """Return how many columns a beatmap is converted onto.

    A beatmap written for mania says so itself through its circle size.
    Anything else is guessed from how much of it is sliders and spinners: a
    beatmap that is mostly circles becomes seven keys, one that is mostly held
    objects becomes four or five.

    Args:
        difficulty: The settings of the beatmap being converted.
    """
    rounded_circle_size = round(difficulty.CircleSize)

    if difficulty.SourceRulesetID == MANIA_RULESET_ID:
        return int(max(1, rounded_circle_size))

    rounded_overall_difficulty = round(difficulty.OverallDifficulty)

    if difficulty.TotalObjectCount > 0 and difficulty.EndTimeObjectCount >= 0:
        count_slider_or_spinner = difficulty.EndTimeObjectCount

        # osu!stable appears to divide these as floats, but release-mode
        # optimisations meant it actually happened on doubles.
        percent_special_objects = (
            count_slider_or_spinner / difficulty.TotalObjectCount
        )

        if percent_special_objects < 0.2:
            return 7
        if percent_special_objects < 0.3 or rounded_circle_size >= 5:
            return 7 if rounded_overall_difficulty > 5 else 6
        if percent_special_objects > 0.6:
            return 5 if rounded_overall_difficulty > 4 else 4

    return max(4, min(int(rounded_overall_difficulty) + 1, 7))
