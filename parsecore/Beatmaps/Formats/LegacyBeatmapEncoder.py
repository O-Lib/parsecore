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

import io
import math

from parsecore.Audio.HitSampleInfo import (
    BANK_DRUM,
    BANK_NORMAL,
    BANK_SOFT,
    HIT_CLAP,
    HIT_FINISH,
    HIT_NORMAL,
    HIT_WHISTLE,
    FileHitSampleInfo,
)
from parsecore.Beatmaps.ControlPoints.DifficultyControlPoint import (
    DifficultyControlPoint,
)
from parsecore.Beatmaps.ControlPoints.SampleControlPoint import SampleControlPoint
from parsecore.Beatmaps.ControlPoints.TimingControlPoint import TimingControlPoint
from parsecore.Beatmaps.Legacy.LegacyControlPointInfo import LegacyControlPointInfo
from parsecore.Beatmaps.Legacy.LegacyEffectFlags import LegacyEffectFlags
from parsecore.Beatmaps.Legacy.LegacyEventType import LegacyEventType
from parsecore.Beatmaps.Legacy.LegacyHitObjectType import LegacyHitObjectType
from parsecore.Beatmaps.Legacy.LegacyHitSoundType import LegacyHitSoundType
from parsecore.Beatmaps.Legacy.LegacySampleBank import LegacySampleBank
from parsecore.Rulesets.Objects.HitObject import CONTROL_POINT_LENIENCY
from parsecore.Rulesets.Objects.Legacy.ConvertHitObjectParser import (
    LegacyHitSampleInfo,
)
from parsecore.Rulesets.Objects.Types.IHasDuration import IHasDuration
from parsecore.Rulesets.Objects.Types.PathType import SplineType
from parsecore.Utils.Vector2 import Vector2, f32

# The format version osu!lazer writes. Anything at or above this is a file
# osu!stable was never meant to read.
FIRST_LAZER_VERSION = 128

# Where an object sits when the ruleset has no positions of its own.
DEFAULT_POSITION = Vector2(256, 192)

# How many combo colours a beatmap may name.
MAX_COMBO_COLOUR_COUNT = 8


