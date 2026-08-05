"""BBC BASIC / Agon-style graphics (PLOT codes, GCOL, MOVE, DRAW)."""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple, Union

RGB = Tuple[int, int, int]

GColState = Tuple[int, int]  # (mode, colour)


def disc_screen_radii(
    os_radius: float,
    x_scale: int,
    y_scale: int,
) -> Tuple[int, int]:
    """BBC CIRCLE FILL screen radii (ellipse axes in pixels)."""
    return (
        max(1, int(round(os_radius / max(1, x_scale)))),
        max(1, int(round(os_radius / max(1, y_scale)))),
    )


def pixel_inside_disc_ellipse(
    sx: int,
    sy: int,
    scx: int,
    scy: int,
    srx: int,
    sry: int,
    *,
    margin: float = 1.0001,
) -> bool:
    """True when (sx, sy) lies inside the BBC disc silhouette."""
    if srx <= 0 or sry <= 0:
        return False
    dx = (float(sx) - float(scx)) / float(srx)
    dy = (float(sy) - float(scy)) / float(sry)
    return (dx * dx) + (dy * dy) <= margin


def apply_gcol(old_colour: int, new_colour: int, mode: int) -> int:
    old = int(old_colour) & 0xFF
    new = int(new_colour) & 0xFF
    if mode == 0:
        return new
    if mode == 1:
        return old | new
    if mode == 2:
        return old & new
    if mode == 3:
        return old ^ new
    if mode == 4:
        # Logical inverse of existing colour (PLOT 2/6). Beeb-style 8-colour
        # invert — not XOR 0xFF (that produced near-invisible high indices).
        return old ^ 0x07
    if mode == 5:
        return old
    if mode == 6:
        return old & (new ^ 0xFF)
    if mode == 7:
        return old | (new ^ 0xFF)
    return new


def _try_numpy():
    try:
        import numpy as np  # type: ignore
        return np
    except ImportError:
        return None


