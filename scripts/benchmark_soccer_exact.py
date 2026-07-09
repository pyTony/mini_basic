"""Soccerball benchmark: fast live preview + exact BBCGraphics profiling.

Live default and benchmark_soccer.py share benchmark_soccer_shared.py
(same pattern as soccerball.bas). Use --profile for per-pixel call counts.

Usage:
  python benchmark_soccer_exact.py --fps 14 --rpm 2.5 --fast
  python benchmark_soccer_exact.py --exact --fps 14 --rpm 0.15
  python benchmark_soccer_exact.py --profile
  python benchmark_soccer_exact.py --verify
"""
from __future__ import annotations

import argparse
import cProfile
import io
import os
import pstats
import sys
import time
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from bbc_modes import bbc_mode_spec  # noqa: E402
from benchmark_soccer_shared import (  # noqa: E402
    CIRCLE_OS_RADIUS,
    C_STEP_FAST_DEG,
    C_STEP_ORIGINAL_DEG,
    DEFAULT_RPM,
    FAST_RPM,
    MODE9_ORIGIN,
    Z_CLIP,
    advance_rotation,
    compute_tmp,
    degrees_per_second_from_rpm,
    draw_soccerball_frame,
    load_soccerball_arrays,
    mode9_size,
    pace_frame,
)
from display import PygameDisplay  # noqa: E402
from test.bbc_expect import sum_slice_1d  # noqa: E402


def make_display(*, dummy: bool, scale: int) -> PygameDisplay:
    if dummy:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
    spec = bbc_mode_spec(9)
    assert spec is not None
    display = PygameDisplay(
        text_cols=spec.text_cols,
        text_rows=spec.text_rows,
        graphics_width=spec.gfx_width,
        graphics_height=spec.gfx_height,
        scale=scale,
        caption='soccerball exact benchmark',
        fps_limit=0,
    )
    display.begin_run()
    display.set_mode(9)
    display.set_graphics_origin(*MODE9_ORIGIN)
    display.set_colour(130)
    return display


def soccerball_frame_exact(display: PygameDisplay, xyz, b_mat, c_angle: float) -> None:
    """One REPEAT body via BBCGraphics (matches soccerball.bas GCOL 0)."""
    tmp = compute_tmp(xyz, b_mat, c_angle)
    display.mark_dirty()
    display.gcol(0, 3)
    display.move_absolute(0, 0)
    display.plot_code(156, CIRCLE_OS_RADIUS, 0)
    display.gcol(0, 0)

    index = 0
    for _j in range(12):
        z = sum_slice_1d(tmp[1], index, index + 4)
        for k in range(5):
            denom = 36 + tmp[1][index]
            x_os = int(3200 * tmp[0][index] / denom)
            y_os = int(3200 * tmp[2][index] / denom)
            if k < 2:
                display.move_absolute(x_os, y_os)
            elif z < Z_CLIP:
                display.plot_code(85, x_os, y_os)
            index += 1

    display.present()


def verify_against_interpreter() -> None:
    from mini_basic import BASICInterpreter, InterpreterConfig

    soccer = os.path.join(_ROOT, '..', 'examples', 'games', 'soccerball.bas')
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
    )
    interp.load(soccer, announce=False)
    for line_num in sorted(interp.program):
        upper = interp.program[line_num].strip().upper()
        if upper.startswith('REPEAT'):
            interp.program[line_num] = 'REM verify-once'
        elif upper.startswith('UNTIL'):
            interp.program[line_num] = 'END'
    with patch('time.sleep'):
        interp.run()
    ref_tmp = interp.array_storage[('TMP', 'float')][2]
    xyz, b_mat = load_soccerball_arrays()
    tmp = compute_tmp(xyz, b_mat, 0.0)
    for plane in range(3):
        for idx in range(60):
            expected = float(ref_tmp[plane][idx])
            got = tmp[plane][idx]
            if abs(expected - got) > 1e-6:
                raise SystemExit(
                    f'verify failed tmp({plane},{idx}): {got} != {expected}',
                )
    print('verify OK: 60-point TMP matches BASICInterpreter')


def run_profile(frames: int, *, dummy: bool, scale: int, c_step: float) -> None:
    xyz, b_mat = load_soccerball_arrays()
    display = make_display(dummy=dummy, scale=scale)
    c_angle = 0.0

    def _bench() -> None:
        nonlocal c_angle
        for _ in range(frames):
            soccerball_frame_exact(display, xyz, b_mat, c_angle)
            c_angle += c_step

    print(f'Profiling {frames} exact-path frames (dummy={dummy}, scale={scale})...')
    t0 = time.perf_counter()
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        _bench()
    finally:
        profiler.disable()
        display.end_run()
    elapsed = time.perf_counter() - t0
    fps = frames / elapsed if elapsed > 0 else 0.0
    print(f'\nExact path: {frames} frames in {elapsed:.3f}s  ({fps:.1f} FPS)\n')

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    print('=== Top 25 by cumulative time ===')
    stats.sort_stats('cumulative').print_stats(25)
    print(stream.getvalue())
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    print('=== Top 25 by call count ===')
    stats.sort_stats('calls').print_stats(25)
    print(stream.getvalue())

    gfx = display._gfx
    if gfx is not None:
        filled = sum(1 for row in gfx.pixels for px in row if px != 0)
        print(f'Non-zero pixels last frame: {filled}')
    per_frame = max(1, frames)
    print(
        f'\nPer-frame call budget (approx): '
        f'_put_pixel ~{1_659_896 // per_frame:,}, '
        f'plot_code ~{130 // per_frame}, '
        f'_fill_triangle ~{120 // per_frame}',
    )
    print(
        'Fast same-pattern preview: python benchmark_soccer.py --fps 14 --rpm 2.5 --fast',
    )


