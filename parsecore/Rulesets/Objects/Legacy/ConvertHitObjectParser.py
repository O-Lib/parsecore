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

from dataclasses import dataclass, replace

from parsecore.Audio.HitSampleInfo import (
    BANK_NORMAL,
    HIT_CLAP,
    HIT_FINISH,
    HIT_NORMAL,
    HIT_WHISTLE,
    FileHitSampleInfo,
    HitSampleInfo,
)
from parsecore.Beatmaps.Formats import Parsing
from parsecore.Beatmaps.Legacy.LegacyHitObjectType import LegacyHitObjectType
from parsecore.Beatmaps.Legacy.LegacyHitSoundType import LegacyHitSoundType
from parsecore.Beatmaps.Legacy.LegacySampleBank import LegacySampleBank
from parsecore.Rulesets.Objects.Legacy.ConvertHitCircle import ConvertHitCircle
from parsecore.Rulesets.Objects.Legacy.ConvertHitObject import ConvertHitObject
from parsecore.Rulesets.Objects.Legacy.ConvertHold import ConvertHold
from parsecore.Rulesets.Objects.Legacy.ConvertSlider import ConvertSlider
from parsecore.Rulesets.Objects.Legacy.ConvertSpinner import ConvertSpinner
from parsecore.Rulesets.Objects.PathControlPoint import PathControlPoint
from parsecore.Rulesets.Objects.SliderPath import SliderPath
from parsecore.Rulesets.Objects.Types.PathType import (
    BEZIER,
    LINEAR,
    PathType,
    SplineType,
)
from parsecore.Utils.Precision import AlmostEquals
from parsecore.Utils.Vector2 import Vector2

# From this beatmap format on, path coordinates keep their fractional part.
FIRST_LAZER_VERSION = 128


@dataclass
class SampleBankInfo:
    """The sample banks in effect for one hit object or slider node."""

    Filename: str | None = None
    BankForNormal: str = ""
    BankForAdditions: str = ""
    Volume: int = 0
    CustomSampleBank: int = 0
    EditorAutoBank: bool = True

    def Clone(self) -> SampleBankInfo:
        """Return an independent copy."""
        return replace(self)


@dataclass(frozen=True, slots=True)
class LegacyHitSampleInfo(HitSampleInfo):
    """A sample that remembers what the beatmap said about it.

    Which of its fields the beatmap set and which it left open decides what a
    sample control point is allowed to fill in later.
    """

    CustomSampleBank: int = 0
    IsLayered: bool = False
    BankSpecified: bool = False


def _is_linear(p0: Vector2, p1: Vector2, p2: Vector2) -> bool:
    """Return whether three points lie on a straight line.

    Args:
        p0: The first point.
        p1: The second point.
        p2: The third point.
    """
    return abs((p1.Y - p0.Y) * (p2.X - p0.X) - (p1.X - p0.X) * (p2.Y - p0.Y)) < 1e-3


