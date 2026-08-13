"""Shared soccerball.bas matrix + fast pygame.draw renderer.

Used by benchmark_soccer.py (fast FPS) and benchmark_soccer_exact.py (live preview).
"""
from __future__ import annotations

import os
import sys
from typing import List, Sequence, Tuple
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic.bbc_graphics import disc_screen_radii, pixel_inside_disc_ellipse  # noqa: E402
from mini_basic.bbc_modes import bbc_mode_spec, bbc_os_scales  # noqa: E402
from test.bbc_expect import (  # noqa: E402
    bbc_cos_degrees,
    bbc_sin_degrees,
    matrix3_multiply,
    sum_slice_1d,
)

# Rotation step per frame (BBC degrees). Corpus/original: C += 0.03.
# soccerball.bas uses 0.5 because mini_basic BBCGraphics is still slow.
C_STEP_ORIGINAL_DEG = 0.03
C_STEP_FAST_DEG = 0.5
C_STEP_DEG = C_STEP_ORIGINAL_DEG
CIRCLE_OS_RADIUS = 432
Z_CLIP = -2.5
MODE9_ORIGIN = (640, 512)

BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
FACE_COLOUR = BLACK

# Corpus: C += 0.03 once per displayed frame at ~30 Hz → 0.9°/s ≈ 0.15 RPM.
REFERENCE_REFRESH_HZ = 30.0
DEFAULT_RPM = C_STEP_ORIGINAL_DEG * REFERENCE_REFRESH_HZ / 6.0
FAST_RPM = C_STEP_FAST_DEG * REFERENCE_REFRESH_HZ / 6.0


def pace_frame(clock, fps_target: int) -> None:
    """Pace display only; rotation must use wall-clock dt separately."""
    clock.tick(fps_target if fps_target > 0 else 0)


def degrees_per_second_from_rpm(rpm: float) -> float:
    """Full rotations per minute → BBC angle degrees per second."""
    return rpm * 360.0 / 60.0


def rpm_from_corpus_step(
    step_deg: float,
    *,
    refresh_hz: float = REFERENCE_REFRESH_HZ,
) -> float:
    """Match corpus C += step once per frame at refresh_hz."""
    return step_deg * refresh_hz / 6.0


def advance_rotation(
    c_angle: float,
    dt_seconds: float,
    *,
    rpm: float,
) -> float:
    """Integrate rotation from wall-clock elapsed time (not pygame tick ms)."""
    if dt_seconds <= 0:
        return c_angle
    return c_angle + degrees_per_second_from_rpm(rpm) * dt_seconds


def _rotation_z_degrees(angle_deg: float) -> List[List[float]]:
    c = bbc_cos_degrees(angle_deg)
    s = bbc_sin_degrees(angle_deg)
    return [
        [c, s, 0.0],
        [-s, c, 0.0],
        [0.0, 0.0, 1.0],
    ]


def _matrix_times_points(
    mat: Sequence[Sequence[float]],
    xyz: Sequence[Sequence[float]],
) -> List[List[float]]:
    planes = len(xyz)
    count = len(xyz[0])
    out = [[0.0] * count for _ in range(planes)]
    for col in range(count):
        vec = [float(xyz[row][col]) for row in range(planes)]
        for row in range(planes):
            total = 0.0
            for k in range(planes):
                total += float(mat[row][k]) * vec[k]
            out[row][col] = total
    return out


def compute_tmp(
    xyz: Sequence[Sequence[float]],
    b_mat: Sequence[Sequence[float]],
    c_angle: float,
) -> List[List[float]]:
    spin = _rotation_z_degrees(c_angle)
    combo = matrix3_multiply(b_mat, spin)
    return _matrix_times_points(combo, xyz)


def load_soccerball_arrays() -> Tuple[List[List[float]], List[List[float]]]:
    from mini_basic import BASICInterpreter, InterpreterConfig

    soccer = os.path.join(_ROOT, 'examples', 'games', 'soccerball.bas')
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
    )
    interp.load(soccer, announce=False)
    for line_num in sorted(interp.program):
        upper = interp.program[line_num].strip().upper()
        if upper.startswith('REPEAT'):
            interp.program[line_num] = 'REM bench-once'
        elif upper.startswith('UNTIL'):
            interp.program[line_num] = 'END'
    with patch('time.sleep'):
        interp.run()
    xyz = [[float(v) for v in row] for row in interp.array_storage[('XYZ', 'float')][2]]
    b_mat = [[float(v) for v in row] for row in interp.array_storage[('B', 'float')][2]]
    return xyz, b_mat


def mode9_size() -> Tuple[int, int]:
    spec = bbc_mode_spec(9)
    assert spec is not None
    return spec.gfx_width, spec.gfx_height


def os_to_screen(
    x_os: int,
    y_os: int,
    *,
    width: int,
    height: int,
    origin: Tuple[int, int] = MODE9_ORIGIN,
    x_scale: int | None = None,
    y_scale: int | None = None,
) -> Tuple[int, int]:
    if x_scale is None or y_scale is None:
        x_scale, y_scale = bbc_os_scales(width, height)
    abs_x = origin[0] + int(x_os)
    abs_y = origin[1] + int(y_os)
    sx = abs_x // x_scale
    sy = height - 1 - abs_y // y_scale
    return sx, sy