class LegacyBeatmapEncoder:
    """Turns a beatmap back into the text a ``.osu`` file holds."""

    def __init__(self, beatmap) -> None:
        """Create an encoder for a beatmap.

        Args:
            beatmap: The beatmap to write out.

        Raises:
            ValueError: If the beatmap belongs to no legacy ruleset.
        """
        self.Beatmap = beatmap
        self._online_ruleset_id = beatmap.BeatmapInfo.RulesetID

        if not 0 <= self._online_ruleset_id <= 3:
            raise ValueError(
                "only beatmaps in the osu, taiko, catch or mania rulesets can be "
                "written to the legacy beatmap format"
            )

    def Encode(self, writer) -> None:
        """Write the whole beatmap.

        Args:
            writer: The text stream to write to.
        """
        _write_line(writer, f"osu file format v{FIRST_LAZER_VERSION}")

        for section in (
            self._handle_general,
            self._handle_editor,
            self._handle_metadata,
            self._handle_difficulty,
            self._handle_events,
            self._handle_control_points,
            self._handle_colours,
            self._handle_hit_objects,
        ):
            _write_line(writer, "")
            section(writer)

    def EncodeToString(self) -> str:
        """Return the whole beatmap as one string."""
        writer = io.StringIO()
        self.Encode(writer)
        return writer.getvalue()

    def _handle_general(self, writer) -> None:
        """Write the general section.

        Args:
            writer: The text stream to write to.
        """
        beatmap = self.Beatmap
        info = beatmap.BeatmapInfo
        metadata = beatmap.Metadata

        _write_line(writer, "[General]")

        if metadata.AudioFile:
            _write_line(writer, f"AudioFilename: {_file_name(metadata.AudioFile)}")
        _write_line(writer, f"AudioLeadIn: {_num(info.AudioLeadIn)}")
        _write_line(writer, f"PreviewTime: {_num(metadata.PreviewTime)}")
        _write_line(writer, f"Countdown: {int(info.Countdown)}")

        sample_points = getattr(beatmap.ControlPointInfo, "SamplePoints", None)
        first_sample = (
            sample_points[0] if sample_points else SampleControlPoint()
        )
        _write_line(
            writer, f"SampleSet: {_to_legacy_sample_bank(first_sample.SampleBank).name}"
        )
        _write_line(writer, f"StackLeniency: {_num_f32(info.StackLeniency)}")
        _write_line(writer, f"Mode: {self._online_ruleset_id}")
        _write_line(writer, f"LetterboxInBreaks: {_flag(info.LetterboxInBreaks)}")

        if info.EpilepsyWarning:
            _write_line(writer, "EpilepsyWarning: 1")
        if info.CountdownOffset > 0:
            _write_line(writer, f"CountdownOffset: {_num(info.CountdownOffset)}")
        if self._online_ruleset_id == 3:
            _write_line(writer, f"SpecialStyle: {_flag(info.SpecialStyle)}")

        _write_line(
            writer, f"WidescreenStoryboard: {_flag(info.WidescreenStoryboard)}"
        )

        if info.SamplesMatchPlaybackRate:
            _write_line(writer, "SamplesMatchPlaybackRate: 1")

    def _handle_editor(self, writer) -> None:
        """Write the editor section.

        Args:
            writer: The text stream to write to.
        """
        info = self.Beatmap.BeatmapInfo

        _write_line(writer, "[Editor]")

        if info.Bookmarks:
            _write_line(
                writer, "Bookmarks: " + ",".join(_num(b) for b in info.Bookmarks)
            )
        _write_line(writer, f"DistanceSpacing: {_num(info.DistanceSpacing)}")
        _write_line(writer, f"BeatDivisor: {_num(info.BeatDivisor)}")
        _write_line(writer, f"GridSize: {_num(info.GridSize)}")
        _write_line(writer, f"TimelineZoom: {_num(info.TimelineZoom)}")
        _write_line(
            writer,
            "VelocityPresets: "
            + ",".join(_num(v) for v in info.SliderVelocityPresets),
        )

    def _handle_metadata(self, writer) -> None:
        """Write the metadata section.

        Args:
            writer: The text stream to write to.
        """
        info = self.Beatmap.BeatmapInfo
        metadata = self.Beatmap.Metadata

        _write_line(writer, "[Metadata]")

        _write_line(writer, f"Title: {metadata.Title}")
        if metadata.TitleUnicode:
            _write_line(writer, f"TitleUnicode: {metadata.TitleUnicode}")
        _write_line(writer, f"Artist: {metadata.Artist}")
        if metadata.ArtistUnicode:
            _write_line(writer, f"ArtistUnicode: {metadata.ArtistUnicode}")
        _write_line(writer, f"Creator: {metadata.Author}")
        _write_line(writer, f"Version: {info.DifficultyName}")
        if metadata.Source:
            _write_line(writer, f"Source: {metadata.Source}")
        if metadata.Tags:
            _write_line(writer, f"Tags: {metadata.Tags}")
        if info.OnlineID > 0:
            _write_line(writer, f"BeatmapID: {info.OnlineID}")
        if info.BeatmapSetID > 0:
            _write_line(writer, f"BeatmapSetID: {info.BeatmapSetID}")

    def _handle_difficulty(self, writer) -> None:
        """Write the difficulty section.

        Args:
            writer: The text stream to write to.
        """
        difficulty = self.Beatmap.Difficulty

        _write_line(writer, "[Difficulty]")

        _write_line(writer, f"HPDrainRate: {_num_f32(difficulty.DrainRate)}")
        _write_line(writer, f"CircleSize: {_num_f32(difficulty.CircleSize)}")
        _write_line(
            writer, f"OverallDifficulty: {_num_f32(difficulty.OverallDifficulty)}"
        )
        _write_line(writer, f"ApproachRate: {_num_f32(difficulty.ApproachRate)}")
        _write_line(writer, f"SliderMultiplier: {_num(difficulty.SliderMultiplier)}")
        _write_line(writer, f"SliderTickRate: {_num(difficulty.SliderTickRate)}")

    def _handle_events(self, writer) -> None:
        """Write the events section.

        Args:
            writer: The text stream to write to.
        """
        _write_line(writer, "[Events]")

        background = self.Beatmap.Metadata.BackgroundFile
        if background:
            _write_line(
                writer, f'{int(LegacyEventType.Background)},0,"{background}",0,0'
            )

        _write_line(writer, "// Break Periods")
        for break_period in self.Beatmap.Breaks:
            _write_line(
                writer,
                f"{int(LegacyEventType.Break)},"
                f"{_num(break_period.StartTime)},{_num(break_period.EndTime)}",
            )

    def _handle_colours(self, writer) -> None:
        """Write the combo colours, if the beatmap names any.

        Args:
            writer: The text stream to write to.
        """
        colours = getattr(self.Beatmap, "ComboColours", None)

        if not colours:
            return

        _write_line(writer, "[Colours]")

        for index, colour in enumerate(colours[:MAX_COMBO_COLOUR_COUNT]):
            _write_line(
                writer,
                f"Combo{1 + index}: {colour.R},{colour.G},{colour.B},{colour.A}",
            )

    def _handle_hit_objects(self, writer) -> None:
        """Write every hit object.

        Args:
            writer: The text stream to write to.
        """
        _write_line(writer, "[HitObjects]")

        for hit_object in self.Beatmap.HitObjects:
            self._handle_hit_object(writer, hit_object)

    def _handle_control_points(self, writer) -> None:
        """Write the timing section.

        Sample banks and slider velocities live on the objects in osu! and in
        control points in the file, so they are pulled back out of the objects
        first and added as the points that would produce them again.

        Args:
            writer: The text stream to write to.
        """
        legacy_points = LegacyControlPointInfo()
        for point in self.Beatmap.ControlPointInfo.AllControlPoints:
            legacy_points.Add(point.Time, point.DeepClone())

        _write_line(writer, "[TimingPoints]")

        # In taiko and mania a scroll speed is written as a slider velocity, so
        # it becomes a beatmap-wide effect and the objects' own difficulty
        # points are ignored.
        scroll_speed_as_slider_velocity = self._online_ruleset_id in (1, 3)

        self._extract_difficulty_control_points(
            legacy_points, scroll_speed_as_slider_velocity
        )
        self._extract_sample_control_points(legacy_points)

        if scroll_speed_as_slider_velocity:
            for point in list(legacy_points.EffectPoints):
                legacy_points.Add(
                    point.Time,
                    DifficultyControlPoint(SliderVelocity=point.ScrollSpeed),
                )

        last_properties = _ControlPointProperties()

        for group in legacy_points.Groups:
            group_timing_point = next(
                (p for p in group.ControlPoints if isinstance(p, TimingControlPoint)),
                None,
            )
            properties = self._properties_for(
                legacy_points, group.Time, group_timing_point is not None, last_properties
            )

            # A group with a timing point in it needs a line of its own.
            if group_timing_point is not None:
                writer.write(
                    f"{_num(group_timing_point.Time)},"
                    f"{_num(group_timing_point.BeatLength)},"
                )

                timing_properties = properties.copy()

                # A timing point cannot carry a slider velocity, because the
                # format writes that as a negative beat length. Leaving it at
                # one keeps any real velocity from being dropped as redundant
                # by the check further down.
                timing_properties.SliderVelocity = 1.0

                # Kiai cannot be set on a beatmap's first timing point, so it
                # is never written on one; where it is needed an inherited
                # point is emitted below anyway.
                timing_properties.EffectFlags &= ~LegacyEffectFlags.Kiai

                _output_control_point(writer, timing_properties, True)
                last_properties = timing_properties

            if properties.IsRedundant(last_properties):
                continue

            # Whatever is left becomes an inherited point.
            writer.write(f"{_num(group.Time)},")
            writer.write(f"{_num(-100 / properties.SliderVelocity)},")
            _output_control_point(writer, properties, False)
            last_properties = properties

    def _properties_for(
        self, legacy_points, time: float, update_sample_bank: bool, last
    ) -> _ControlPointProperties:
        """Return the file's view of the control points at one moment.

        Args:
            legacy_points: Every control point, including the extracted ones.
            time: The moment to read at.
            update_sample_bank: Whether this group may change the sample bank.
            last: The properties written for the group before this one.
        """
        timing_point = legacy_points.TimingPointAt(time)
        difficulty_point = legacy_points.DifficultyPointAt(time)
        sample_point = legacy_points.SamplePointAt(time)
        effect_point = legacy_points.EffectPointAt(time)

        # Running a sample through the point uncovers what the file stored,
        # such as the custom bank index.
        temp_sample = sample_point.ApplyTo(LegacyHitSampleInfo(Name=""))
        custom_sample_bank = _to_legacy_custom_sample_bank(temp_sample)

        effect_flags = LegacyEffectFlags.None_
        if effect_point.KiaiMode:
            effect_flags |= LegacyEffectFlags.Kiai
        if timing_point.OmitFirstBarLine:
            effect_flags |= LegacyEffectFlags.OmitFirstBarLine

        return _ControlPointProperties(
            SliderVelocity=difficulty_point.SliderVelocity,
            TimingSignature=timing_point.TimeSignature.Numerator,
            SampleBank=(
                int(_to_legacy_sample_bank(temp_sample.Bank))
                if update_sample_bank
                else last.SampleBank
            ),
            # An unset custom bank keeps whatever the last group had.
            CustomSampleBank=(
                custom_sample_bank
                if custom_sample_bank >= 0
                else last.CustomSampleBank
            ),
            SampleVolume=temp_sample.Volume,
            EffectFlags=effect_flags,
        )

    def _extract_difficulty_control_points(
        self, legacy_points, scroll_speed_as_slider_velocity: bool
    ) -> None:
        """Add the slider velocities the objects carry as control points.

        Args:
            legacy_points: The points being built up.
            scroll_speed_as_slider_velocity: Whether the ruleset writes its
                scroll speed as a slider velocity, in which case the objects'
                own velocities are ignored.
        """
        if scroll_speed_as_slider_velocity:
            return

        collected = [
            DifficultyControlPoint(
                Time=h.StartTime, SliderVelocity=h.SliderVelocityMultiplier
            )
            for h in self.Beatmap.HitObjects
            if hasattr(h, "SliderVelocityMultiplier")
        ]

        last_relevant = None
        for point in sorted(collected, key=lambda p: p.Time):
            if last_relevant is None or not point.IsRedundant(last_relevant):
                legacy_points.Add(point.Time, point)
                last_relevant = point

    def _extract_sample_control_points(self, legacy_points) -> None:
        """Add the sample banks the objects carry as control points.

        Args:
            legacy_points: The points being built up.
        """
        collected = list(self._collect_sample_control_points(self.Beatmap.HitObjects))

        last_relevant = None
        for point in sorted(collected, key=lambda p: p.Time):
            if last_relevant is None or not point.IsRedundant(last_relevant):
                legacy_points.Add(point.Time, point)
                last_relevant = point

    def _collect_sample_control_points(self, hit_objects):
        """Yield a sample point for every sound the objects make.

        Args:
            hit_objects: The objects to walk, nested ones included.
        """
        for hit_object in hit_objects:
            node_samples = getattr(hit_object, "NodeSamples", None)

            if node_samples is not None and hasattr(hit_object, "SpanCount"):
                span_duration = hit_object.Duration / hit_object.SpanCount

                for i, samples in enumerate(node_samples):
                    node_time = hit_object.StartTime + i * span_duration

                    if samples:
                        yield _sample_point_for(node_time, samples)

                    if (
                        span_duration > CONTROL_POINT_LENIENCY + 1
                        and hit_object.Samples
                        and i < len(node_samples) - 1
                    ):
                        yield _sample_point_for(
                            node_time + CONTROL_POINT_LENIENCY + 1, hit_object.Samples
                        )
            elif hit_object.Samples:
                yield _sample_point_for(hit_object.GetEndTime(), hit_object.Samples)

            yield from self._collect_sample_control_points(
                hit_object.NestedHitObjects
            )

    def _handle_hit_object(self, writer, hit_object) -> None:
        """Write one hit object.

        Args:
            writer: The text stream to write to.
            hit_object: The object to write.
        """
        position = DEFAULT_POSITION

        if self._online_ruleset_id in (0, 2):
            position = Vector2(hit_object.X, hit_object.Y)
        elif self._online_ruleset_id == 3:
            total_columns = int(max(1, self.Beatmap.Difficulty.CircleSize))
            position = Vector2(
                int(math.floor((hit_object.X + 0.5) * (512.0 / total_columns))),
                position.Y,
            )

        writer.write(f"{_num(position.X)},")
        writer.write(f"{_num(position.Y)},")
        writer.write(f"{_num(hit_object.StartTime)},")
        writer.write(f"{int(self._object_type(hit_object))},")
        writer.write(f"{int(_to_legacy_hit_sound_type(hit_object.Samples))},")

        if hasattr(hit_object, "Path"):
            self._add_path_data(writer, hit_object, position)
            writer.write(self._sample_bank(hit_object.Samples))
        else:
            if isinstance(hit_object, IHasDuration):
                self._add_end_time_data(writer, hit_object)

            writer.write(self._sample_bank(hit_object.Samples))

        _write_line(writer, "")

    def _object_type(self, hit_object) -> int:
        """Return the type flags one object is written with.

        Args:
            hit_object: The object to classify.
        """
        object_type = LegacyHitObjectType(getattr(hit_object, "ComboOffset", 0) << 4)

        if getattr(hit_object, "NewCombo", False):
            object_type |= LegacyHitObjectType.NewCombo

        if hasattr(hit_object, "Path"):
            object_type |= LegacyHitObjectType.Slider
        elif isinstance(hit_object, IHasDuration):
            object_type |= (
                LegacyHitObjectType.Hold
                if self._online_ruleset_id == 3
                else LegacyHitObjectType.Spinner
            )
        else:
            object_type |= LegacyHitObjectType.Circle

        return object_type

    def _add_path_data(self, writer, hit_object, position: Vector2) -> None:
        """Write a slider's path, repeats and per-node sounds.

        Args:
            writer: The text stream to write to.
            hit_object: The slider to write.
            position: Where its head sits, which the points are relative to.
        """
        control_points = hit_object.Path.ControlPoints

        for i, point in enumerate(control_points):
            if point.Type is not None:
                writer.write(_path_type_prefix(point.Type))

            if i != 0:
                writer.write(
                    f"{_num(position.X + point.Position.X)}:"
                    f"{_num(position.Y + point.Position.Y)}"
                )
                writer.write("|" if i != len(control_points) - 1 else ",")

        repeat_count = getattr(hit_object, "RepeatCount", 0)
        span_count = repeat_count + 1

        writer.write(f"{_num(span_count)},")
        expected = hit_object.Path.ExpectedDistance
        writer.write(
            f"{_num(expected if expected is not None else hit_object.Path.Distance)},"
        )

        node_samples = getattr(hit_object, "NodeSamples", None)
        if node_samples is None:
            return

        for i in range(span_count + 1):
            sound = (
                int(_to_legacy_hit_sound_type(node_samples[i]))
                if i < len(node_samples)
                else 0
            )
            writer.write(str(sound))
            writer.write("|" if i != span_count else ",")

        for i in range(span_count + 1):
            writer.write(
                self._sample_bank(node_samples[i], True)
                if i < len(node_samples)
                else "0:0"
            )
            writer.write("|" if i != span_count else ",")

    def _add_end_time_data(self, writer, hit_object) -> None:
        """Write an object's end time.

        Args:
            writer: The text stream to write to.
            hit_object: The object to write.
        """
        object_type = self._object_type(hit_object)

        # A mania hold writes its end time as though it were sample data.
        suffix = ":" if object_type == LegacyHitObjectType.Hold else ","

        writer.write(f"{_num(hit_object.EndTime)}{suffix}")

    def _sample_bank(self, samples: list, banks_only: bool = False) -> str:
        """Return the sample banks an object is written with.

        Args:
            samples: The object's samples.
            banks_only: Whether to leave off the custom bank, volume and file.
        """
        normal = next((s for s in samples if s.Name == HIT_NORMAL), None)
        addition = next(
            (
                s
                for s in samples
                if s.Name and s.Name != HIT_NORMAL and not s.EditorAutoBank
            ),
            None,
        )

        normal_bank = _to_legacy_sample_bank(normal.Bank if normal else None)
        add_bank = _to_legacy_sample_bank(addition.Bank if addition else None)

        result = f"{int(normal_bank)}:{int(add_bank)}"

        if banks_only:
            return result

        named = next((s for s in samples if s.Name), None)
        custom_sample_bank = _to_legacy_custom_sample_bank(named)
        sample_filename = next(
            (s.LookupNames[0] for s in samples if isinstance(s, FileHitSampleInfo)),
            "",
        )
        volume = samples[0].Volume if samples else 100

        # Outside mania the custom bank and volume are left off: the control
        # points already carry them, and repeating them here confuses the
        # editor.
        if self._online_ruleset_id != 3:
            custom_sample_bank = 0
            volume = 0

        return f"{result}:{custom_sample_bank}:{volume}:{sample_filename}"