class ConvertHitObjectParser:
    """Turns one ``[HitObjects]`` line into a :class:`ConvertHitObject`."""

    def __init__(self, offset: float = 0.0, format_version: int = 14) -> None:
        """Create a parser.

        Args:
            offset: A timing offset applied to every object (early formats).
            format_version: The beatmap's file format version.
        """
        self.Offset = offset
        self.FormatVersion = format_version
        self.first_object = True
        self.last_object: ConvertHitObject | None = None

    def Parse(self, text: str) -> ConvertHitObject | None:
        """Parse one hit-object line.

        Args:
            text: The raw line.

        Returns:
            The parsed object, or ``None`` if the line declares no known type.
        """
        split = text.strip().split(",")
        if len(split) < 5:
            return None

        # osu! truncates coordinates to integers before using them.
        pos = Vector2(
            int(Parsing.ParseFloat(split[0], Parsing.MAX_COORDINATE_VALUE)),
            int(Parsing.ParseFloat(split[1], Parsing.MAX_COORDINATE_VALUE)),
        )

        start_time = Parsing.ParseDouble(split[2]) + self.Offset

        type_ = LegacyHitObjectType(Parsing.ParseInt(split[3]))

        combo_offset = int(type_ & LegacyHitObjectType.ComboOffset) >> 4
        type_ &= ~LegacyHitObjectType.ComboOffset

        combo = bool(type_ & LegacyHitObjectType.NewCombo)
        type_ &= ~LegacyHitObjectType.NewCombo

        sound_type = LegacyHitSoundType(Parsing.ParseInt(split[4]))
        bank_info = SampleBankInfo()

        result: ConvertHitObject | None = None

        if type_ & LegacyHitObjectType.Circle:
            result = ConvertHitCircle(start_time, pos)
            if len(split) > 5:
                self._read_custom_sample_banks(split[5], bank_info)

        elif type_ & LegacyHitObjectType.Slider:
            result = self._parse_slider(split, pos, start_time, sound_type, bank_info)

        elif type_ & LegacyHitObjectType.Spinner:
            duration = max(
                0.0, Parsing.ParseDouble(split[5]) + self.Offset - start_time
            )
            result = ConvertSpinner(start_time, start_time + duration)
            if len(split) > 6:
                self._read_custom_sample_banks(split[6], bank_info)

        elif type_ & LegacyHitObjectType.Hold:
            end_time = max(start_time, Parsing.ParseDouble(split[2]))
            if len(split) > 5 and split[5]:
                ss = split[5].split(":")
                end_time = max(start_time, Parsing.ParseDouble(ss[0]))
                self._read_custom_sample_banks(":".join(ss[1:]), bank_info)
            result = ConvertHold(start_time, end_time + self.Offset, pos)

        if result is None:
            return None

        result.StartTime = start_time

        if isinstance(result, (ConvertHitCircle, ConvertSlider)):
            # The first object of a beatmap always opens a combo, and so does
            # the first one after a spinner.
            result.NewCombo = (
                self.first_object
                or isinstance(self.last_object, ConvertSpinner)
                or combo
            )
            result.ComboOffset = combo_offset if combo else 0
        elif isinstance(result, ConvertSpinner):
            result.NewCombo = combo
        else:
            result.NewCombo = False

        result.LegacyType = int(type_)
        result.Samples = self._convert_sound_type(sound_type, bank_info)

        self.first_object = False
        self.last_object = result
        return result

    def _parse_slider(
        self,
        split: list[str],
        pos: Vector2,
        start_time: float,
        sound_type: LegacyHitSoundType,
        bank_info: SampleBankInfo,
    ) -> ConvertSlider | None:
        """Parse the slider-specific columns of a hit-object line.

        Args:
            split: The comma-separated columns.
            pos: The slider head's position.
            start_time: The slider's start time.
            sound_type: The object's default hit sound.
            bank_info: The object's default sample banks.

        Returns:
            The parsed slider.
        """
        if len(split) < 7:
            return None

        repeat_count = Parsing.ParseInt(split[6])
        if repeat_count > 9000:
            raise Parsing.ParsingError("repeat count is way too high")
        repeat_count = max(0, repeat_count - 1)

        length: float | None = None
        if len(split) > 7:
            length = max(
                0.0, Parsing.ParseDouble(split[7], Parsing.MAX_COORDINATE_VALUE)
            )
            if length == 0:
                length = None

        if len(split) > 10:
            self._read_custom_sample_banks(split[10], bank_info)

        # One node per repeat, plus the head and tail.
        nodes = repeat_count + 2

        node_bank_infos = [bank_info.Clone() for _ in range(nodes)]
        if len(split) > 9 and split[9]:
            sets = split[9].split("|")
            for i in range(min(nodes, len(sets))):
                self._read_custom_sample_banks(sets[i], node_bank_infos[i], True)

        node_sound_types = [sound_type] * nodes
        if len(split) > 8 and split[8]:
            adds = split[8].split("|")
            for i in range(min(nodes, len(adds))):
                try:
                    node_sound_types[i] = LegacyHitSoundType(int(adds[i]))
                except (ValueError, TypeError):
                    pass

        node_samples = [
            self._convert_sound_type(node_sound_types[i], node_bank_infos[i])
            for i in range(nodes)
        ]

        slider = ConvertSlider(start_time, pos)
        slider.Path = SliderPath(self._convert_path_string(split[5], pos), length)

        if AlmostEquals(slider.Path.Distance, 0):
            repeat_count = 0
            node_samples = [node_samples[0], node_samples[-1]]

        slider.RepeatCount = repeat_count
        slider.NodeSamples = node_samples
        return slider

    def _convert_path_string(
        self, point_string: str, offset: Vector2
    ) -> list[PathControlPoint]:
        """Parse a slider's path string into control points.

        Handles explicit segments (a curve letter mid-path) here, and leaves
        implicit segments -- two identical consecutive points -- to
        :meth:`_convert_points`.

        Args:
            point_string: The raw path, e.g. ``B|100:100|200:200``.
            offset: The slider head's position, subtracted from every point.

        Returns:
            The path's control points, relative to the slider head.
        """
        point_string_split = point_string.split("|")

        points: list[Vector2] = []
        segments: list[tuple[PathType, int]] = []

        for token in point_string_split:
            if not token:
                continue
            if token[0].isalpha():
                # A letter starts a new segment of that curve type.
                segments.append((PathType.from_legacy(token), len(points)))
                # The first segment is prepended with the slider head itself.
                if not points:
                    points.append(Vector2())
            else:
                points.append(self._read_point(token, offset))

        control_points: list[PathControlPoint] = []

        for i, (segment_type, start_index) in enumerate(segments):
            if i < len(segments) - 1:
                end_index = segments[i + 1][1]
                control_points.extend(
                    self._convert_points(
                        segment_type,
                        points[start_index:end_index],
                        points[end_index] if end_index < len(points) else None,
                    )
                )
            else:
                control_points.extend(
                    self._convert_points(segment_type, points[start_index:], None)
                )

        return control_points

    def _read_point(self, value: str, start_pos: Vector2) -> Vector2:
        """Parse one ``x:y`` point of a path.

        Args:
            value: The raw point.
            start_pos: The slider head, subtracted from the result.

        Returns:
            The point relative to the slider head.
        """
        vertex_split = value.split(":")

        x = Parsing.ParseFloat(vertex_split[0], Parsing.MAX_COORDINATE_VALUE)
        y = Parsing.ParseFloat(vertex_split[1], Parsing.MAX_COORDINATE_VALUE)

        if self.FormatVersion < FIRST_LAZER_VERSION:
            # Legacy formats truncate path coordinates to whole pixels.
            pos = Vector2(int(x), int(y))
        else:
            pos = Vector2(x, y)

        return pos - start_pos

    def _convert_points(
        self,
        type_: PathType,
        points: list[Vector2],
        end_point: Vector2 | None,
    ) -> list[PathControlPoint]:
        """Turn one segment's points into control points.

        A segment splits further wherever two consecutive points share a
        position -- a "red anchor" in the editor. For ``X|1:1|2:2|2:2|3:3``
        this yields ``X: {(1,1), (2,2)}`` then ``X: {(3,3)}``.

        Args:
            type_: The segment's declared curve type.
            points: The segment's points.
            end_point: The following segment's first point, counted for the
                perfect-curve rules but not returned.

        Returns:
            The segment's control points, in order.
        """
        if not points:
            return []

        vertices = [PathControlPoint(p) for p in points]

        # Edge cases that keep perfect curves matching osu!stable.
        if type_.type == SplineType.PerfectCurve:
            end_point_length = 0 if end_point is None else 1

            if self.FormatVersion < FIRST_LAZER_VERSION:
                if len(vertices) + end_point_length != 3:
                    type_ = BEZIER
                elif _is_linear(
                    points[0],
                    points[1],
                    end_point if end_point is not None else points[2],
                ):
                    # osu!stable drew collinear perfect curves as straight lines.
                    type_ = LINEAR
            elif len(vertices) + end_point_length > 3:
                type_ = BEZIER

        # The first control point always carries a definite type.
        vertices[0] = PathControlPoint(vertices[0].Position, type_)

        result: list[PathControlPoint] = []
        start_index = 0
        end_index = 0

        while True:
            end_index += 1
            if end_index >= len(vertices):
                break

            if vertices[end_index].Position != vertices[end_index - 1].Position:
                continue

            # Legacy catmull sliders have no multi-segment support, so adjacent
            # catmull segments stay merged.
            if (
                type_.type == SplineType.Catmull
                and end_index > 1
                and self.FormatVersion < FIRST_LAZER_VERSION
            ):
                continue

            # A segment's last control point may not start a new segment.
            if end_index == len(vertices) - 1:
                continue

            vertices[end_index - 1] = PathControlPoint(
                vertices[end_index - 1].Position, type_
            )
            result.extend(vertices[start_index:end_index])

            # The repeated point is implicit in the path, so it is skipped.
            start_index = end_index + 1

        if start_index < end_index:
            result.extend(vertices[start_index:end_index])

        return result

    def _read_custom_sample_banks(
        self, string: str, bank_info: SampleBankInfo, banks_only: bool = False
    ) -> None:
        """Read the trailing ``bank:addBank:custom:volume:file`` column.

        Args:
            string: The raw column.
            bank_info: The bank info to populate.
            banks_only: Whether only the two bank fields are present.
        """
        if not string:
            return

        split = string.split(":")

        bank = LegacySampleBank(Parsing.ParseInt(split[0]))
        add_bank = LegacySampleBank(Parsing.ParseInt(split[1])) if len(split) > 1 else (
            LegacySampleBank.None_
        )

        string_bank: str | None = bank.name.lower()
        if string_bank == "none_":
            string_bank = None
        string_add_bank: str | None = add_bank.name.lower()
        if string_add_bank == "none_":
            string_add_bank = None

        bank_info.EditorAutoBank = string_add_bank is None
        bank_info.BankForNormal = string_bank or ""
        bank_info.BankForAdditions = string_add_bank or string_bank or ""

        if banks_only:
            return

        if len(split) > 2:
            bank_info.CustomSampleBank = Parsing.ParseInt(split[2])
        if len(split) > 3:
            bank_info.Volume = max(0, Parsing.ParseInt(split[3]))
        if len(split) > 4:
            bank_info.Filename = split[4]

    def _convert_sound_type(
        self, type_: LegacyHitSoundType, bank_info: SampleBankInfo
    ) -> list[HitSampleInfo]:
        """Turn hit-sound flags plus banks into the samples that play.

        Args:
            type_: The hit-sound flags.
            bank_info: The banks and volume in effect.

        Returns:
            The samples for this object or node.
        """
        if bank_info.Filename:
            sound_types: list[HitSampleInfo] = [
                FileHitSampleInfo(
                    Bank=BANK_NORMAL,
                    Volume=bank_info.Volume,
                    Filename=bank_info.Filename,
                )
            ]
        else:
            sound_types = [
                self._legacy_sample(
                    HIT_NORMAL,
                    bank_info.BankForNormal,
                    bank_info,
                    editor_auto_bank=True,
                    # A sound that does not name the normal flag still plays a
                    # normal sample underneath it, as a layered one. No flags
                    # at all counts as a plain normal sample.
                    is_layered=(
                        type_ != LegacyHitSoundType.None_
                        and not (type_ & LegacyHitSoundType.Normal)
                    ),
                )
            ]

        for flag, name in (
            (LegacyHitSoundType.Finish, HIT_FINISH),
            (LegacyHitSoundType.Whistle, HIT_WHISTLE),
            (LegacyHitSoundType.Clap, HIT_CLAP),
        ):
            if type_ & flag:
                sound_types.append(
                    self._legacy_sample(
                        name,
                        bank_info.BankForAdditions,
                        bank_info,
                        editor_auto_bank=bank_info.EditorAutoBank,
                    )
                )

        return sound_types

    @staticmethod
    def _legacy_sample(
        name: str,
        bank: str,
        bank_info: SampleBankInfo,
        editor_auto_bank: bool,
        is_layered: bool = False,
    ) -> LegacyHitSampleInfo:
        """Return one sample as the beatmap described it.

        Args:
            name: Which sound this is.
            bank: The bank the beatmap named, if it named one.
            bank_info: The banks and volume in effect.
            editor_auto_bank: Whether the bank was left to the control points.
            is_layered: Whether this sample plays underneath another.
        """
        custom = bank_info.CustomSampleBank

        return LegacyHitSampleInfo(
            Name=name,
            Bank=bank or BANK_NORMAL,
            # A custom bank is only looked up from two upwards, for reasons
            # lost to osu!stable.
            Suffix=str(custom) if custom >= 2 else None,
            Volume=bank_info.Volume,
            EditorAutoBank=editor_auto_bank,
            CustomSampleBank=custom,
            IsLayered=is_layered,
            BankSpecified=bool(bank),
        )
