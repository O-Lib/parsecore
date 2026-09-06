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
from dataclasses import dataclass

from parsecore.Utils.Vector2 import Vector2, f32

BEZIER_TOLERANCE = 0.25
CATMULL_DETAIL = 50

# Single precision, because it is divided by the radius before anything widens
# it and the result decides how many points the arc gets.
CIRCULAR_ARC_TOLERANCE = f32(0.1)


def _almost_equals(a: float, b: float, acceptable_difference: float = 1e-3) -> bool:
    """Return whether two values are within ``acceptable_difference``."""
    return abs(a - b) <= acceptable_difference


def _bezier_is_flat_enough(control_points: list[Vector2]) -> bool:
    """Return whether a bezier segment is flat enough to stop subdividing.

    Args:
        control_points: The segment's control points.
    """
    for i in range(1, len(control_points) - 1):
        d = control_points[i - 1] - control_points[i] * 2.0 + control_points[i + 1]
        if d.length_squared() > BEZIER_TOLERANCE * BEZIER_TOLERANCE * 4:
            return False
    return True


def _bezier_subdivide(
    control_points: list[Vector2],
    left: list[Vector2],
    right: list[Vector2],
    subdivision_buffer: list[Vector2],
    count: int,
) -> None:
    """Split a bezier segment in two using de Casteljau's algorithm.

    Args:
        control_points: The segment to split.
        left: Output buffer receiving the left half.
        right: Output buffer receiving the right half.
        subdivision_buffer: Scratch buffer of at least ``count`` entries.
        count: The number of control points.
    """
    midpoints = subdivision_buffer
    for i in range(count):
        midpoints[i] = control_points[i]

    for i in range(count):
        left[i] = midpoints[0]
        right[count - i - 1] = midpoints[count - i - 1]

        for j in range(count - i - 1):
            midpoints[j] = (midpoints[j] + midpoints[j + 1]) / 2.0


def _bezier_approximate(
    control_points: list[Vector2],
    output: list[Vector2],
    subdivision_buffer1: list[Vector2],
    subdivision_buffer2: list[Vector2],
    count: int,
) -> None:
    """Append a flat-enough bezier segment to ``output`` as line segments.

    Args:
        control_points: The segment to approximate.
        output: The list receiving the approximated points.
        subdivision_buffer1: Scratch buffer of ``count`` entries.
        subdivision_buffer2: Scratch buffer of ``count * 2 - 1`` entries.
        count: The number of control points.
    """
    left = subdivision_buffer2
    right = subdivision_buffer1

    _bezier_subdivide(control_points, left, right, subdivision_buffer1, count)

    for i in range(count - 1):
        left[count + i] = right[i + 1]

    output.append(control_points[0])

    for i in range(1, count - 1):
        index = 2 * i
        p = (left[index - 1] + left[index] * 2.0 + left[index + 1]) * 0.25
        output.append(p)


def bezier_to_piecewise_linear(control_points: list[Vector2]) -> list[Vector2]:
    """Approximate a bezier curve with a list of line segments.

    Args:
        control_points: The curve's control points.

    Returns:
        The flattened points along the curve.
    """
    return b_spline_to_piecewise_linear(control_points, len(control_points) - 1)


def _b_spline_to_bezier_internal(
    control_points: list[Vector2], degree: int
) -> tuple[list[list[Vector2]], int]:
    """Split a B-spline into bezier segments by repeated knot insertion.

    Args:
        control_points: The spline's control points.
        degree: The requested spline degree.

    Returns:
        The bezier segments as a stack (last entry is processed first), and the
        degree actually used.
    """
    degree = min(degree, len(control_points) - 1)
    point_count = len(control_points) - 1
    points = list(control_points)

    result: list[list[Vector2]] = []

    if degree == point_count:
        result.append(points)
        return result, degree

    for i in range(point_count - degree):
        sub_bezier: list[Vector2] = [Vector2()] * (degree + 1)
        sub_bezier[0] = points[i]

        for j in range(degree - 1):
            sub_bezier[j + 1] = points[i + 1]

            for k in range(1, degree - j):
                weight = min(k, point_count - degree - i)
                points[i + k] = (
                    points[i + k] * weight + points[i + k + 1]
                ) / (weight + 1)

        sub_bezier[degree] = points[i + 1]
        result.append(sub_bezier)

    result.append(points[point_count - degree:])

    # osu! rebuilds the stack from itself here, which reverses it.
    result.reverse()
    return result, degree