class _ControlPointProperties:
    """The six values one line of the timing section carries."""

    def __init__(
        self,
        SliderVelocity: float = 0.0,
        TimingSignature: int = 0,
        SampleBank: int = 0,
        CustomSampleBank: int = 0,
        SampleVolume: int = 0,
        EffectFlags: LegacyEffectFlags = LegacyEffectFlags.None_,
    ) -> None:
        """Create a set of properties.

        Everything starts at zero rather than at a sensible default, because
        osu! begins from a blank value type. The difference shows: a beatmap
        whose first group would otherwise look unchanged still gets a line.

        Args:
            SliderVelocity: The velocity multiplier in effect.
            TimingSignature: The beats per bar.
            SampleBank: Which of the three built-in banks is in use.
            CustomSampleBank: Which numbered custom bank is in use.
            SampleVolume: How loud the samples are.
            EffectFlags: Kiai and the omitted first bar line.
        """
        self.SliderVelocity = SliderVelocity
        self.TimingSignature = TimingSignature
        self.SampleBank = SampleBank
        self.CustomSampleBank = CustomSampleBank
        self.SampleVolume = SampleVolume
        self.EffectFlags = EffectFlags

    def copy(self) -> _ControlPointProperties:
        """Return an independent copy of these properties."""
        return _ControlPointProperties(
            self.SliderVelocity,
            self.TimingSignature,
            self.SampleBank,
            self.CustomSampleBank,
            self.SampleVolume,
            self.EffectFlags,
        )

    def IsRedundant(self, other: _ControlPointProperties) -> bool:
        """Return whether writing these would change nothing.

        Args:
            other: The properties already in effect.
        """
        return (
            self.SliderVelocity == other.SliderVelocity
            and self.TimingSignature == other.TimingSignature
            and self.SampleBank == other.SampleBank
            and self.CustomSampleBank == other.CustomSampleBank
            and self.SampleVolume == other.SampleVolume
            and self.EffectFlags == other.EffectFlags
        )


