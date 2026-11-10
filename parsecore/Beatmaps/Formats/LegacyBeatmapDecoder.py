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
import re

from parsecore.Audio.HitSampleInfo import BANK_NORMAL
from parsecore.Beatmaps.Beatmap import Beatmap
from parsecore.Beatmaps.BeatmapDifficulty import BeatmapDifficulty
from parsecore.Beatmaps.ControlPoints.ControlPoint import ControlPoint
from parsecore.Beatmaps.ControlPoints.DifficultyControlPoint import DEFAULT as DP
from parsecore.Beatmaps.ControlPoints.DifficultyControlPoint import (
    DifficultyControlPoint,
)
from parsecore.Beatmaps.ControlPoints.EffectControlPoint import EffectControlPoint
from parsecore.Beatmaps.ControlPoints.SampleControlPoint import DEFAULT as SP
from parsecore.Beatmaps.ControlPoints.TimingControlPoint import TimingControlPoint
from parsecore.Beatmaps.CountdownType import CountdownType
from parsecore.Beatmaps.Formats import Parsing
from parsecore.Beatmaps.Formats.LegacyDecoder import LegacyDecoder, Section
from parsecore.Beatmaps.Legacy.LegacyControlPointInfo import (
    LegacyControlPointInfo,
    LegacySampleControlPoint,
)
from parsecore.Beatmaps.Legacy.LegacyEffectFlags import LegacyEffectFlags
from parsecore.Beatmaps.Legacy.LegacyEventType import LegacyEventType
from parsecore.Beatmaps.Legacy.LegacySampleBank import LegacySampleBank
from parsecore.Beatmaps.Timing.BreakPeriod import BreakPeriod
from parsecore.Beatmaps.Timing.TimeSignature import SIMPLE_QUADRUPLE, TimeSignature
from parsecore.Rulesets.Objects.HitObject import CONTROL_POINT_LENIENCY, HitObject
from parsecore.Rulesets.Objects.Legacy.ConvertHitObject import ConvertHitObject
from parsecore.Rulesets.Objects.Legacy.ConvertHitObjectParser import (
    ConvertHitObjectParser,
)
from parsecore.Rulesets.Objects.Types.IHasGenerateTicks import IHasGenerateTicks
from parsecore.Rulesets.Objects.Types.IHasRepeats import IHasRepeats, SpanCount
from parsecore.Rulesets.Objects.Types.IHasSliderVelocity import IHasSliderVelocity
from parsecore.Utils.Precision import Clamp

LATEST_VERSION = 14
EARLY_VERSION_TIMING_OFFSET = 24

# Mania reads circle size as a key count.
MAX_MANIA_KEY_COUNT = 18

_VERSION_RE = re.compile(r"^osu file format v(\d+)", re.IGNORECASE)


class LegacyDifficultyControlPoint(DifficultyControlPoint):
    """A difficulty point that remembers the legacy beat length it came from."""

    def __init__(self, beat_length: float = 0.0, **kwargs) -> None:
        """Create a legacy difficulty point.

        Args:
            beat_length: The raw beat length of the timing line.
            **kwargs: Passed through to :class:`DifficultyControlPoint`.
        """
        super().__init__(**kwargs)
        # A NaN beat length disables slider ticks entirely.
        self.GenerateTicks = beat_length == beat_length  # False only for NaN


