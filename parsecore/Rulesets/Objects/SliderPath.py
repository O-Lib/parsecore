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

import bisect
import math

from parsecore.Rulesets.Objects.PathControlPoint import PathControlPoint
from parsecore.Rulesets.Objects.Types.PathType import LINEAR, PathType, SplineType
from parsecore.Utils import PathApproximator
from parsecore.Utils.Vector2 import Vector2, f32


class SliderPath:
    """A slider's curve, built from control points and an expected distance."""

    def __init__(
        self,
        control_points: list[PathControlPoint] | None = None,
        expected_distance: float | None = None,
    ) -> None:
        """Create a path from control points and an optional expected distance.

        Args:
            control_points: The path's control points, in order.
            expected_distance: The distance the beatmap declares for this
                slider; the path is trimmed or extended to match it.
        """
        self.ControlPoints: list[PathControlPoint] = list(control_points or [])
        self.ExpectedDistance: float | None = expected_distance

        self.OptimiseCatmull = False

        self._optimised_length = 0.0
        self._calculated_path: list[Vector2] = []
        self._cumulative_length: list[float] = []
        self._valid = False

    @property
    def Distance(self) -> float:
        """Return the path's total length."""
        self._ensure_valid()
        return self._cumulative_length[-1] if self._cumulative_length else 0.0

    @property
    def CalculatedDistance(self) -> float:
        """Return the length of the flattened path before any trimming."""
        self._ensure_valid()
        return self._calculated_length

    def PositionAt(self, progress: float) -> Vector2:
        """Return the position at a progress value along the path.

        Args:
            progress: The progress along the path, ``0`` to ``1``.

        Returns:
            The point on the path.
        """
        self._ensure_valid()
        d = self._progress_to_distance(progress)
        return self._interpolate_vertices(self._index_of_distance(d), d)

    def invalidate(self) -> None:
        """Mark the cached geometry as stale so it is recomputed on next use."""
        self._valid = False

    def _ensure_valid(self) -> None:
        """Recompute the flattened path and its lengths if they are stale."""
        if self._valid:
            return
        self._calculate_path()
        self._calculate_length()
        self._valid = True

    def _calculate_path(self) -> None:
        """Flatten every segment of the path into ``_calculated_path``."""
        self._calculated_path = []
        self._optimised_length = 0.0

        if not self.ControlPoints:
            return

        vertices = [cp.Position for cp in self.ControlPoints]

        start = 0
        for i in range(len(self.ControlPoints)):
            if self.ControlPoints[i].Type is None and i < len(self.ControlPoints) - 1:
                continue

            # The current vertex ends the segment.
            segment_vertices = vertices[start : i + 1]
            segment_type = self.ControlPoints[start].Type or LINEAR

            if len(segment_vertices) == 1:
                # A lone vertex is already flat.
                self._calculated_path.append(segment_vertices[0])
            elif segment_vertices:
                subpath = self._calculate_sub_path(segment_vertices, segment_type)

                skip_first = bool(
                    self._calculated_path
                    and subpath
                    and self._calculated_path[-1] == subpath[0]
                )
                self._calculated_path.extend(subpath[1:] if skip_first else subpath)

            start = i

    def _calculate_sub_path(
        self, sub_control_points: list[Vector2], type_: PathType
    ) -> list[Vector2]:
        """Flatten a single segment according to its curve type.

        Args:
            sub_control_points: The segment's control points.
            type_: The segment's curve type.

        Returns:
            The flattened points of that segment.
        """
        match type_.type:
            case SplineType.Linear:
                return PathApproximator.linear_to_piecewise_linear(sub_control_points)

            case SplineType.PerfectCurve:
                if len(sub_control_points) == 3:
                    properties = PathApproximator.circular_arc_properties(
                        sub_control_points
                    )
                    if properties.IsValid:
                        if 2 * properties.Radius <= 0.1:
                            sub_points = 2
                        else:
                            sub_points = max(
                                2,
                                math.ceil(
                                    properties.ThetaRange
                                    / (
                                        2
                                        * math.acos(
                                            max(-1.0, 1.0 - (0.1 / properties.Radius))
                                        )
                                    )
                                ),
                            )
                        if sub_points < 1000:
                            subpath = (
                                PathApproximator.circular_arc_to_piecewise_linear(
                                    sub_control_points
                                )
                            )
                            if subpath:
                                return subpath

            case SplineType.Catmull:
                subpath = PathApproximator.catmull_to_piecewise_linear(
                    sub_control_points
                )
                if not self.OptimiseCatmull:
                    return subpath
                return self._optimise_catmull_path(subpath)

        return PathApproximator.b_spline_to_piecewise_linear(
            sub_control_points,
            type_.degree
            if type_.degree is not None
            else len(sub_control_points),
        )

    def _optimise_catmull_path(self, subpath: list[Vector2]) -> list[Vector2]:
        """Drop catmull points that sit within six pixels of the last kept one.

        osu!stable only drew segments six pixels apart, which matters where a
        catmull path loops around stacked knots. The dropped length is recorded
        so the path is not then stretched back to the expected distance.

        Args:
            subpath: The flattened catmull segment.

        Returns:
            The reduced segment.
        """
        catmull_segment_length = PathApproximator.CATMULL_DETAIL * 2

        optimised_path: list[Vector2] = []
        last_start: Vector2 | None = None
        length_removed_since_start = 0.0

        for i, point in enumerate(subpath):
            if last_start is None:
                optimised_path.append(point)
                last_start = point
                continue

            dist_from_start = Vector2.distance(last_start, point)
            length_removed_since_start += Vector2.distance(subpath[i - 1], point)

            # Six pixels from the start, the last vertex at a knot, or the end.
            if (
                dist_from_start > 6
                or (i + 1) % catmull_segment_length == 0
                or i == len(subpath) - 1
            ):
                optimised_path.append(point)
                self._optimised_length += length_removed_since_start - dist_from_start
                last_start = None
                length_removed_since_start = 0.0

        return optimised_path

    def _calculate_length(self) -> None:
        """Build the cumulative length table, honouring the expected distance."""
        self._calculated_length = self._optimised_length
        self._cumulative_length = [0.0]

        for i in range(len(self._calculated_path) - 1):
            diff = self._calculated_path[i + 1] - self._calculated_path[i]
            self._calculated_length += diff.length()
            self._cumulative_length.append(self._calculated_length)

        expected_distance = self.ExpectedDistance
        if expected_distance is None or self._calculated_length == expected_distance:
            return

        if (
            len(self._calculated_path) >= 2
            and self._calculated_path[-1] == self._calculated_path[-2]
            and expected_distance > self._calculated_length
        ):
            self._cumulative_length.append(self._calculated_length)
            return

        self._cumulative_length.pop()

        path_end_index = len(self._calculated_path) - 1

        if self._calculated_length > expected_distance:
            while (
                self._cumulative_length
                and self._cumulative_length[-1] >= expected_distance
            ):
                self._cumulative_length.pop()
                del self._calculated_path[path_end_index]
                path_end_index -= 1

        if path_end_index <= 0:
            # The expected distance is zero or negative.
            self._cumulative_length.append(0.0)
            return

        direction = (
            self._calculated_path[path_end_index]
            - self._calculated_path[path_end_index - 1]
        ).normalised()

        self._calculated_path[path_end_index] = self._calculated_path[
            path_end_index - 1
        ] + direction * f32(expected_distance - self._cumulative_length[-1])
        self._cumulative_length.append(expected_distance)

    def _index_of_distance(self, d: float) -> int:
        """Return the index of the first cumulative length at or past ``d``."""
        return bisect.bisect_left(self._cumulative_length, d)

    def _progress_to_distance(self, progress: float) -> float:
        """Return the distance along the path for a progress value."""
        return min(max(progress, 0.0), 1.0) * self.Distance

    def _interpolate_vertices(self, i: int, d: float) -> Vector2:
        """Return the point at distance ``d``, interpolating within segment ``i``."""
        if not self._calculated_path:
            return Vector2()

        if i <= 0:
            return self._calculated_path[0]
        if i >= len(self._calculated_path):
            return self._calculated_path[-1]

        p0 = self._calculated_path[i - 1]
        p1 = self._calculated_path[i]

        d0 = self._cumulative_length[i - 1]
        d1 = self._cumulative_length[i]

        if abs(d0 - d1) <= 1e-7:
            return p0

        w = (d - d0) / (d1 - d0)
        return p0 + (p1 - p0) * f32(w)