def b_spline_to_piecewise_linear(
    control_points: list[Vector2], degree: int
) -> list[Vector2]:
    """Approximate a B-spline (or a bezier, when ``degree`` spans all points).

    Args:
        control_points: The curve's control points.
        degree: The spline degree; ``len(control_points) - 1`` gives a bezier.

    Returns:
        The flattened points along the curve.

    Raises:
        ValueError: If the degree is below one.
    """
    if degree < 1:
        raise ValueError("degree must be at least one")

    if len(control_points) < 2:
        return [] if not control_points else [control_points[0]]

    degree = min(degree, len(control_points) - 1)

    output: list[Vector2] = []
    point_count = len(control_points) - 1

    to_flatten, degree = _b_spline_to_bezier_internal(control_points, degree)
    free_buffers: list[list[Vector2]] = []

    subdivision_buffer1 = [Vector2() for _ in range(degree + 1)]
    subdivision_buffer2 = [Vector2() for _ in range(degree * 2 + 1)]
    left_child = subdivision_buffer2

    while to_flatten:
        parent = to_flatten.pop()

        if _bezier_is_flat_enough(parent):
            _bezier_approximate(
                parent, output, subdivision_buffer1, subdivision_buffer2, degree + 1
            )
            free_buffers.append(parent)
            continue

        right_child = (
            free_buffers.pop()
            if free_buffers
            else [Vector2() for _ in range(degree + 1)]
        )
        _bezier_subdivide(
            parent, left_child, right_child, subdivision_buffer1, degree + 1
        )

        for i in range(degree + 1):
            parent[i] = left_child[i]

        to_flatten.append(right_child)
        to_flatten.append(parent)

    output.append(control_points[point_count])
    return output


def _catmull_find_point(
    v1: Vector2, v2: Vector2, v3: Vector2, v4: Vector2, t: float
) -> Vector2:
    """Return the catmull-rom point at ``t`` between ``v2`` and ``v3``.

    Args:
        v1: The point before the segment.
        v2: The segment's start.
        v3: The segment's end.
        v4: The point after the segment.
        t: The progress along the segment, ``0`` to ``1``.
    """
    t = f32(t)
    t2 = f32(t * t)
    t3 = f32(t * t2)

    def axis(a: float, b: float, c: float, d: float) -> float:
        """Return one axis of the point, in single precision throughout.

        Every operation is narrowed on its own and applied left to right,
        because osu! evaluates this polynomial in ``float`` and the order the
        partial sums round in is visible in the result.
        """
        linear = f32(f32(-a + c) * t)

        quadratic = f32(2.0 * a)
        quadratic = f32(quadratic - f32(5.0 * b))
        quadratic = f32(quadratic + f32(4.0 * c))
        quadratic = f32(f32(quadratic - d) * t2)

        cubic = f32(-a + f32(3.0 * b))
        cubic = f32(cubic - f32(3.0 * c))
        cubic = f32(f32(cubic + d) * t3)

        total = f32(2.0 * b)
        total = f32(total + linear)
        total = f32(total + quadratic)
        total = f32(total + cubic)
        return f32(0.5 * total)

    return Vector2(axis(v1.X, v2.X, v3.X, v4.X), axis(v1.Y, v2.Y, v3.Y, v4.Y))


def catmull_to_piecewise_linear(control_points: list[Vector2]) -> list[Vector2]:
    """Approximate a catmull-rom curve with a list of line segments.

    Args:
        control_points: The curve's control points.

    Returns:
        The flattened points along the curve.
    """
    result: list[Vector2] = []

    for i in range(len(control_points) - 1):
        v1 = control_points[i - 1] if i > 0 else control_points[i]
        v2 = control_points[i]
        v3 = (
            control_points[i + 1]
            if i < len(control_points) - 1
            else v2 + v2 - v1
        )
        v4 = (
            control_points[i + 2]
            if i < len(control_points) - 2
            else v3 + v3 - v2
        )

        for c in range(CATMULL_DETAIL):
            result.append(_catmull_find_point(v1, v2, v3, v4, c / CATMULL_DETAIL))
            result.append(
                _catmull_find_point(v1, v2, v3, v4, (c + 1) / CATMULL_DETAIL)
            )

    return result