def run_live_fast(
    fps_limit: int,
    scale: int,
    rpm: float,
    *,
    vsync: bool,
) -> None:
    import pygame

    width, height = mode9_size()
    win_w, win_h = width * scale, height * scale
    xyz, b_mat = load_soccerball_arrays()
    c_angle = 0.0
    report_at = time.perf_counter()
    reported_fps = 0.0

    pygame.init()
    if vsync:
        screen = pygame.display.set_mode((win_w, win_h), vsync=1)
    else:
        screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption('Soccerball exact preview (fast draw)')
    clock = pygame.time.Clock()
    canvas = pygame.Surface((width, height))
    deg_per_s = degrees_per_second_from_rpm(rpm)
    cap = 'unlimited' if fps_limit <= 0 else str(fps_limit)
    print(
        f'Target FPS: {cap}, rotation: {rpm:g} RPM ({deg_per_s:.2f}°/s)',
    )
    if vsync:
        print('vsync on')
    if fps_limit <= 0 and not vsync:
        print('Tip: add --vsync so FPS matches what you see.')
    print('ESC / close window to quit.\n')

    running = True
    frame_start = time.perf_counter()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        tmp = compute_tmp(xyz, b_mat, c_angle)
        draw_soccerball_frame(canvas, tmp, width=width, height=height)
        if scale != 1:
            screen.blit(pygame.transform.scale(canvas, (win_w, win_h)), (0, 0))
        else:
            screen.blit(canvas, (0, 0))
        pygame.display.flip()
        pace_frame(clock, fps_limit)

        now = time.perf_counter()
        c_angle = advance_rotation(c_angle, now - frame_start, rpm=rpm)
        frame_start = now
        if now - report_at >= 1.0:
            reported_fps = clock.get_fps()
            print(f'FPS: {reported_fps:.1f}')
            report_at = now

    pygame.quit()
    print(f'\nFinal FPS (measured): {reported_fps:.1f}')


def run_live_exact(fps_limit: int, scale: int, rpm: float) -> None:
    xyz, b_mat = load_soccerball_arrays()
    display = make_display(dummy=False, scale=scale)
    display.fps_limit = fps_limit
    pygame_mod = display._pygame
    c_angle = 0.0
    frame_count = 0
    report_time = time.time()
    reported_fps = 0.0

    deg_per_s = degrees_per_second_from_rpm(rpm)
    cap = 'unlimited' if fps_limit <= 0 else str(fps_limit)
    print(
        f'BBCGraphics path (slow) — target FPS: {cap}, '
        f'rotation: {rpm:g} RPM ({deg_per_s:.2f}°/s)',
    )
    print('ESC / close window to quit.\n')
    running = True
    frame_start = time.perf_counter()
    while running:
        for event in pygame_mod.event.get():
            if event.type == pygame_mod.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame_mod.K_ESCAPE:
                running = False
        soccerball_frame_exact(display, xyz, b_mat, c_angle)
        now = time.perf_counter()
        c_angle = advance_rotation(c_angle, now - frame_start, rpm=rpm)
        frame_start = now
        frame_count += 1
        now = time.time()
        if now - report_time >= 1.0:
            reported_fps = frame_count
            print(f'FPS: {reported_fps}')
            frame_count = 0
            report_time = now

    display.end_run()
    print(f'\nFinal second FPS: {reported_fps}')


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Soccerball benchmark: fast preview + exact-path profiling',
    )
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--exact', action='store_true', help='Slow BBCGraphics live')
    parser.add_argument('--frames', type=int, default=60)
    parser.add_argument('--fps', type=int, default=30, help='Display frame cap (0 = unlimited)')
    parser.add_argument(
        '--rpm',
        type=float,
        default=DEFAULT_RPM,
        metavar='N',
        help=f'Full rotations per minute (default {DEFAULT_RPM:g})',
    )
    parser.add_argument('--scale', type=int, default=2)
    parser.add_argument('--dummy', action='store_true')
    parser.add_argument('--verify', action='store_true')
    parser.add_argument(
        '--step',
        type=float,
        default=C_STEP_ORIGINAL_DEG,
        metavar='DEG',
        help=f'Per-frame C step for --profile only (default {C_STEP_ORIGINAL_DEG})',
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help=f'Live: {FAST_RPM:g} RPM; --profile: step {C_STEP_FAST_DEG}',
    )
    parser.add_argument('--vsync', action='store_true', help='Sync flip to monitor')
    args = parser.parse_args()
    c_step = C_STEP_FAST_DEG if args.fast else max(0.0, float(args.step))
    rpm = FAST_RPM if args.fast else max(0.0, float(args.rpm))

    if args.verify:
        verify_against_interpreter()
        return 0
    if args.profile:
        run_profile(
            max(1, args.frames),
            dummy=args.dummy or True,
            scale=args.scale,
            c_step=c_step,
        )
        return 0
    if args.exact:
        run_live_exact(args.fps, args.scale, rpm)
    else:
        run_live_fast(args.fps, args.scale, rpm, vsync=args.vsync)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())