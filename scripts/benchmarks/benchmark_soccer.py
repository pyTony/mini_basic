"""Fast soccerball benchmark — same pattern as soccerball.bas / benchmark_soccer_exact.

--fps caps display refresh only. --rpm sets full rotations per minute (wall-clock).

Run:
  python benchmark_soccer.py --rpm 0.15
      Corpus-like spin (C += 0.03 at ~30 Hz).
  python benchmark_soccer.py --rpm 2.5 --fast
      soccerball.bas workaround speed.
  python benchmark_soccer.py --fps 0 --vsync --rpm 1
      Smooth display; one rotation per minute.
"""
from __future__ import annotations

import argparse
import time

import pygame

from benchmark_soccer_shared import (
    DEFAULT_RPM,
    FAST_RPM,
    advance_rotation,
    compute_tmp,
    degrees_per_second_from_rpm,
    draw_soccerball_frame,
    load_soccerball_arrays,
    mode9_size,
    pace_frame,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Fast soccerball benchmark (same pattern as BASIC)',
    )
    parser.add_argument(
        '--fps',
        type=int,
        default=30,
        help='Display frame cap (0 = unlimited)',
    )
    parser.add_argument(
        '--rpm',
        type=float,
        default=DEFAULT_RPM,
        metavar='N',
        help=f'Full rotations per minute (default {DEFAULT_RPM:g}, corpus-like)',
    )
    parser.add_argument('--scale', type=int, default=1, help='Window scale')
    parser.add_argument(
        '--fast',
        action='store_true',
        help=f'Use {FAST_RPM:g} RPM (soccerball.bas workaround)',
    )
    parser.add_argument('--vsync', action='store_true', help='Sync to monitor (--fps 0)')
    args = parser.parse_args()
    fps_target = max(0, int(args.fps))
    scale = max(1, int(args.scale))
    rpm = FAST_RPM if args.fast else max(0.0, float(args.rpm))
    deg_per_s = degrees_per_second_from_rpm(rpm)

    width, height = mode9_size()
    win_w, win_h = width * scale, height * scale

    xyz, b_mat = load_soccerball_arrays()
    c_angle = 0.0

    pygame.init()
    if args.vsync:
        screen = pygame.display.set_mode((win_w, win_h), vsync=1)
    else:
        screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption('Soccerball fast benchmark (BASIC pattern)')
    clock = pygame.time.Clock()
    canvas = pygame.Surface((width, height))

    reported_fps = 0.0
    report_at = time.perf_counter()
    cap = 'unlimited' if fps_target <= 0 else str(fps_target)
    print(
        f'Target FPS: {cap}, rotation: {rpm:g} RPM ({deg_per_s:.2f}°/s)',
    )
    if fps_target <= 0 and not args.vsync:
        print('Tip: add --vsync so measured FPS matches the display.')
    print('ESC / close to quit.\n')

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
        pace_frame(clock, fps_target)

        now = time.perf_counter()
        c_angle = advance_rotation(c_angle, now - frame_start, rpm=rpm)
        frame_start = now
        if now - report_at >= 1.0:
            reported_fps = clock.get_fps()
            print(f'FPS: {reported_fps:.1f}')
            report_at = now

    pygame.quit()
    print(f'\nFinal FPS (measured): {reported_fps:.1f}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())