def _output_control_point(
    writer, properties: _ControlPointProperties, is_timing_point: bool
) -> None:
    """Write the tail of one timing section line.

    Args:
        writer: The text stream to write to.
        properties: The values to write.
        is_timing_point: Whether this line carries its own beat length.
    """
    writer.write(f"{properties.TimingSignature},")
    writer.write(f"{properties.SampleBank},")
    writer.write(f"{properties.CustomSampleBank},")
    writer.write(f"{properties.SampleVolume},")
    writer.write("1," if is_timing_point else "0,")
    writer.write(f"{int(properties.EffectFlags)}")
    _write_line(writer, "")


def _sample_point_for(time: float, samples: list) -> SampleControlPoint:
    """Return the control point that would produce a set of samples.

    Args:
        time: When the samples sound.
        samples: The samples to describe.
    """
    volume = max(s.Volume for s in samples)

    bank = next(
        (s.Bank for s in samples if s.Name == HIT_NORMAL), None
    ) or samples[0].Bank

    custom_index = max(_custom_index_of(s) for s in samples)

    return SampleControlPoint(
        Time=time,
        SampleVolume=volume,
        SampleBank=bank,
        CustomSampleBank=custom_index,
    )


def _custom_index_of(sample) -> int:
    """Return which numbered custom bank a sample belongs to.

    Args:
        sample: The sample to read.
    """
    if isinstance(sample, (LegacyHitSampleInfo, FileHitSampleInfo)):
        return sample.CustomSampleBank

    if sample.Suffix is not None:
        try:
            return int(sample.Suffix)
        except ValueError:
            pass

    return 1 if getattr(sample, "UseBeatmapSamples", False) else -1