class LegacyBeatmapDecoder(LegacyDecoder):
    """Decodes a legacy ``.osu`` file."""

    def __init__(self, format_version: int = LATEST_VERSION) -> None:
        """Create a decoder for a given format version.

        Args:
            format_version: The version from the file header.
        """
        super().__init__(format_version)
        self.offset = (
            EARLY_VERSION_TIMING_OFFSET if format_version < 5 else 0.0
        )
        self._beatmap: Beatmap = Beatmap()
        self._parser: ConvertHitObjectParser = ConvertHitObjectParser()
        self._default_sample_bank = LegacySampleBank.Normal
        self._default_sample_volume = 100
        self._has_approach_rate = False
        self._pending_control_points: list[ControlPoint] = []
        self._pending_control_point_types: set[type] = set()
        self._pending_control_points_time = 0.0

        self.ApplyOffsets: bool = True

    @classmethod
    def FromPath(cls, path: str) -> Beatmap:
        """Decode a beatmap from a file on disk.

        Args:
            path: The path to a ``.osu`` file.

        Returns:
            The decoded beatmap.
        """
        with open(path, encoding="utf-8-sig", errors="replace") as handle:
            return cls.FromText(handle.read())

    @classmethod
    def FromText(cls, text: str) -> Beatmap:
        """Decode a beatmap from the contents of a ``.osu`` file.

        Args:
            text: The whole file as text.

        Returns:
            The decoded beatmap.
        """
        lines = text.splitlines()

        version = LATEST_VERSION
        for line in lines:
            match = _VERSION_RE.search(line.strip())
            if match:
                version = int(match.group(1))
                break

        decoder = cls(version)
        return decoder.Decode(lines)

    def Decode(self, lines: list[str]) -> Beatmap:
        """Decode a beatmap from already-split lines.

        Args:
            lines: The file's lines, without line endings.

        Returns:
            The decoded beatmap.
        """
        output = _create_template_object()
        self.ParseStreamInto(lines, output)
        return output

    def ParseStreamInto(self, lines: list[str], output: Beatmap) -> None:
        """Parse lines from a .osu file into an existing beatmap instance.

        Args:
            lines: The file's lines without line endings.
            output: The beatmap object to populate.
        """
        self._beatmap = output
        self._beatmap.BeatmapInfo.BeatmapVersion = self.FormatVersion
        self._parser = ConvertHitObjectParser(self._get_offset_time(), self.FormatVersion)

        self._beatmap.BeatmapInfo.WidescreenStoryboard = False

        super().ParseStreamInto(lines, output)
        self._apply_difficulty_restrictions(output.Difficulty, output)

        self._flush_pending_points()
        
        self._beatmap.HitObjects = sorted(self._beatmap.HitObjects, key=lambda h: h.StartTime)

        self._post_process_breaks(self._beatmap)

        for hit_object in self._beatmap.HitObjects:
            self._apply_defaults(hit_object)
            self._apply_samples(hit_object)

    @staticmethod
    def _apply_difficulty_restrictions(difficulty: BeatmapDifficulty, beatmap: Beatmap) -> None:
        """Clamp every difficulty setting to the range osu! accepts.

        Args:
            difficulty: The difficulty settings to clamp.
            beatmap: The beatmap they belong to.
        """
        difficulty.DrainRate = Clamp(difficulty.DrainRate, 0.0, 10.0)

        if beatmap.BeatmapInfo.RulesetID != 3:
            difficulty.CircleSize = Clamp(difficulty.CircleSize, 0.0, 10.0)
        else:
            # Mania reads circle size as a key count, so it has its own range.
            difficulty.CircleSize = Clamp(difficulty.CircleSize, 1.0, MAX_MANIA_KEY_COUNT)

        difficulty.OverallDifficulty = Clamp(difficulty.OverallDifficulty, 0.0, 10.0)
        difficulty.ApproachRate = Clamp(difficulty.ApproachRate, 0.0, 10.0)
        difficulty.SliderMultiplier = Clamp(difficulty.SliderMultiplier, 0.4, 3.6)
        difficulty.SliderTickRate = Clamp(difficulty.SliderTickRate, 0.5, 8.0)

    @staticmethod
    def _post_process_breaks(beatmap: Beatmap) -> None:
        """Start a new combo on the first object after each break.

        Args:
            beatmap: The beatmap to process.
        """
        current_break = 0
        force_new_combo = False

        for hit_object in beatmap.HitObjects:
            if isinstance(hit_object, ConvertHitObject):
                while (
                    current_break < len(beatmap.Breaks)
                    and beatmap.Breaks[current_break].EndTime < hit_object.StartTime
                ):
                    force_new_combo = True
                    current_break += 1

                hit_object.NewCombo |= force_new_combo
                force_new_combo = False

    def ParseLine(self, output: Beatmap, section: Section, line: str) -> None:
        """Dispatch one line to its section handler.

        Args:
            output: The beatmap being populated.
            section: The section the line belongs to.
            line: The raw line.
        """
        match section:
            case Section.General:
                self._handle_general(line)
            case Section.Editor:
                self._handle_editor(line)
            case Section.Metadata:
                self._handle_metadata(line)
            case Section.Difficulty:
                self._handle_difficulty(line)
            case Section.Events:
                self._handle_event(line)
            case Section.TimingPoints:
                self._handle_timing_point(line)
            case Section.HitObjects:
                self._handle_hit_object(line)

        super().ParseLine(output, section, line)

    def _handle_general(self, line: str) -> None:
        """Parse one ``[General]`` line.

        Args:
            line: The raw line.
        """
        key, value = self.SplitKeyVal(self.StripComments(line))
        info = self._beatmap.BeatmapInfo
        metadata = info.Metadata

        match key:
            case "AudioFilename":
                metadata.AudioFile = value
            case "AudioLeadIn":
                info.AudioLeadIn = Parsing.ParseInt(value)
            case "PreviewTime":
                time = Parsing.ParseInt(value)
                metadata.PreviewTime = -1 if time == -1 else int(self._get_offset_time(time))
            case "SampleSet":
                self._default_sample_bank = LegacySampleBank[value]
            case "SampleVolume":
                self._default_sample_volume = Parsing.ParseInt(value)
            case "StackLeniency":
                info.StackLeniency = Parsing.ParseFloat(value)
            case "Mode":
                info.RulesetID = Parsing.ParseInt(value)
            case "LetterboxInBreaks":
                info.LetterboxInBreaks = Parsing.ParseInt(value) == 1
            case "SpecialStyle":
                info.SpecialStyle = Parsing.ParseInt(value) == 1
            case "WidescreenStoryboard":
                info.WidescreenStoryboard = Parsing.ParseInt(value) == 1
            case "EpilepsyWarning":
                info.EpilepsyWarning = Parsing.ParseInt(value) == 1
            case "SamplesMatchPlaybackRate":
                info.SamplesMatchPlaybackRate = Parsing.ParseInt(value) == 1
            case "Countdown":
                info.Countdown = CountdownType(Parsing.ParseInt(value))
            case "CountdownOffset":
                info.CountdownOffset = Parsing.ParseInt(value)

    def _handle_editor(self, line: str) -> None:
        """Parse one ``[Editor]`` line.

        Args:
            line: The raw line.
        """
        key, value = self.SplitKeyVal(self.StripComments(line))
        info = self._beatmap.BeatmapInfo

        match key:
            case "Bookmarks":
                info.Bookmarks = [
                    value_ for value_ in (
                        Parsing.TryParseInt(v) for v in value.split(",")
                    )
                    if value_ is not None
                ]
            case "VelocityPresets":
                info.SliderVelocityPresets = [
                    value_ for value_ in (
                        Parsing.TryParseDouble(v) for v in value.split(",")
                    )
                    if value_ is not None
                ]
            case "DistanceSpacing":
                info.DistanceSpacing = max(0.0, Parsing.ParseDouble(value))
            case "BeatDivisor":
                info.BeatDivisor = Parsing.ParseInt(value)
            case "GridSize":
                info.GridSize = Parsing.ParseInt(value)
            case "TimelineZoom":
                info.TimelineZoom = max(0.0, Parsing.ParseDouble(value))

    def _handle_metadata(self, line: str) -> None:
        """Parse one ``[Metadata]`` line.

        Args:
            line: The raw line.
        """
        key, value = self.SplitKeyVal(line)
        metadata = self._beatmap.BeatmapInfo.Metadata

        match key:
            case "Title":
                metadata.Title = value
            case "TitleUnicode":
                metadata.TitleUnicode = value
            case "Artist":
                metadata.Artist = value
            case "ArtistUnicode":
                metadata.ArtistUnicode = value
            case "Creator":
                metadata.Author = value
            case "Version":
                self._beatmap.BeatmapInfo.DifficultyName = value
            case "Source":
                metadata.Source = value
            case "Tags":
                metadata.Tags = value
            case "BeatmapID":
                self._beatmap.BeatmapInfo.OnlineID = Parsing.ParseInt(value)
            case "BeatmapSetID":
                self._beatmap.BeatmapInfo.BeatmapSetID = Parsing.ParseInt(value)

    def _handle_difficulty(self, line: str) -> None:
        """Parse one ``[Difficulty]`` line.

        Args:
            line: The raw line.
        """
        key, value = self.SplitKeyVal(self.StripComments(line))
        difficulty = self._beatmap.Difficulty

        match key:
            case "HPDrainRate":
                difficulty.DrainRate = Parsing.ParseFloat(value)
            case "CircleSize":
                difficulty.CircleSize = Parsing.ParseFloat(value)
            case "OverallDifficulty":
                difficulty.OverallDifficulty = Parsing.ParseFloat(value)
                if not self._has_approach_rate:
                    difficulty.ApproachRate = difficulty.OverallDifficulty
            case "ApproachRate":
                difficulty.ApproachRate = Parsing.ParseFloat(value)
                self._has_approach_rate = True
            case "SliderMultiplier":
                difficulty.SliderMultiplier = Parsing.ParseDouble(value)
            case "SliderTickRate":
                difficulty.SliderTickRate = Parsing.ParseDouble(value)

    def _handle_event(self, line: str) -> None:
        """Parse one ``[Events]`` line.

        Args:
            line: The raw line.
        """
        split = line.strip().split(",")
        if not split:
            return

        try:
            event_type = LegacyEventType(int(split[0]))
        except (ValueError, TypeError):
            # Named events (``Video``, ``Sprite``, ...) are storyboard lines.
            self._beatmap.UnhandledEventLines.append(line)
            return

        match event_type:
            case LegacyEventType.Background:
                if len(split) > 2:
                    self._beatmap.Metadata.BackgroundFile = split[2].strip('"')
            case LegacyEventType.Break:
                if len(split) > 2:
                    start = self._get_offset_time(Parsing.ParseDouble(split[1]))
                    end = max(start, self._get_offset_time(Parsing.ParseDouble(split[2])))
                    self._beatmap.Breaks.append(BreakPeriod(start, end))
            case _:
                self._beatmap.UnhandledEventLines.append(line)

    def _handle_timing_point(self, line: str) -> None:
        """Parse one ``[TimingPoints]`` line.

        Args:
            line: The raw line.
        """
        split = line.split(",")
        if len(split) < 2:
            return

        time = self._get_offset_time(Parsing.ParseDouble(split[0].strip()))
        # A NaN beat length is deliberate in some beatmaps: it is how they turn
        # slider tick generation off, so it has to survive parsing.
        beat_length = Parsing.ParseDouble(split[1].strip(), allow_nan=True)
        speed_multiplier = 100.0 / -beat_length if beat_length < 0 else 1.0

        time_signature = SIMPLE_QUADRUPLE
        if len(split) >= 3 and split[2] and not split[2].startswith("0"):
            time_signature = TimeSignature(Parsing.ParseInt(split[2]))

        sample_set = self._default_sample_bank
        if len(split) >= 4:
            try:
                sample_set = LegacySampleBank(Parsing.ParseInt(split[3]))
            except ValueError:
                pass

        custom_sample_bank = 0
        if len(split) >= 5:
            custom_sample_bank = Parsing.ParseInt(split[4])

        sample_volume = self._default_sample_volume
        if len(split) >= 6:
            sample_volume = Parsing.ParseInt(split[5])

        timing_change = True
        if len(split) >= 7:
            timing_change = split[6].startswith("1")

        kiai_mode = False
        omit_first_bar_signature = False
        if len(split) >= 8:
            try:
                effect_flags = LegacyEffectFlags(Parsing.ParseInt(split[7]))
                kiai_mode = bool(effect_flags & LegacyEffectFlags.Kiai)
                omit_first_bar_signature = bool(
                    effect_flags & LegacyEffectFlags.OmitFirstBarLine
                )
            except ValueError:
                pass

        string_sample_set = sample_set.name.lower()
        if string_sample_set == "none_":
            string_sample_set = BANK_NORMAL

        if timing_change:
            if math.isnan(beat_length):  # NaN
                return
            point = TimingControlPoint(
                BeatLength=beat_length,
                TimeSignature=time_signature,
                OmitFirstBarLine=omit_first_bar_signature,
            )
            self._add_control_point(time, point, True)

        ruleset_id = self._beatmap.BeatmapInfo.RulesetID

        difficulty_point = DifficultyControlPoint(
            GenerateTicks=not math.isnan(beat_length),
            SliderVelocity=speed_multiplier
        )
        self._add_control_point(time, difficulty_point, timing_change)

        effect_point = EffectControlPoint(KiaiMode=kiai_mode)
        # Scroll speed only applies to taiko and mania.
        if ruleset_id in (1, 3):
            effect_point.ScrollSpeed = speed_multiplier
        self._add_control_point(time, effect_point, timing_change)

        sample_point = LegacySampleControlPoint()
        sample_point.SampleBank = string_sample_set
        sample_point.SampleVolume = sample_volume
        sample_point.CustomSampleBank = custom_sample_bank
        self._add_control_point(time, sample_point, timing_change)

    def _handle_hit_object(self, line: str) -> None:
        """Parse one ``[HitObjects]`` line.

        Args:
            line: The raw line.
        """
        obj = self._parser.Parse(line)
        if obj is not None:
            obj.ApplyDefaults(self._beatmap.ControlPointInfo, self._beatmap.Difficulty)
            self._beatmap.HitObjects.append(obj)

    def _add_control_point(
        self, time: float, point: ControlPoint, timing_change: bool
    ) -> None:
        """Add a control point, buffering inherited ones until the time changes.

        Args:
            time: The point's time in milliseconds.
            point: The point to add.
            timing_change: Whether this came from an uninherited (red) line.
        """
        if time != self._pending_control_points_time:
            self._flush_pending_points()

        # A point from a red line goes to the front of the buffer rather than
        # straight into the beatmap. Only the last point of each kind at a
        # given time survives the flush, so this is what lets an inherited
        # line sitting on the same millisecond override a red one.
        if timing_change:
            self._pending_control_points.insert(0, point)
        else:
            self._pending_control_points.append(point)

        self._pending_control_points_time = time

    def _flush_pending_points(self) -> None:
        """Commit buffered points, keeping only the last of each type."""
        for point in reversed(self._pending_control_points):
            if type(point) in self._pending_control_point_types:
                continue
            self._pending_control_point_types.add(type(point))
            self._beatmap.ControlPointInfo.Add(
                self._pending_control_points_time, point
            )

        self._pending_control_points.clear()
        self._pending_control_point_types.clear()

    def _get_offset_time(self, time: float | None = None) -> float:
        """Return a time with the early-format offset applied.

        Args:
            time: The raw time from the file.
        """
        if time:
            return time + (self.offset if self.ApplyOffsets else 0)

        return self.offset if self.ApplyOffsets else 0.0

    def _apply_defaults(self, hit_object: HitObject) -> None:
        """Apply control points and difficulty to every hit object.

        Args:
            hit_object: Beatmap's hit object.
        """
        difficulty_control_point = DP
        control_point_info = self._beatmap.ControlPointInfo
        if isinstance(control_point_info, LegacyControlPointInfo):
            difficulty_control_point = control_point_info.DifficultyPointAt(hit_object.StartTime)

        if isinstance(hit_object, IHasGenerateTicks):
            hit_object.GenerateTicks = difficulty_control_point.GenerateTicks

        if isinstance(hit_object, IHasSliderVelocity):
            hit_object.SliderVelocityMultiplier = difficulty_control_point.SliderVelocity

        hit_object.ApplyDefaults(self._beatmap.ControlPointInfo, self._beatmap.Difficulty)

    def _apply_samples(self, hit_object: HitObject) -> None:
        """Fill in the bank and volume the control points give an object.

        A beatmap states an object's sounds and its banks separately: the
        object says which sounds it makes, the control points say what they
        sound like. The two are joined here.

        Args:
            hit_object: The object to complete.
        """
        sample_control_point = SP
        control_point_info = self._beatmap.ControlPointInfo
        if isinstance(hit_object, IHasRepeats):
            if isinstance(control_point_info, LegacyControlPointInfo):
                sample_control_point = control_point_info.SamplePointAt(
                    hit_object.StartTime + CONTROL_POINT_LENIENCY + 1
                )

            hit_object.Samples = [sample_control_point.ApplyTo(sp) for sp in hit_object.Samples]

            for i in range(len(hit_object.NodeSamples)):
                time = (
                        hit_object.StartTime + i * hit_object.Duration
                        / SpanCount(hit_object) + CONTROL_POINT_LENIENCY
                )
                node_sample_point = (
                    control_point_info.SamplePointAt(time)
                    if isinstance(control_point_info, LegacyControlPointInfo)
                    else SP
                )

                hit_object.NodeSamples[i] = [node_sample_point.ApplyTo(h) for h in hit_object.NodeSamples[i]]
        else:
            if isinstance(control_point_info, LegacyControlPointInfo):
                sample_control_point = control_point_info.SamplePointAt(
                    hit_object.GetEndTime() + CONTROL_POINT_LENIENCY
                )
            hit_object.Samples = [sample_control_point.ApplyTo(sp) for sp in hit_object.Samples]


def _create_template_object() -> Beatmap:
    """Return a empty template beatmap pre-configured with legacy control point info."""
    beatmap = Beatmap()
    beatmap.ControlPointInfo = LegacyControlPointInfo()
    return beatmap
