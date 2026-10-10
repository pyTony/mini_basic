"""Python-side expected values for mini_basic tests (manual-grounded).

Use when the authoritative answer comes from math/geometry rather than
trusting PRINT output from corpus programs (which may have typos).
References: documentation/manuals/bbcwin/extracts/
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple


def bbc_sin_degrees(angle_deg: float) -> float:
    """BBC BASIC SIN/COS/TAN take degrees (BB4W manual, DEG/RAD keywords)."""
    return math.sin(math.radians(angle_deg))


def bbc_cos_degrees(angle_deg: float) -> float:
    return math.cos(math.radians(angle_deg))


def rotation_matrix_y_degrees(angle_deg: float) -> List[List[float]]:
    """Row-major 3x3 rotation about Y (soccerball / gorillas convention)."""
    c = bbc_cos_degrees(angle_deg)
    s = bbc_sin_degrees(angle_deg)
    return [
        [c, 0.0, -s],
        [0.0, 1.0, 0.0],
        [s, 0.0, c],
    ]


def matrix3_identity() -> List[List[float]]:
    return [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]


def matrix3_multiply(
    left: Sequence[Sequence[float]],
    right: Sequence[Sequence[float]],
) -> List[List[float]]:
    rows = len(left)
    cols = len(right[0])
    inner = len(right)
    result = [[0.0] * cols for _ in range(rows)]
    for i in range(rows):
        for k in range(cols):
            total = 0.0
            for j in range(inner):
                total += float(left[i][j]) * float(right[j][k])
            result[i][k] = total
    return result


def circle_screen_pixel_area(os_radius: float, x_scale: float) -> float:
    """Filled circle pixel count in MODE 8 (OS units scaled by x_scale)."""
    screen_r = os_radius / x_scale
    return math.pi * screen_r * screen_r


def circle_screen_outline_bounds(os_radius: float, x_scale: float) -> Tuple[float, float]:
    """Approximate outline pixel count range for hollow CIRCLE."""
    screen_r = os_radius / x_scale
    circumference = 2.0 * math.pi * screen_r
    return circumference * 0.85, circumference * 1.25


def sum_slice_1d(values: Sequence[float], start: int, end: int) -> float:
    """BBC SUM(array(i TO j)) inclusive slice."""
    if end < start:
        start, end = end, start
    return float(sum(values[start : end + 1]))


def assert_matrix_almost(
    testcase,
    actual: Sequence[Sequence[float]],
    expected: Sequence[Sequence[float]],
    *,
    places: int = 6,
) -> None:
    testcase.assertEqual(len(actual), len(expected))
    for row, (a_row, e_row) in enumerate(zip(actual, expected)):
        testcase.assertEqual(len(a_row), len(e_row), f'row {row} width')
        for col, (a_val, e_val) in enumerate(zip(a_row, e_row)):
            testcase.assertAlmostEqual(
                float(a_val),
                float(e_val),
                places=places,
                msg=f'[{row},{col}]',
            )