def _to_legacy_custom_sample_bank(sample) -> int:
    """Return the custom bank index a sample carries.

    Args:
        sample: The sample to read, which may be nothing.
    """
    if isinstance(sample, (LegacyHitSampleInfo, FileHitSampleInfo)):
        return sample.CustomSampleBank

    return 0


def _to_legacy_sample_bank(bank: str | None) -> LegacySampleBank:
    """Return which of the built-in banks a name refers to.

    Args:
        bank: The bank's name, which may be nothing.
    """
    match (bank or "").lower():
        case _ if bank is None:
            return LegacySampleBank.None_
        case s if s == BANK_NORMAL:
            return LegacySampleBank.Normal
        case s if s == BANK_SOFT:
            return LegacySampleBank.Soft
        case s if s == BANK_DRUM:
            return LegacySampleBank.Drum
        case _:
            return LegacySampleBank.None_


def _to_legacy_hit_sound_type(samples: list) -> LegacyHitSoundType:
    """Return the sound flags a set of samples is written as.

    Args:
        samples: The samples to describe.
    """
    sound_type = LegacyHitSoundType.None_

    for sample in samples:
        match sample.Name:
            case s if s == HIT_WHISTLE:
                sound_type |= LegacyHitSoundType.Whistle
            case s if s == HIT_FINISH:
                sound_type |= LegacyHitSoundType.Finish
            case s if s == HIT_CLAP:
                sound_type |= LegacyHitSoundType.Clap

    return sound_type


