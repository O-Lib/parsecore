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

from parsecore.Rulesets.Objects.PathControlPoint import PathControlPoint
from parsecore.Rulesets.Objects.SliderPath import SliderPath
from parsecore.Rulesets.Osu.Objects.Slider import Slider
from parsecore.Utils.Vector2 import Vector2

# The playfield osu! positions every object inside.
PLAYFIELD_SIZE = Vector2(512, 384)


def ReflectVerticallyAlongPlayfield(osu_object) -> None:
    """Mirror an object across the playfield's horizontal centre line.

    A slider is mirrored by negating the Y of every control point, which keeps
    the curve's shape and length while flipping the direction it travels.

    Args:
        osu_object: The hit object to reflect, modified in place.
    """
    osu_object.Position = Vector2(
        osu_object.Position.X, PLAYFIELD_SIZE.Y - osu_object.Position.Y
    )

    if not isinstance(osu_object, Slider):
        return

    _modify_slider(
        osu_object,
        lambda point: PathControlPoint(
            Vector2(point.Position.X, -point.Position.Y), point.Type
        ),
    )


def ReflectHorizontallyAlongPlayfield(osu_object) -> None:
    """Mirror an object across the playfield's vertical centre line.

    Args:
        osu_object: The hit object to reflect, modified in place.
    """
    osu_object.Position = Vector2(
        PLAYFIELD_SIZE.X - osu_object.Position.X, osu_object.Position.Y
    )

    if not isinstance(osu_object, Slider):
        return

    _modify_slider(
        osu_object,
        lambda point: PathControlPoint(
            Vector2(-point.Position.X, point.Position.Y), point.Type
        ),
    )


def _modify_slider(slider, modify_control_point) -> None:
    """Rebuild a slider's path with every control point transformed.

    osu! assigns a whole new path rather than editing the existing one, which
    is what makes the length recompute.

    Args:
        slider: The slider to rebuild.
        modify_control_point: Returns the replacement for a control point.
    """
    control_points = [
        modify_control_point(PathControlPoint(point.Position, point.Type))
        for point in slider.Path.ControlPoints
    ]

    slider.Path = SliderPath(control_points, slider.Path.ExpectedDistance)