def _project_index(
    tmp: Sequence[Sequence[float]],
    index: int,
    *,
    width: int,
    height: int,
) -> Tuple[int, int]:
    denom = 36 + tmp[1][index]
    x_os = int(3200 * tmp[0][index] / denom)
    y_os = int(3200 * tmp[2][index] / denom)
    return os_to_screen(x_os, y_os, width=width, height=height)


def fill_disc_surface(
    surface,
    color: Tuple[int, int, int],
    cx: int,
    cy: int,
    srx: int,
    sry: int,
) -> None:
    """BBC CIRCLE FILL scanline ellipse on a pygame surface (not pygame.draw.circle)."""
    import math

    width, height = surface.get_size()
    for sy in range(max(0, cy - sry), min(height, cy + sry + 1)):
        dy = sy - cy
        if abs(dy) > sry:
            continue
        half_x = int(
            math.sqrt(max(0.0, float(srx * srx * (1.0 - (dy / sry) ** 2))))
        )
        x0 = max(0, cx - half_x)
        x1 = min(width, cx + half_x + 1)
        for sx in range(x0, x1):
            surface.set_at((sx, sy), color)


def fill_triangle_in_disc(
    surface,
    color: Tuple[int, int, int],
    tri: Sequence[Tuple[int, int]],
    *,
    cx: int,
    cy: int,
    srx: int,
    sry: int,
) -> None:
    """Rasterise a filled triangle but only paint pixels inside the ball disc.

    Vertex clipping shrinks faces and leaves yellow seams at the silhouette;
    BBC SDL hides that at C+=0.03. Pixel masking keeps full face geometry.
    """
    import math

    if len(tri) != 3:
        return
    ordered = sorted(((int(px), int(py)) for px, py in tri), key=lambda p: p[1])
    (x_a, y_a), (x_b, y_b), (x_c, y_c) = ordered

    def edge_x(y: int, x1i: int, y1i: int, x2i: int, y2i: int) -> List[float]:
        y_min = min(y1i, y2i)
        y_max = max(y1i, y2i)
        if y < y_min or y > y_max:
            return []
        if y1i == y2i:
            return [float(x1i), float(x2i)]
        t = (y - y1i) / (y2i - y1i)
        return [x1i + t * (x2i - x1i)]

    width, height = surface.get_size()
    y_start = int(y_a)
    y_end = int(y_c)
    for y in range(y_start, y_end + 1):
        if y < 0 or y >= height:
            continue
        xs: List[float] = []
        for xa, ya, xb, yb in (
            (x_a, y_a, x_b, y_b),
            (x_b, y_b, x_c, y_c),
            (x_c, y_c, x_a, y_a),
        ):
            xs.extend(edge_x(y, xa, ya, xb, yb))
        if len(xs) < 2:
            continue
        x_left = int(math.floor(min(xs)))
        x_right = int(math.ceil(max(xs)))
        for x in range(x_left, x_right + 1):
            if x < 0 or x >= width:
                continue
            if pixel_inside_disc_ellipse(x, y, cx, cy, srx, sry):
                surface.set_at((x, y), color)


def plot85_triangles_for_face(
    screen_pts: Sequence[Tuple[int, int]],
) -> List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]]:
    """Filled triangles from MOVE, MOVE, PLOT 85 × 3 (soccerball inner loop)."""
    if len(screen_pts) < 5:
        return []
    p0, p1, p2, p3, p4 = screen_pts[:5]
    return [(p0, p1, p2), (p1, p2, p3), (p2, p3, p4)]


def draw_soccerball_frame(
    surface,
    tmp: Sequence[Sequence[float]],
    *,
    width: int | None = None,
    height: int | None = None,
    face_colour: Tuple[int, int, int] = FACE_COLOUR,
) -> None:
    """One frame: yellow CIRCLE FILL + black PLOT 85 triangles (BBC rasteriser)."""
    if width is None or height is None:
        width, height = mode9_size()
    x_scale, y_scale = bbc_os_scales(width, height)

    surface.fill(BLACK)
    cx, cy = os_to_screen(
        0, 0, width=width, height=height, x_scale=x_scale, y_scale=y_scale,
    )
    srx, sry = disc_screen_radii(CIRCLE_OS_RADIUS, x_scale, y_scale)
    # pygame.draw.circle extends ~0.3px past BBC CIRCLE FILL — visible yellow rim at low RPM.
    fill_disc_surface(surface, YELLOW, cx, cy, srx, sry)

    index = 0
    for _j in range(12):
        z = sum_slice_1d(tmp[1], index, index + 4)
        pts: List[Tuple[int, int]] = []
        for _k in range(5):
            pts.append(_project_index(tmp, index, width=width, height=height))
            index += 1
        if z < Z_CLIP:
            for tri in plot85_triangles_for_face(pts):
                fill_triangle_in_disc(
                    surface,
                    face_colour,
                    tri,
                    cx=cx,
                    cy=cy,
                    srx=srx,
                    sry=sry,
                )
