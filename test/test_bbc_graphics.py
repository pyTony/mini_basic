import os
import sys
import unittest

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# benchmark_soccer_shared lives in scripts/
_SCRIPTS = os.path.join(_ROOT, 'scripts')
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from mini_basic.bbc_graphics import BBCGraphics, apply_gcol

# Pure framebuffer math — no pygame window; safe in phase1 non-gfx runs.
pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]



class BBCGraphicsTests(unittest.TestCase):
    def test_gcol_modes(self):
        self.assertEqual(apply_gcol(0, 7, 0), 7)
        self.assertEqual(apply_gcol(3, 5, 3), 6)

    def test_move_and_point_plot(self):
        gfx = BBCGraphics(64, 64)
        gfx.gcol(0, 2)
        gfx.move_absolute(10, 10)
        gfx.plot_code(69, 20, 20)
        colour = gfx.point_colour(20, 20)
        self.assertEqual(colour, 2)

    def test_dirty_rect_tracks_plots_and_skips_same_ink(self):
        """Present path uses dirty rect patches; same-ink rewrite is free."""
        gfx = BBCGraphics(64, 64, x_scale=1, y_scale=1)
        gfx.gcol(0, 2)
        gfx.plot_code(69, 10, 10)
        gfx.plot_code(69, 40, 30)
        rect = gfx.peek_dirty_rect()
        self.assertIsNotNone(rect)
        x0, y0, x1, y1 = rect
        self.assertLessEqual(x0, x1)
        self.assertLessEqual(y0, y1)
        self.assertGreaterEqual(gfx.plot_count, 2)
        taken = gfx.consume_dirty_rect()
        self.assertEqual(taken, rect)
        self.assertIsNone(gfx.peek_dirty_rect())
        self.assertEqual(gfx.plot_count, 0)
        # Mode-0 same colour again: no dirty expansion
        gfx.plot_code(69, 10, 10)
        self.assertIsNone(gfx.peek_dirty_rect())

    def test_relative_draw(self):
        gfx = BBCGraphics(64, 64)
        gfx.gcol(0, 3)
        gfx.move_absolute(5, 5)
        gfx.draw_relative(10, 0)
        self.assertEqual(gfx.point_colour(15, 5), 3)

    def test_filled_rectangle(self):
        gfx = BBCGraphics(64, 64)
        gfx.gcol(0, 4)
        gfx.move_absolute(10, 10)
        gfx.plot_code(101, 20, 20)
        self.assertEqual(gfx.point_colour(15, 15), 4)

    def test_fill_rectangle_gcol0_block(self):
        """Mandelbrot-style RECTANGLE FILL uses a block write, not per-pixel plots."""
        gfx = BBCGraphics(64, 64, x_scale=1, y_scale=1)
        gfx.gcol(0, 5)
        gfx.fill_rectangle(8, 8, 8, 8)
        self.assertEqual(gfx.point_colour(8, 8), 5)
        self.assertEqual(gfx.point_colour(15, 15), 5)
        self.assertEqual(gfx.point_colour(16, 16), 5)
        self.assertEqual(gfx.point_colour(17, 17), 0)
        self.assertGreaterEqual(gfx.plot_count, 64)

    def test_plot_181_filled_triangle_absolute(self):
        gfx = BBCGraphics(320, 256, x_scale=4, y_scale=4)
        gfx.gcol(0, 1)
        gfx.move_absolute(100, 0)
        gfx.move_absolute(0, 100)
        gfx.plot_code(181, 0, 0)
        filled = sum(1 for row in gfx.pixels for colour in row if colour == 1)
        self.assertGreater(filled, 50)

    def test_plot_181_pie_sector_fills_beyond_chord(self):
        """Centre+two equal-radius rims tessellate arc (piechart vs chord triangle)."""
        import math

        gfx = BBCGraphics(640, 512, x_scale=2, y_scale=2)
        gfx.gcol(0, 1)
        cx, cy, r = 640, 512, 300
        a0, a1 = 0.0, 2.0  # ~115° slice
        gfx.move_absolute(cx, cy)
        gfx.move_absolute(
            int(cx + r * math.cos(a0)),
            int(cy + r * math.sin(a0)),
        )
        gfx.plot_code(
            181,
            int(cx + r * math.cos(a1)),
            int(cy + r * math.sin(a1)),
        )
        filled = sum(1 for row in gfx.pixels for colour in row if colour == 1)
        # Chord-only triangle is ~half the sector area; sector path is larger.
        self.assertGreater(filled, 8000)

    def test_circle_fill_clip_blocks_false_sector_bulge(self):
        """Soccerball: after CIRCLE FILL, PLOT 85 must not sector-bulge outside disc."""
        import math

        from mini_basic.bbc_graphics import pixel_inside_disc_ellipse

        gfx = BBCGraphics(640, 512, x_scale=2, y_scale=2)
        gfx.set_origin(640, 512)
        gfx.gcol(0, 2)
        gfx.clear_graphics(2)  # green field (not black — black is ink under test)
        gfx.gcol(0, 3)
        gfx.move_absolute(0, 0)
        # CIRCLE FILL: plot group 0x98 + absolute last point → radius via hypot
        gfx.plot_code(0x99, 432, 0)
        self.assertIsNotNone(gfx._clip_disc)
        # Near-equal rims about a non-centre vertex (false pie sector).
        gfx.gcol(0, 0)
        r = 200
        pts = [
            (int(r * math.cos(a)), int(r * math.sin(a)))
            for a in (0.2, 0.2 + 2.1, 0.2 + 4.2)
        ]
        gfx.move_absolute(*pts[0])
        gfx.move_absolute(*pts[1])
        gfx.plot_code(85, pts[2][0], pts[2][1])
        scx, scy, srx, sry = gfx._clip_disc
        outside = 0
        for sy, row in enumerate(gfx.pixels):
            for sx, col in enumerate(row):
                if int(col) != 0:
                    continue
                if not pixel_inside_disc_ellipse(sx, sy, scx, scy, srx, sry):
                    outside += 1
        self.assertEqual(outside, 0)

    def test_filled_triangle_flat_base(self):
        gfx = BBCGraphics(320, 256, x_scale=4, y_scale=4)
        gfx.gcol(0, 1)
        gfx.move_absolute(-200, -200)
        gfx.move_absolute(200, -200)
        gfx.plot_code(85, 200, 200)
        filled = sum(1 for row in gfx.pixels for colour in row if colour == 1)
        self.assertGreater(filled, 200)

    def test_mode1_user_zero_is_bottom_left_by_default(self):
        gfx = BBCGraphics(320, 256, x_scale=4, y_scale=4)
        self.assertEqual(gfx._to_screen(0, 0), (0, 255))

    def test_origin_places_user_zero_at_absolute_os_point(self):
        gfx = BBCGraphics(320, 256, x_scale=4, y_scale=4)
        gfx.set_origin(640, 512)
        self.assertEqual(gfx._to_screen(0, 0), (160, 127))

    def test_mode1_draw_relative_from_origin_anchor(self):
        gfx = BBCGraphics(320, 256, x_scale=4, y_scale=4)
        gfx.set_origin(160, 128)
        gfx.gcol(0, 1)
        gfx.move_absolute(0, 0)
        gfx.draw_relative(200, 0)
        gfx.draw_relative(0, 150)
        self.assertEqual(gfx.point_colour(0, 0), 1)
        self.assertEqual(gfx.point_colour(200, 0), 1)
        self.assertEqual(gfx.point_colour(200, 150), 1)
        sx, sy = gfx._to_screen(200, 0)
        self.assertEqual(gfx.pixels[sy][sx], 1)
        sx, sy = gfx._to_screen(200, 150)
        self.assertEqual(gfx.pixels[sy][sx], 1)

    def test_gcol_xor_mode_erases_foreground_plot(self):
        gfx = BBCGraphics(64, 64)
        gfx.gcol(0, 3)
        gfx.move_absolute(10, 10)
        gfx.plot_code(69, 20, 20)
        self.assertEqual(gfx.point_colour(20, 20), 3)
        gfx.gcol(3, 3)
        gfx.plot_code(69, 20, 20)
        self.assertEqual(gfx.point_colour(20, 20), 0)

    def test_circle_fill_sets_disc_clip_for_later_triangles(self):
        """PLOT 85 past the disc edge must fill to the silhouette, not leave yellow gaps."""
        gfx = BBCGraphics(320, 256, x_scale=4, y_scale=4)
        gfx.set_origin(640, 512)
        gfx.gcol(0, 3)
        gfx.move_absolute(0, 0)
        gfx.plot_code(156, 0, 432)
        gfx.gcol(0, 0)
        # Apex above the disc; base chord crosses the upper silhouette.
        gfx.move_absolute(-400, 200)
        gfx.move_absolute(400, 200)
        gfx.plot_code(85, 0, 600)
        cx, cy = gfx._to_screen(0, 0)
        scx, scy, srx, sry = gfx._clip_disc
        self.assertIsNotNone(gfx._clip_disc)
        top_sy = scy - sry
        self.assertEqual(gfx.pixels[top_sy][scx], 0)
        self.assertEqual(gfx.pixels[top_sy][max(0, scx - 4)], 0)
        self.assertEqual(gfx.pixels[top_sy][min(gfx.width - 1, scx + 4)], 0)


    def test_benchmark_disc_matches_bbc_circle_fill(self):
        """pygame.draw.circle overshoots BBC CIRCLE FILL; benchmark must not use it."""
        import pygame

        from benchmark_soccer_shared import (
            fill_disc_surface,
            mode9_size,
            os_to_screen,
            CIRCLE_OS_RADIUS,
            YELLOW,
            BLACK,
        )
        from mini_basic.bbc_graphics import disc_screen_radii
        from mini_basic.bbc_modes import bbc_os_scales

        pygame.init()
        width, height = mode9_size()
        x_scale, y_scale = bbc_os_scales(width, height)
        cx, cy = os_to_screen(0, 0, width=width, height=height)
        srx, sry = disc_screen_radii(CIRCLE_OS_RADIUS, x_scale, y_scale)

        gfx = BBCGraphics(width, height, x_scale=x_scale, y_scale=y_scale)
        gfx.set_origin(640, 512)
        gfx.gcol(0, 3)
        gfx.move_absolute(0, 0)
        gfx.plot_code(156, 0, CIRCLE_OS_RADIUS)

        bench = pygame.Surface((width, height))
        bench.fill(BLACK)
        fill_disc_surface(bench, YELLOW, cx, cy, srx, sry)

        extra = 0
        for y in range(height):
            for x in range(width):
                if bench.get_at((x, y))[:3] == YELLOW and gfx.pixels[y][x] != 3:
                    extra += 1
        self.assertEqual(extra, 0)

    def test_soccerball_top_pentagon_covers_disc_rim_at_rest(self):
        """Vertex clipping left yellow at the silhouette; pixel disc mask must not."""
        import pygame

        from benchmark_soccer_shared import (
            compute_tmp,
            draw_soccerball_frame,
            load_soccerball_arrays,
            mode9_size,
            plot85_triangles_for_face,
            Z_CLIP,
            _project_index,
            YELLOW,
        )
        from test.bbc_expect import sum_slice_1d

        def pip(x, y, tri):
            (x0, y0), (x1, y1), (x2, y2) = tri
            a = (y1 - y0) * (x - x0) - (x1 - x0) * (y - y0)
            b = (y2 - y1) * (x - x1) - (x2 - x1) * (y - y1)
            c = (y0 - y2) * (x - x2) - (x0 - x2) * (y - y2)
            return (a >= 0 and b >= 0 and c >= 0) or (a <= 0 and b <= 0 and c <= 0)

        pygame.init()
        width, height = mode9_size()
        xyz, b_mat = load_soccerball_arrays()
        tmp = compute_tmp(xyz, b_mat, 0.0)
        surface = pygame.Surface((width, height))
        draw_soccerball_frame(surface, tmp, width=width, height=height)

        index = 10
        pts = [_project_index(tmp, index + k, width=width, height=height) for k in range(5)]
        tris = plot85_triangles_for_face(pts)
        leaks = [
            (x, y)
            for y in range(height)
            for x in range(width)
            if any(pip(x, y, tri) for tri in tris)
            and surface.get_at((x, y))[:3] == YELLOW
        ]
        self.assertEqual(leaks, [])


if __name__ == '__main__':
    unittest.main()