@dataclass(slots=True)
class CircularArcProperties:
    """The centre, radius and angular range of a three-point circular arc."""

    IsValid: bool = False
    ThetaStart: float = 0.0
    ThetaRange: float = 0.0
    Direction: float = 1.0
    Radius: float = 0.0
    Centre: Vector2 = None  # type: ignore[assignment]

    @property
    def ThetaEnd(self) -> float:
        """Return the arc's end angle."""
        return self.ThetaStart + self.ThetaRange * self.Direction


def circular_arc_properties(control_points: list[Vector2]) -> CircularArcProperties:
    """Return the circle through three points, or an invalid result.

    Uses the Cartesian circumcircle formula in single precision, as
    ``osu.Framework`` does.

    Args:
        control_points: Exactly three points describing the arc.

    Returns:
        The arc's properties; ``IsValid`` is ``False`` for degenerate input.
    """
    a, b, c = control_points[0], control_points[1], control_points[2]

    # Three collinear points describe no circle.
    if _almost_equals(
        0.0, (b.Y - a.Y) * (c.X - a.X) - (b.X - a.X) * (c.Y - a.Y)
    ):
        return CircularArcProperties(IsValid=False, Centre=Vector2())

    d = f32(
        2
        * f32(
            f32(a.X * (b - c).Y) + f32(b.X * (c - a).Y) + f32(c.X * (a - b).Y)
        )
    )
    if d == 0:
        return CircularArcProperties(IsValid=False, Centre=Vector2())

    a_sq = a.length_squared()
    b_sq = b.length_squared()
    c_sq = c.length_squared()

    centre = Vector2(
        f32(
            f32(a_sq * (b - c).Y) + f32(b_sq * (c - a).Y) + f32(c_sq * (a - b).Y)
        ),
        f32(
            f32(a_sq * (c - b).X) + f32(b_sq * (a - c).X) + f32(c_sq * (b - a).X)
        ),
    ) / d

    d_a = a - centre
    d_c = c - centre

    radius = d_a.length()

    theta_start = math.atan2(d_a.Y, d_a.X)
    theta_end = math.atan2(d_c.Y, d_c.X)

    while theta_end < theta_start:
        theta_end += 2 * math.pi

    direction = 1.0
    theta_range = theta_end - theta_start

    # Draw the arc on whichever side of AC the point B lies.
    ortho_a_to_c = c - a
    ortho_a_to_c = Vector2(ortho_a_to_c.Y, -ortho_a_to_c.X)

    if Vector2.dot(ortho_a_to_c, b - a) < 0:
        direction = -direction
        theta_range = 2 * math.pi - theta_range

    return CircularArcProperties(
        IsValid=True,
        ThetaStart=theta_start,
        ThetaRange=theta_range,
        Direction=direction,
        Radius=radius,
        Centre=centre,
    )


def circular_arc_to_piecewise_linear(control_points: list[Vector2]) -> list[Vector2]:
    """Approximate a three-point circular arc with line segments.

    Falls back to a bezier approximation when the three points are collinear.

    Args:
        control_points: Exactly three points describing the arc.

    Returns:
        The flattened points along the arc.
    """
    pr = circular_arc_properties(control_points)
    if not pr.IsValid:
        return bezier_to_piecewise_linear(control_points)

    if 2 * pr.Radius <= CIRCULAR_ARC_TOLERANCE:
        amount_points = 2
    else:
        # How far the arc may bend between two points. The tolerance and the
        # radius are both single precision, so the whole argument is worked out
        # there and only widens once the angle is taken. Near a full turn the
        # argument sits so close to one that this rounding decides whether the
        # arc gets one more point.
        cosine = f32(1 - f32(CIRCULAR_ARC_TOLERANCE / pr.Radius))
        amount_points = max(
            2, math.ceil(pr.ThetaRange / (2 * math.acos(max(-1.0, cosine))))
        )

    output: list[Vector2] = []
    for i in range(amount_points):
        fract = i / (amount_points - 1)
        theta = pr.ThetaStart + pr.Direction * fract * pr.ThetaRange
        o = Vector2(f32(math.cos(theta)), f32(math.sin(theta))) * pr.Radius
        output.append(pr.Centre + o)

    return output


def linear_to_piecewise_linear(control_points: list[Vector2]) -> list[Vector2]:
    """Return the control points unchanged; a linear path is already flat.

    Args:
        control_points: The path's control points.
    """
    return list(control_points)
