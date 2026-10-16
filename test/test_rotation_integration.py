"""Rotation integration: --rpm sets deg/s; display --fps is independent."""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# benchmark_soccer_shared lives in scripts/
_SCRIPTS = os.path.join(_ROOT, 'scripts')
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import pytest

from benchmark_soccer_shared import (
    DEFAULT_RPM,
    FAST_RPM,
    advance_rotation,
    degrees_per_second_from_rpm,
    rpm_from_corpus_step,
    C_STEP_ORIGINAL_DEG,
    REFERENCE_REFRESH_HZ,
)

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def _degrees_per_second_from_rpm_loop(
    rpm: float,
    *,
    frames: int,
    frame_seconds: float,
) -> float:
    c_angle = 0.0
    for _ in range(frames):
        c_angle = advance_rotation(c_angle, frame_seconds, rpm=rpm)
    elapsed = frames * frame_seconds
    return c_angle / elapsed


def _old_per_frame_step(actual_fps: float) -> float:
    """Buggy model: C += step each displayed frame → deg/s = step × actual_fps."""
    return C_STEP_ORIGINAL_DEG * actual_fps


def test_default_rpm_matches_corpus() -> None:
    expected = rpm_from_corpus_step(C_STEP_ORIGINAL_DEG, refresh_hz=REFERENCE_REFRESH_HZ)
    assert abs(DEFAULT_RPM - expected) < 1e-12
    assert abs(degrees_per_second_from_rpm(DEFAULT_RPM) - 0.9) < 1e-12


def test_wall_clock_matches_rpm() -> None:
    for rpm in (DEFAULT_RPM, FAST_RPM, 1.0, 6.0):
        expected = degrees_per_second_from_rpm(rpm)
        got = _degrees_per_second_from_rpm_loop(
            rpm, frames=300, frame_seconds=1.0 / 60.0,
        )
        assert abs(got - expected) < 1e-9, (rpm, got, expected)


def test_rotation_independent_of_frame_interval() -> None:
    slow_frames = _degrees_per_second_from_rpm_loop(
        1.0, frames=60, frame_seconds=1.0 / 30.0,
    )
    fast_frames = _degrees_per_second_from_rpm_loop(
        1.0, frames=240, frame_seconds=1.0 / 120.0,
    )
    assert abs(slow_frames - fast_frames) < 1e-9
    assert abs(slow_frames - 6.0) < 1e-9


def test_per_frame_step_inverts_when_high_cap_lowers_actual_fps() -> None:
    high_cap_low_actual = _old_per_frame_step(actual_fps=20.0)
    low_cap_higher_actual = _old_per_frame_step(actual_fps=30.0)
    assert high_cap_low_actual < low_cap_higher_actual