def _path_type_prefix(path_type) -> str:
    """Return the letter a path segment's type is written as.

    Args:
        path_type: The segment type.
    """
    match path_type.type:
        case SplineType.BSpline:
            return f"B{path_type.degree}|" if path_type.degree else "B|"
        case SplineType.Catmull:
            return "C|"
        case SplineType.PerfectCurve:
            return "P|"
        case SplineType.Linear:
            return "L|"

    return ""


def _file_name(path: str) -> str:
    """Return just the file name of a path.

    Args:
        path: The path to trim.
    """
    return path.replace("\\", "/").rsplit("/", 1)[-1]


def _flag(value: bool) -> str:
    """Return a boolean as the digit the format writes.

    Args:
        value: The flag to write.
    """
    return "1" if value else "0"


def _num(value) -> str:
    """Return a number the way .NET writes one.

    A value that happens to be whole is written without a decimal point, and
    anything else with as few digits as still read back exactly.

    Args:
        value: The number to write.
    """
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)

    if value == int(value) and abs(value) < 1e16:
        return str(int(value))

    return repr(float(value))


def _num_f32(value) -> str:
    """Return a single-precision number the way .NET writes one.

    A ``float`` prints with as few digits as still read back as the same
    ``float``, which is fewer than a ``double`` would need: a stack leniency of
    seven tenths writes as ``0.7`` rather than ``0.699999988079071``.

    Args:
        value: The number to write.
    """
    if value == int(value) and abs(value) < 1e16:
        return str(int(value))

    for digits in range(1, 10):
        text = f"{value:.{digits}g}"
        if f32(float(text)) == f32(value):
            return text

    return repr(float(value))


def _write_line(writer, text: str) -> None:
    """Write one line, ended the way osu! ends them.

    Args:
        writer: The text stream to write to.
        text: The line to write.
    """
    writer.write(text)
    writer.write("\r\n")
