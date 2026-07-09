"""Soccerball benchmark v2 — authentic BBC soccerball.bas (3D diagonal spin).

Uses the same matrix projection and PLOT 85 triangle pattern as soccerball.txt.
Lines and faces are clipped to the yellow disc by draw order (fill, then seams).

Run: python benchmark_soccer_v2.py
      python benchmark_soccer_v2.py --rpm 0.15
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import pygame

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from benchmark_soccer_shared import (  # noqa: E402
    C_STEP_ORIGINAL_DEG,
    DEFAULT_RPM,
    advance_rotation,
    compute_tmp,
    degrees_per_second_from_rpm,
    draw_soccerball_frame,
    load_soccerball_arrays,
    mode9_size,
    pace_frame,
    rpm_from_corpus_step,
)


def main() -> None:
    parser = argparse.ArgumentParser(description='BBC soccerball benchmark (authentic 3D)')
    parser.add_argument(
        '--rpm',
        type=float,
        default=DEFAULT_RPM,
        help=f'rotation speed (default {DEFAULT_RPM:g} = corpus C+=0.03 at 30Hz)',
    )
    parser.add_argument('--fps', type=int, default=30, help='target display FPS (0 = uncapped)')
    parser.add_argument('--scale', type=int, default=1, help='window scale factor')
    args = parser.parse_args()

    width, height = mode9_size()
    win_w = max(width, width * args.scale)
    win_h = max(height, height * args.scale)

    pygame.init()
    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption('Pure Python Soccerball Benchmark v2 (BBC 3D)')
    canvas = pygame.Surface((width, height))
    clock = pygame.time.Clock()

    xyz, b_mat = load_soccerball_arrays()
    c_angle = 0.0
    frame_count = 0
    fps_print = 0.0
    last_fps_time = time.monotonic()
    last_frame_time = last_fps_time

    print('BBC soccerball v2 (3D diagonal axis, corpus rotation).')
    print(f'RPM={args.rpm:g}  FPS target={args.fps}\n')

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        now = time.monotonic()
        dt = now - last_frame_time
        last_frame_time = now
        c_angle = advance_rotation(c_angle, dt, rpm=args.rpm)

        tmp = compute_tmp(xyz, b_mat, c_angle)
        draw_soccerball_frame(canvas, tmp, width=width, height=height)

        if win_w == width and win_h == height:
            scaled = canvas
        else:
            scaled = pygame.transform.scale(canvas, (win_w, win_h))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()

        pace_frame(clock, args.fps)
        frame_count += 1
        if now - last_fps_time >= 1.0:
            fps_print = frame_count / (now - last_fps_time)
            print(f'FPS: {fps_print:.1f}  C={c_angle:.2f}°')
            frame_count = 0
            last_fps_time = now

    pygame.quit()
    print(f'\nFinal FPS: {fps_print:.1f}')
    print(f'Corpus step equivalent: C += {C_STEP_ORIGINAL_DEG} at ~30 Hz ({rpm_from_corpus_step(C_STEP_ORIGINAL_DEG):.3g} RPM)')


if __name__ == '__main__':
    main()