class BBCGraphics:
    """Low-resolution framebuffer with BBC PLOT semantics.

    Pixel store is a numpy ``uint8`` array when numpy is available (fast present
    path); otherwise nested Python lists. Plotting updates a dirty rectangle so
    the display can blit patches instead of re-uploading the full frame every
    present during dense PLOT loops (saucer, etc.).
    """

    def __init__(
        self,
        width: int,
        height: int,
        *,
        x_scale: int = 1,
        y_scale: int = 1,
    ) -> None:
        self.width = width
        self.height = height
        self.x_scale = max(1, int(x_scale))
        self.y_scale = max(1, int(y_scale))
        self.origin_x = 0
        self.origin_y = 0
        self.cursor_x = 0
        self.cursor_y = 0
        self.stack: List[Tuple[int, int]] = []
        self.gcol_fg: GColState = (0, 7)
        self.gcol_bg: GColState = (0, 0)
        self._np = _try_numpy()
        self.pixels = self._alloc_pixels(width, height, fill=0)
        self.rgb_pixels: List[List[Optional[RGB]]] = [
            [None for _ in range(width)] for _ in range(height)
        ]
        self.rgb_dirty: set[Tuple[int, int]] = set()  # (sx, sy) with non-None rgb_pixels entry
        self._truecolour_rgb: Optional[RGB] = None
        # Optional screen-space ellipse clip (scx, scy, srx, sry) from last CIRCLE FILL.
        self._clip_disc: Optional[Tuple[int, int, int, int]] = None
        # Inclusive dirty rect in screen pixels; None = clean.
        self._dirty_rect: Optional[Tuple[int, int, int, int]] = None
        self.plot_count = 0  # pixels written since last consume (for present coalescing)
        # VDU 24 graphics window in absolute OS units (bottom-left origin), or None = full.
        self._viewport_os: Optional[Tuple[int, int, int, int]] = None

    def _alloc_pixels(self, width: int, height: int, fill: int = 0):
        fill_b = int(fill) & 0xFF
        if self._np is not None:
            arr = self._np.zeros((height, width), dtype=self._np.uint8)
            if fill_b:
                arr.fill(fill_b)
            return arr
        return [[fill_b for _ in range(width)] for _ in range(height)]

    @property
    def pixels_is_numpy(self) -> bool:
        return self._np is not None and not isinstance(self.pixels, list)

    def mark_full_dirty(self) -> None:
        if self.width <= 0 or self.height <= 0:
            self._dirty_rect = None
            return
        self._dirty_rect = (0, 0, self.width - 1, self.height - 1)

    def _mark_pixel_dirty(self, sx: int, sy: int) -> None:
        if self._dirty_rect is None:
            self._dirty_rect = (sx, sy, sx, sy)
            return
        x0, y0, x1, y1 = self._dirty_rect
        if sx < x0:
            x0 = sx
        if sy < y0:
            y0 = sy
        if sx > x1:
            x1 = sx
        if sy > y1:
            y1 = sy
        self._dirty_rect = (x0, y0, x1, y1)

    def consume_dirty_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """Return and clear the dirty rectangle (inclusive x0,y0,x1,y1)."""
        rect = self._dirty_rect
        self._dirty_rect = None
        self.plot_count = 0
        return rect

    def peek_dirty_rect(self) -> Optional[Tuple[int, int, int, int]]:
        return self._dirty_rect

    def set_graphics_viewport(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """VDU 24 — graphics window in absolute OS units (screen bottom-left)."""
        xa, xb = int(x1), int(x2)
        ya, yb = int(y1), int(y2)
        self._viewport_os = (min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb))

    def clear_graphics_viewport(self) -> None:
        """VDU 26 — restore full-screen graphics window."""
        self._viewport_os = None

    def _absolute_os_to_screen(self, abs_x: int, abs_y: int) -> Tuple[int, int]:
        """Map absolute OS coords (ignore ORIGIN) to framebuffer pixels."""
        sx = int(abs_x) // max(1, self.x_scale)
        sy = self.height - 1 - int(abs_y) // max(1, self.y_scale)
        return sx, sy

    def clear_graphics(self, bg_colour: int | None = None) -> None:
        """CLG / VDU 16 — fill graphics window (or full screen) with GCOL background.

        welcome.bbc draws the red frame by CLG red in a large VDU 24 window, then
        CLG gray in a smaller window — must not wipe the outer border.
        """
        self._clip_disc = None
        bg = self.gcol_bg[1] if bg_colour is None else int(bg_colour)
        bg_b = int(bg) & 0xFF
        if self._viewport_os is None:
            if self.pixels_is_numpy:
                self.pixels.fill(bg_b)
                # rgb overrides: cheap full clear
                for y in range(self.height):
                    rgb_row = self.rgb_pixels[y]
                    for x in range(self.width):
                        rgb_row[x] = None
            else:
                for y, row in enumerate(self.pixels):
                    rgb_row = self.rgb_pixels[y]
                    for x in range(self.width):
                        row[x] = bg_b
                        rgb_row[x] = None
            self.rgb_dirty.clear()
            self.mark_full_dirty()
            self.plot_count = 0
            return

        x1, y1, x2, y2 = self._viewport_os
        # Inclusive OS box → screen; clamp to framebuffer.
        corners = [
            self._absolute_os_to_screen(x1, y1),
            self._absolute_os_to_screen(x1, y2),
            self._absolute_os_to_screen(x2, y1),
            self._absolute_os_to_screen(x2, y2),
        ]
        sxs = [c[0] for c in corners]
        sys_ = [c[1] for c in corners]
        sx0 = max(0, min(sxs))
        sx1 = min(self.width - 1, max(sxs))
        sy0 = max(0, min(sys_))
        sy1 = min(self.height - 1, max(sys_))
        if sx0 > sx1 or sy0 > sy1:
            return
        if self.pixels_is_numpy:
            self.pixels[sy0 : sy1 + 1, sx0 : sx1 + 1] = bg_b
        else:
            for sy in range(sy0, sy1 + 1):
                row = self.pixels[sy]
                rgb_row = self.rgb_pixels[sy]
                for sx in range(sx0, sx1 + 1):
                    row[sx] = bg_b
                    rgb_row[sx] = None
        # Drop rgb_dirty points inside the cleared rect
        if self.rgb_dirty:
            self.rgb_dirty = {
                (sx, sy)
                for sx, sy in self.rgb_dirty
                if not (sx0 <= sx <= sx1 and sy0 <= sy <= sy1)
            }
        if self._dirty_rect is None:
            self._dirty_rect = (sx0, sy0, sx1, sy1)
        else:
            dx0, dy0, dx1, dy1 = self._dirty_rect
            self._dirty_rect = (
                min(dx0, sx0),
                min(dy0, sy0),
                max(dx1, sx1),
                max(dy1, sy1),
            )
        self.plot_count += (sx1 - sx0 + 1) * (sy1 - sy0 + 1)

    def set_truecolour(self, rgb: Optional[RGB]) -> None:
        if rgb is None:
            self._truecolour_rgb = None
            return
        self._truecolour_rgb = (
            max(0, min(255, int(rgb[0]))),
            max(0, min(255, int(rgb[1]))),
            max(0, min(255, int(rgb[2]))),
        )

    def clear_truecolour(self) -> None:
        self._truecolour_rgb = None

    def set_origin(self, x: int, y: int) -> None:
        self.origin_x = int(x)
        self.origin_y = int(y)

    def gcol(self, mode: int, colour: int) -> None:
        colour = int(colour)
        if colour >= 128:
            self.gcol_bg = (int(mode), colour - 128)
        else:
            self.gcol_fg = (int(mode), colour)

    def point_colour(self, x: int, y: int) -> int:
        sx, sy = self._to_screen(x, y)
        if 0 <= sx < self.width and 0 <= sy < self.height:
            return self.pixels[sy][sx]
        return 0

    def move_absolute(self, x: int, y: int) -> None:
        self._push_cursor()
        self.cursor_x = int(x)
        self.cursor_y = int(y)

    def move_relative(self, dx: int, dy: int) -> None:
        self._push_cursor()
        self.cursor_x += int(dx)
        self.cursor_y += int(dy)

    def fill_rectangle(self, x: int, y: int, width: int, height: int) -> None:
        """Fill axis-aligned rect in OS units by painting each *screen* pixel once.

        Iterating OS units under scale>1 rewrote the same pixels many times and
        made Mandelbrot-style block fills unusably slow (and easy to time out).
        """
        gcol = self.gcol_fg
        x0, y0 = int(x), int(y)
        x1, y1 = x0 + int(width), y0 + int(height)
        corners = (
            self._to_screen(x0, y0),
            self._to_screen(x1, y0),
            self._to_screen(x0, y1),
            self._to_screen(x1, y1),
        )
        sxs = [c[0] for c in corners]
        sys_ = [c[1] for c in corners]
        left, right = min(sxs), max(sxs)
        top, bottom = min(sys_), max(sys_)
        # Inclusive OS range maps to inclusive screen bounds; clamp to FB.
        left = max(0, left)
        top = max(0, top)
        right = min(self.width - 1, right)
        bottom = min(self.height - 1, bottom)
        if left > right or top > bottom:
            return
        for sy in range(top, bottom + 1):
            for sx in range(left, right + 1):
                self._put_screen_pixel(sx, sy, gcol)

    def draw_relative(self, dx: int, dy: int) -> None:
        self.plot_code(1, int(dx), int(dy))

    def draw_absolute(self, x: int, y: int) -> None:
        """DRAW x,y — equivalent to PLOT 5 (absolute line to point)."""
        self.plot_code(5, int(x), int(y))

    def plot_code(self, code: int, x: int, y: int) -> None:
        code = int(code) & 0xFF
        sub = code & 7
        op = code & 0xF8
        relative = sub < 4
        tx = self.cursor_x + x if relative else int(x)
        ty = self.cursor_y + y if relative else int(y)

        self._push_cursor()

        if op == 0x00:
            self._line(code, tx, ty)
        elif op == 0x40:
            self._point(code, tx, ty)
        elif op in (0x50, 0xB0):
            self._triangle(code, tx, ty)
        elif op == 0xA0:
            self._triangle_outline(code, tx, ty)
        elif op == 0x60:
            self._rectangle(code, tx, ty)
        elif op == 0x90:
            self._circle(code, tx, ty, filled=False)
        elif op == 0x98:
            self._circle(code, tx, ty, filled=True)
        elif sub in (0, 4):
            pass
        else:
            self._line(code, tx, ty)

        self.cursor_x = tx
        self.cursor_y = ty

    def _push_cursor(self) -> None:
        self.stack.append((self.cursor_x, self.cursor_y))
        if len(self.stack) > 8:
            self.stack.pop(0)

    def _stack_point(self, index: int) -> Tuple[int, int]:
        if not self.stack:
            return (self.cursor_x, self.cursor_y)
        return self.stack[index]

    def _plot_subcolour(self, sub: int) -> Tuple[GColState, bool]:
        if sub in (2, 6):
            return ((4, 0), False)
        if sub in (3, 7):
            return (self.gcol_bg, True)
        return (self.gcol_fg, False)

    def _put_screen_pixel(self, sx: int, sy: int, gcol: GColState) -> None:
        if not (0 <= sx < self.width and 0 <= sy < self.height):
            return
        clip = self._clip_disc
        if clip is not None:
            scx, scy, srx, sry = clip
            if not pixel_inside_disc_ellipse(sx, sy, scx, scy, srx, sry):
                return
        mode, colour = gcol
        old = int(self.pixels[sy][sx])
        new = apply_gcol(old, colour, mode)
        if new == old and mode == 0 and self._truecolour_rgb is None:
            # No visible change — skip dirty bookkeeping (hidden-line / redraw same ink).
            return
        self.pixels[sy][sx] = new
        self._mark_pixel_dirty(sx, sy)
        self.plot_count += 1
        if self._truecolour_rgb is not None and new != 0:
            self.rgb_pixels[sy][sx] = self._truecolour_rgb
            self.rgb_dirty.add((sx, sy))
        else:
            # Drop DISPLAY/truecolour overrides so palette GCOL (incl. XOR mode 3
            # VDU 5 labels on piechart) is what present() shows.
            self.rgb_pixels[sy][sx] = None
            self.rgb_dirty.discard((sx, sy))

    def _put_pixel(self, x: int, y: int, gcol: GColState) -> None:
        sx, sy = self._to_screen(x, y)
        self._put_screen_pixel(sx, sy, gcol)

    def put_truecolour_point_os(self, x: int, y: int, rgb: RGB, colour: int = 7) -> None:
        """Fast absolute point with truecolour RGB (squares.bbc-style pixel fill)."""
        sx, sy = self._to_screen(int(x), int(y))
        if not (0 <= sx < self.width and 0 <= sy < self.height):
            return
        clip = self._clip_disc
        if clip is not None:
            scx, scy, srx, sry = clip
            if not pixel_inside_disc_ellipse(sx, sy, scx, scy, srx, sry):
                return
        self.pixels[sy][sx] = int(colour) & 0xFF
        self.rgb_pixels[sy][sx] = (
            int(rgb[0]) & 0xFF,
            int(rgb[1]) & 0xFF,
            int(rgb[2]) & 0xFF,
        )
        self._mark_pixel_dirty(sx, sy)
        self.rgb_dirty.add((sx, sy))
        self.plot_count += 1
        self.cursor_x = int(x)
        self.cursor_y = int(y)

    def _to_screen(self, x: int, y: int) -> Tuple[int, int]:
        """Map user graphics coords to framebuffer pixels (BB4W/SDL semantics).

        Absolute OS coordinates use (0, 0) at the bottom-left of the screen.
        ORIGIN X,Y places user coordinate (0, 0) at absolute position (X, Y).
        """
        abs_x = self.origin_x + int(x)
        abs_y = self.origin_y + int(y)
        sx = abs_x // self.x_scale
        sy = self.height - 1 - abs_y // self.y_scale
        return sx, sy

    def from_screen(self, sx: int, sy: int) -> Tuple[int, int]:
        """Inverse of _to_screen (graphics units, relative to current ORIGIN)."""
        abs_x = int(sx) * self.x_scale
        abs_y = (self.height - 1 - int(sy)) * self.y_scale
        return abs_x - self.origin_x, abs_y - self.origin_y

    def _from_screen(self, sx: int, sy: int) -> Tuple[int, int]:
        return self.from_screen(sx, sy)

    def _point(self, code: int, x: int, y: int) -> None:
        sub = code & 7
        if sub in (0, 4):
            return
        gcol, _ = self._plot_subcolour(sub)
        self._put_pixel(x, y, gcol)

    def _line(self, code: int, x1: int, y1: int) -> None:
        sub = code & 7
        if sub in (0, 4):
            return
        x0, y0 = self._stack_point(-1)
        gcol, _ = self._plot_subcolour(sub)
        self._bresenham_line(x0, y0, x1, y1, gcol)

    def _bresenham_line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        gcol: GColState,
    ) -> None:
        # Iterate in screen pixels so scaled OS units do not XOR the same pixel twice.
        sx0, sy0 = self._to_screen(x0, y0)
        sx1, sy1 = self._to_screen(x1, y1)
        dx = abs(sx1 - sx0)
        dy = -abs(sy1 - sy0)
        sx_step = 1 if sx0 < sx1 else -1
        sy_step = 1 if sy0 < sy1 else -1
        err = dx + dy
        sx, sy = sx0, sy0
        while True:
            self._put_screen_pixel(sx, sy, gcol)
            if sx == sx1 and sy == sy1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                sx += sx_step
            if e2 <= dx:
                err += dx
                sy += sy_step

    def _triangle(self, code: int, x2: int, y2: int) -> None:
        if len(self.stack) < 2:
            return
        x0, y0 = self.stack[-2]
        x1, y1 = self.stack[-1]
        gcol, _ = self._plot_subcolour(code & 7)
        self._fill_triangle(x0, y0, x1, y1, x2, y2, gcol)

    def _triangle_outline(self, code: int, x2: int, y2: int) -> None:
        if len(self.stack) < 2:
            return
        x0, y0 = self.stack[-2]
        x1, y1 = self.stack[-1]
        gcol, _ = self._plot_subcolour(code & 7)
        self._bresenham_line(x0, y0, x1, y1, gcol)
        self._bresenham_line(x1, y1, x2, y2, gcol)
        self._bresenham_line(x2, y2, x0, y0, gcol)

    def _rectangle(self, code: int, x1: int, y1: int) -> None:
        if len(self.stack) < 1:
            return
        x0, y0 = self.stack[-1]
        gcol, _ = self._plot_subcolour(code & 7)
        left = min(x0, x1)
        right = max(x0, x1)
        top = max(y0, y1)
        bottom = min(y0, y1)
        for y in range(bottom, top + 1):
            for x in range(left, right + 1):
                self._put_pixel(x, y, gcol)

    def _circle(self, code: int, x1: int, y1: int, *, filled: bool) -> None:
        if len(self.stack) < 1:
            return
        cx, cy = self.stack[-1]
        radius = int(round(math.hypot(x1 - cx, y1 - cy)))
        gcol, _ = self._plot_subcolour(code & 7)
        mode, colour = gcol
        if filled:
            # Scanline fill in screen coordinates — avoids per-pixel _to_screen calls.
            scx, scy = self._to_screen(cx, cy)
            srx, sry = disc_screen_radii(radius, self.x_scale, self.y_scale)
            h, w = self.height, self.width
            for spy in range(max(0, scy - sry), min(h, scy + sry + 1)):
                dy = spy - scy
                if abs(dy) > sry:
                    continue
                half_x = int(
                    math.sqrt(max(0.0, float(srx * srx * (1.0 - (dy / sry) ** 2))))
                )
                x0 = max(0, scx - half_x)
                x1s = min(w, scx + half_x + 1)
                row = self.pixels[spy]
                rgb_row = self.rgb_pixels[spy]
                trgb = self._truecolour_rgb
                if mode == 0:
                    for sx in range(x0, x1s):
                        row[sx] = colour
                        if trgb is not None and colour != 0:
                            rgb_row[sx] = trgb
                            self.rgb_dirty.add((sx, spy))
                        elif colour == 0:
                            rgb_row[sx] = None
                            self.rgb_dirty.discard((sx, spy))
                else:
                    for sx in range(x0, x1s):
                        row[sx] = apply_gcol(int(row[sx]), colour, mode)
                        if trgb is not None and int(row[sx]) != 0:
                            rgb_row[sx] = trgb
                            self.rgb_dirty.add((sx, spy))
                if x1s > x0:
                    self._mark_pixel_dirty(x0, spy)
                    self._mark_pixel_dirty(x1s - 1, spy)
                    self.plot_count += x1s - x0

            # Clip later PLOT fills to the disc silhouette (pixel mask, not vertex pull-in).
            self._clip_disc = (scx, scy, srx, sry)
        else:
            if radius <= 0:
                self._put_pixel(cx, cy, gcol)
                return
            x = 0
            y = radius
            d = 3 - 2 * radius
            points = set()
            def octants(px: int, py: int) -> None:
                for ox, oy in (
                    (px, py), (-px, py), (px, -py), (-px, -py),
                    (py, px), (-py, px), (py, -px), (-py, -px),
                ):
                    points.add((cx + ox, cy + oy))
            while x <= y:
                octants(x, y)
                if d < 0:
                    d += 4 * x + 6
                else:
                    d += 4 * (x - y) + 10
                    y -= 1
                x += 1
            for px, py in points:
                self._put_pixel(px, py, gcol)

    def _fill_triangle(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        gcol: GColState,
    ) -> None:
        """Filled PLOT 85/181 — rasterise in screen pixels to avoid OS-scale gaps.

        Pie-chart sectors (BBCSDL piechart.bbc): MOVE centre; MOVE rim A; PLOT 181 rim B
        is a single chord triangle. With a few large slices that looks like a
        polygon, not a pie. When A and B lie on a common radius from the first
        point, tessellate the arc so the filled region matches a circular sector.
        """
        if self._fill_circular_sector_os(x0, y0, x1, y1, x2, y2, gcol):
            return
        pts = [
            self._to_screen(x0, y0),
            self._to_screen(x1, y1),
            self._to_screen(x2, y2),
        ]
        self._fill_triangle_screen(pts, gcol)

    def _fill_circular_sector_os(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        gcol: GColState,
    ) -> bool:
        """If (x0,y0) is centre and rims share radius, fill a circular sector.

        Returns True when the sector path handled the fill.

        Uses one screen-space scan (not dozens of chord triangles) so piechart's
        Depth×slice loop under *REFRESH OFF finishes quickly.

        Disabled while ``_clip_disc`` is set (after CIRCLE FILL): soccerball's
        projected pentagon chords often look equilateral about a *vertex*, so
        the sector path drew large wedges that bulged outside the yellow disc.
        Plain triangles still honour disc clip via ``_put_screen_pixel``.
        """
        if self._clip_disc is not None:
            return False
        dx1 = float(x1 - x0)
        dy1 = float(y1 - y0)
        dx2 = float(x2 - x0)
        dy2 = float(y2 - y0)
        r1 = math.hypot(dx1, dy1)
        r2 = math.hypot(dx2, dy2)
        if r1 < 8.0 or r2 < 8.0:
            return False
        # Same radius (chord of a circle about the first MOVE point).
        if abs(r1 - r2) > max(2.0, 0.03 * r1):
            return False
        a1 = math.atan2(dy1, dx1)
        a2 = math.atan2(dy2, dx2)
        # Shortest signed turn a1 → a2 in (-π, π]. Piechart slices are each
        # < π so this matches increasing `prev`; avoids filling ~2π for a
        # small clockwise isosceles triangle.
        delta = a2 - a1
        while delta <= -math.pi:
            delta += 2.0 * math.pi
        while delta > math.pi:
            delta -= 2.0 * math.pi
        if abs(delta) < 0.05:
            return False
        radius = 0.5 * (r1 + r2)
        self._fill_sector_screen(x0, y0, radius, a1, delta, gcol)
        return True

    def _angle_in_sweep(self, ang: float, a0: float, delta: float) -> bool:
        """True if ang lies on the signed short sweep from a0 by delta."""
        d = ang - a0
        while d <= -math.pi:
            d += 2.0 * math.pi
        while d > math.pi:
            d -= 2.0 * math.pi
        if delta >= 0.0:
            return -1e-9 <= d <= delta + 1e-9
        return delta - 1e-9 <= d <= 1e-9

    def _fill_sector_screen(
        self,
        cx: int,
        cy: int,
        radius: float,
        a0: float,
        delta: float,
        gcol: GColState,
    ) -> None:
        """Rasterise a disc sector in screen pixels (fast bulk write + one dirty rect)."""
        scx, scy = self._to_screen(cx, cy)
        srx = max(1, int(math.ceil(radius / max(1, self.x_scale))))
        sry = max(1, int(math.ceil(radius / max(1, self.y_scale))))
        x_lo = max(0, scx - srx - 1)
        x_hi = min(self.width - 1, scx + srx + 1)
        y_lo = max(0, scy - sry - 1)
        y_hi = min(self.height - 1, scy + sry + 1)
        if x_lo > x_hi or y_lo > y_hi:
            return

        mode, colour = gcol
        colour_b = int(colour) & 0xFF
        use_replace = mode == 0
        true_rgb = self._truecolour_rgb if use_replace else None

        # Ray endpoints for wedge test (no per-pixel atan2).
        a1 = a0 + delta
        ca0, sa0 = math.cos(a0), math.sin(a0)
        ca1, sa1 = math.cos(a1), math.sin(a1)
        ccw = delta >= 0.0

        if use_replace and self.pixels_is_numpy:
            painted = self._fill_sector_numpy(
                cx, cy, radius, ca0, sa0, ca1, sa1, ccw,
                x_lo, x_hi, y_lo, y_hi, colour_b, true_rgb,
            )
        else:
            painted = self._fill_sector_python(
                cx, cy, radius, ca0, sa0, ca1, sa1, ccw,
                x_lo, x_hi, y_lo, y_hi, gcol, use_replace, colour_b, true_rgb,
            )

        if painted and use_replace:
            if self._dirty_rect is None:
                self._dirty_rect = (x_lo, y_lo, x_hi, y_hi)
            else:
                dx0, dy0, dx1, dy1 = self._dirty_rect
                self._dirty_rect = (
                    min(dx0, x_lo),
                    min(dy0, y_lo),
                    max(dx1, x_hi),
                    max(dy1, y_hi),
                )
            self.plot_count += painted

    def _fill_sector_python(
        self,
        cx: int,
        cy: int,
        radius: float,
        ca0: float,
        sa0: float,
        ca1: float,
        sa1: float,
        ccw: bool,
        x_lo: int,
        x_hi: int,
        y_lo: int,
        y_hi: int,
        gcol: GColState,
        use_replace: bool,
        colour_b: int,
        true_rgb: Optional[RGB],
    ) -> int:
        r2 = float(radius) * float(radius)
        xs = self.x_scale
        ys = self.y_scale
        ox = self.origin_x
        oy = self.origin_y
        h = self.height
        painted = 0
        for sy in range(y_lo, y_hi + 1):
            uy = float((h - 1 - sy) * ys - oy - cy)
            uy2 = uy * uy
            row = self.pixels[sy]
            rgb_row = self.rgb_pixels[sy]
            for sx in range(x_lo, x_hi + 1):
                ux = float(sx * xs - ox - cx)
                if ux * ux + uy2 > r2:
                    continue
                # cross(ray, p) = cos*uy - sin*ux; CCW sector: left of start, right of end
                c0 = ca0 * uy - sa0 * ux
                c1 = ca1 * uy - sa1 * ux
                if ccw:
                    if c0 < -1e-6 or c1 > 1e-6:
                        continue
                else:
                    if c0 > 1e-6 or c1 < -1e-6:
                        continue
                if use_replace:
                    row[sx] = colour_b
                    if true_rgb is not None:
                        rgb_row[sx] = true_rgb
                        self.rgb_dirty.add((sx, sy))
                    else:
                        rgb_row[sx] = None
                        self.rgb_dirty.discard((sx, sy))
                    painted += 1
                else:
                    self._put_screen_pixel(sx, sy, gcol)
        return painted

    def _fill_sector_numpy(
        self,
        cx: int,
        cy: int,
        radius: float,
        ca0: float,
        sa0: float,
        ca1: float,
        sa1: float,
        ccw: bool,
        x_lo: int,
        x_hi: int,
        y_lo: int,
        y_hi: int,
        colour_b: int,
        true_rgb: Optional[RGB],
    ) -> int:
        np = self._np
        assert np is not None
        # Screen → user relative to centre (vectorised).
        sx = np.arange(x_lo, x_hi + 1, dtype=np.float64)
        sy = np.arange(y_lo, y_hi + 1, dtype=np.float64)
        ux = sx * float(self.x_scale) - float(self.origin_x) - float(cx)
        uy = (float(self.height - 1) - sy) * float(self.y_scale) - float(
            self.origin_y
        ) - float(cy)
        # Broadcasting: uy column, ux row
        ux2d = ux[np.newaxis, :]
        uy2d = uy[:, np.newaxis]
        r2 = float(radius) * float(radius)
        inside = ux2d * ux2d + uy2d * uy2d <= r2
        c0 = ca0 * uy2d - sa0 * ux2d
        c1 = ca1 * uy2d - sa1 * ux2d
        if ccw:
            wedge = (c0 >= -1e-6) & (c1 <= 1e-6)
        else:
            wedge = (c0 <= 1e-6) & (c1 >= -1e-6)
        mask = inside & wedge
        if not mask.any():
            return 0
        patch = self.pixels[y_lo : y_hi + 1, x_lo : x_hi + 1]
        patch[mask] = colour_b
        n = int(mask.sum())
        if true_rgb is not None:
            ys_i, xs_i = np.nonzero(mask)
            for j, i in zip(ys_i.tolist(), xs_i.tolist()):
                py, px = y_lo + j, x_lo + i
                self.rgb_pixels[py][px] = true_rgb
                self.rgb_dirty.add((px, py))
        elif self.rgb_dirty:
            # Only scrub overrides if any exist (piechart uses palette only).
            ys_i, xs_i = np.nonzero(mask)
            for j, i in zip(ys_i.tolist(), xs_i.tolist()):
                py, px = y_lo + j, x_lo + i
                if self.rgb_pixels[py][px] is not None:
                    self.rgb_pixels[py][px] = None
                    self.rgb_dirty.discard((px, py))
        return n

    def _fill_triangle_screen(
        self,
        pts: Sequence[Tuple[int, int]],
        gcol: GColState,
    ) -> None:
        if len(pts) != 3:
            return
        ordered = sorted(pts, key=lambda p: p[1])
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

        y_start = int(y_a)
        y_end = int(y_c)
        for y in range(y_start, y_end + 1):
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
                self._put_screen_pixel(x, y, gcol)
