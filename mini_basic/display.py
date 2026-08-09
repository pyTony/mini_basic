"""Optional display backends for mini_basic (terminal, pygame/SDL window)."""
from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod

os.environ.setdefault('SDL_WINDOWS_DPI_AWARENESS', 'permonitorv2')
os.environ.setdefault('SDL_VIDEO_CENTERED', '1')
os.environ.setdefault('SDL_HINT_GRAB_KEYBOARD', '0')
os.environ.setdefault('SDL_RENDER_SCALE_QUALITY', 'nearest')
os.environ.setdefault('SDL_WINDOWS_DPI_AWARENESS', 'permonitorv2')
os.environ.setdefault('SDL_VIDEO_CENTERED', '1')
os.environ.setdefault('SDL_HINT_GRAB_KEYBOARD', '0')
os.environ.setdefault('SDL_RENDER_SCALE_QUALITY', 'nearest')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
from typing import Callable, Dict, List, Optional, Sequence, Tuple

_WINDOW_CHROME_HEIGHT = 48
_WINDOW_CHROME_WIDTH = 16
_WINDOW_MARGIN = 8
_TITLE_BAR_ESTIMATE = 40

DEBUG = False

# Package-wide debug helper (active config / MINI_BASIC_DEBUG / --debug).
from mini_basic.util.debug import dprint  # noqa: F401

from mini_basic.bbc_font import blit_char as blit_mos_char
from mini_basic.bbc_graphics import BBCGraphics
from mini_basic.bbc_modes import (
    BBCModeSpec,
    TELETEXT_FG_COLOURS,
    TELETEXT_GFX_COLOURS,
    bbc_mode_spec,
    bbc_os_scales,
    map_mode_text_colour,
    teletext_mosaic_pattern,
    teletext_sextant_filled,
)

# BBC Micro / Agon style text colours (0-15); 16+ map to extended palette.
# Colour 7 is white on the Beeb (not VGA light-gray). welcome GCOL 0,7 letters
# must contrast with red CHR$255 blocks; gray-7 made them invisible on GCOL 135 paper.
BBC_PALETTE: Tuple[Tuple[int, int, int], ...] = (
    (0, 0, 0),
    (180, 0, 0),
    (0, 160, 0),
    (180, 180, 0),
    (0, 0, 180),
    (180, 0, 180),
    (0, 180, 180),
    (255, 255, 255),
    (80, 80, 80),
    (255, 0, 0),
    (0, 255, 0),
    (255, 255, 0),
    (0, 0, 255),
    (255, 0, 255),
    (0, 255, 255),
    (255, 255, 255),
)


def pygame_keydown_char(pygame: object, event: object) -> Optional[str]:
    unicode = getattr(event, 'unicode', '') or ''
    if unicode and unicode.isprintable():
        return unicode
    key = getattr(event, 'key', None)
    mod = getattr(event, 'mod', 0)
    if key is None:
        return None
    if pygame.K_a <= key <= pygame.K_z:
        ch = chr(ord('a') + key - pygame.K_a)
        if mod & (pygame.KMOD_SHIFT | pygame.KMOD_CAPS):
            ch = ch.upper()
        return ch
    if pygame.K_0 <= key <= pygame.K_0:
        return chr(ord('0') + key - pygame.K_0)
    return None


def colour_to_rgb(colour: int) -> Tuple[int, int, int]:
    if 0 <= colour < len(BBC_PALETTE):
        return BBC_PALETTE[colour]
    # Agon-style extended indices: spread hues.
    hue = (colour * 137) % 360
    sat = 180 + (colour % 64)
    val = 120 + ((colour // 3) % 120)
    return _hsv_to_rgb(hue, sat / 255.0, val / 255.0)


def _hsv_to_rgb(h: int, s: float, v: float) -> Tuple[int, int, int]:
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        rp, gp, bp = c, x, 0
    elif h < 120:
        rp, gp, bp = x, c, 0
    elif h < 180:
        rp, gp, bp = 0, c, x
    elif h < 240:
        rp, gp, bp = 0, x, c
    elif h < 300:
        rp, gp, bp = x, 0, c
    else:
        rp, gp, bp = c, 0, x
    return (
        int((rp + m) * 255),
        int((gp + m) * 255),
        int((bp + m) * 255),
    )


class DisplayBackend(ABC):
    """Abstract output surface for text and low-resolution graphics."""

    @abstractmethod
    def begin_run(self) -> None:
        ...

    @abstractmethod
    def end_run(self) -> None:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...

    @abstractmethod
    def set_mode(self, mode: int) -> None:
        ...

    @abstractmethod
    def set_colour(self, colour: int) -> None:
        ...

    @abstractmethod
    def goto(self, row: int, col: int) -> None:
        ...

    @abstractmethod
    def write(self, text: str) -> None:
        ...

    @abstractmethod
    def newline(self) -> None:
        ...

    @abstractmethod
    def plot(self, x: int, y: int, colour: Optional[int] = None) -> None:
        ...

    def gcol(self, mode: int, colour: int) -> None:
        return

    def plot_code(self, code: int, x: int, y: int) -> None:
        self.plot(x, y)

    def move_absolute(self, x: int, y: int) -> None:
        return

    def move_relative(self, dx: int, dy: int) -> None:
        return

    def draw_relative(self, dx: int, dy: int) -> None:
        return

    def draw_absolute(self, x: int, y: int) -> None:
        return

    def fill_rectangle(self, x: int, y: int, width: int, height: int) -> None:
        return

    def clear_graphics(self) -> None:
        return

    def set_graphics_origin(self, x: int, y: int) -> None:
        return

    def set_graphics_size(self, width: int, height: int) -> None:
        return

    def set_palette_rgb(self, index: int, rgb: Tuple[int, int, int]) -> None:
        return

    def point_colour(self, x: int, y: int) -> int:
        return 0

    def mouse_state(self) -> Tuple[int, int, int]:
        return (0, 0, 0)

    def is_graphics_mode(self) -> bool:
        return False

    @abstractmethod
    def define_sprite(self, sprite_id: int, pixels: Sequence[Sequence[int]]) -> None:
        ...

    @abstractmethod
    def draw_sprite(self, sprite_id: int, x: int, y: int) -> None:
        ...

    @abstractmethod
    def present(self, *, force: bool = False) -> None:
        ...

    def mark_dirty(self) -> None:
        return

    @abstractmethod
    def poll(self) -> bool:
        """Process window events. Returns False if the user closed the window."""
        ...

    def pump_events(self) -> None:
        """Drain the OS message queue (pygame: keeps the window responsive)."""
        return

    def read_line(
        self,
        *,
        max_length: int = 255,
        tee: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Read a line of input when the backend owns the keyboard (pygame)."""
        raise NotImplementedError

    def hold_open(self) -> None:
        """Keep the display visible after the program ends (pygame: until Escape/close)."""
        return

    def capture_framebuffer(self) -> List[List[int]]:
        """BBC graphics palette indices per pixel; empty when unavailable."""
        return []

    def capture_canvas_rgb(self) -> Tuple[int, int, List[List[Tuple[int, int, int]]]]:
        """Logical canvas RGB rows after present(); (0, 0, []) when unavailable."""
        return 0, 0, []

    def capture_screen_rgb(self) -> Tuple[int, int, List[List[Tuple[int, int, int]]]]:
        """Scaled window RGB rows after present(); (0, 0, []) when unavailable."""
        return 0, 0, []


def count_framebuffer_pixels(
    pixels: Sequence[Sequence[int]],
    *,
    colour: Optional[int] = None,
    exclude: Tuple[int, ...] = (0,),
) -> int:
    """Count pixels in a captured framebuffer."""
    total = 0
    for row in pixels:
        for value in row:
            if colour is not None:
                if value == colour:
                    total += 1
            elif value not in exclude:
                total += 1
    return total


class NullDisplay(DisplayBackend):
    """No-op backend (``display=none`` / ``null``)."""

    def begin_run(self) -> None:
        return

    def end_run(self) -> None:
        return

    def clear(self) -> None:
        return

    def set_mode(self, mode: int) -> None:
        return

    def set_text_dimensions(self, cols: int, rows: int) -> None:
        return

    def set_colour(self, colour: int) -> None:
        return

    def goto(self, row: int, col: int) -> None:
        return

    def write(self, text: str) -> None:
        return

    def newline(self) -> None:
        return

    def set_graphics_print_mode(self, enabled: bool) -> None:
        return

    def plot(self, x: int, y: int, colour: Optional[int] = None) -> None:
        return

    def define_sprite(self, sprite_id: int, pixels: Sequence[Sequence[int]]) -> None:
        return

    def draw_sprite(self, sprite_id: int, x: int, y: int) -> None:
        return

    def present(self, *, force: bool = False) -> None:
        return

    def mark_dirty(self) -> None:
        return

    def poll(self) -> bool:
        return True

    def pump_events(self) -> None:
        return


class TerminalDisplay(DisplayBackend):
    """Text-cell backend for ``--display terminal``.

    Streaming mode (default): each ``write``/``newline`` goes straight to
    stdout so plain PRINT works under ``redirect_stdout`` / pipes.

    After a ``goto`` (TAB/PRINT AT), switches to grid mode; ``present()``
    repaints the full grid with ANSI. Restored after copy-paste recovery.
    """

    _ANSI_FG = (30, 31, 32, 33, 34, 35, 36, 37)
    _ANSI_BG = (40, 41, 42, 43, 44, 45, 46, 47)

    def __init__(self, text_cols: int = 80, text_rows: int = 30):
        self.text_cols = max(1, int(text_cols))
        self.text_rows = max(1, int(text_rows))
        self._cursor_row = 0
        self._cursor_col = 0
        self._fg_colour = 7
        self._bg_colour = 0
        self._text: List[List[Tuple[str, int, int]]] = []
        self._dirty = True
        self._open = False
        self._positioned = False
        self._terminal_text = True
        self._reset_text_grid()

    def _blank_cell(self) -> Tuple[str, int, int]:
        return (' ', self._fg_colour, self._bg_colour)

    def _reset_text_grid(self) -> None:
        blank = self._blank_cell()
        self._text = [
            [blank for _ in range(self.text_cols)] for _ in range(self.text_rows)
        ]
        self._cursor_row = 0
        self._cursor_col = 0
        self._dirty = True

    def begin_run(self) -> None:
        self._open = True
        self._positioned = False
        self._dirty = True

    def end_run(self) -> None:
        self.present(force=True)
        self._open = False

    def set_text_dimensions(self, cols: int, rows: int) -> None:
        cols = max(1, int(cols))
        rows = max(1, int(rows))
        if cols != self.text_cols or rows != self.text_rows:
            self.text_cols = cols
            self.text_rows = rows
            self._reset_text_grid()

    def clear(self) -> None:
        self._reset_text_grid()
        self._dirty = True
        if not self._positioned:
            try:
                sys.stdout.write('\x1b[2J\x1b[H')
                sys.stdout.flush()
            except Exception:
                pass

    def goto(self, row: int, col: int) -> None:
        self._positioned = True
        self._cursor_row = max(0, min(self.text_rows - 1, int(row)))
        self._cursor_col = max(0, min(self.text_cols - 1, int(col)))
        self._dirty = True

    def write(self, text: str) -> None:
        if not text:
            return
        if not self._positioned:
            # Stream once to stdout; update grid/cursor without re-emitting.
            try:
                sys.stdout.write(text)
                sys.stdout.flush()
            except Exception:
                pass
            for ch in text:
                if ch == '\n':
                    self._grid_newline()
                else:
                    self._grid_put(ch)
            return
        for ch in text:
            if ch == '\n':
                self.newline()
                continue
            if self._cursor_col >= self.text_cols:
                self.newline()
            self._grid_put(ch)

    def _grid_put(self, ch: str) -> None:
        if self._cursor_col >= self.text_cols:
            self._grid_newline()
        r, c = self._cursor_row, self._cursor_col
        self._text[r][c] = (ch, self._fg_colour, self._bg_colour)
        self._cursor_col += 1
        self._dirty = True

    def _grid_newline(self) -> None:
        self._cursor_row += 1
        self._cursor_col = 0
        if self._cursor_row >= self.text_rows:
            self._text.pop(0)
            self._text.append([self._blank_cell() for _ in range(self.text_cols)])
            self._cursor_row = self.text_rows - 1
        self._dirty = True

    def newline(self) -> None:
        if not self._positioned:
            try:
                sys.stdout.write('\n')
                sys.stdout.flush()
            except Exception:
                pass
        self._grid_newline()

    @staticmethod
    def _cell_parts(cell: object) -> Tuple[str, int, int]:
        if not isinstance(cell, tuple) or not cell:
            return ' ', 7, 0
        ch = str(cell[0]) if cell[0] is not None else ' '
        fg = int(cell[1]) if len(cell) > 1 else 7
        bg = int(cell[2]) if len(cell) > 2 else 0
        return ch, fg & 7, bg & 7

    def present(self, *, force: bool = False) -> None:
        if not self._positioned:
            # Streaming mode already wrote through; nothing to repaint.
            self._dirty = False
            return
        if not (force or self._dirty):
            return
        if not self._open and not force:
            return
        try:
            out = sys.stdout
            esc = '\x1b'
            for r in range(self.text_rows):
                out.write(f'{esc}[{r + 1};1H')
                last_fg: Optional[int] = None
                last_bg: Optional[int] = None
                for cell in self._text[r]:
                    ch, fg, bg = self._cell_parts(cell)
                    if fg != last_fg or bg != last_bg:
                        out.write(
                            f'{esc}[0;{self._ANSI_FG[fg]};{self._ANSI_BG[bg]}m'
                        )
                        last_fg, last_bg = fg, bg
                    out.write(ch if ch else ' ')
                out.write(f'{esc}[0m{esc}[K')
            cr = max(0, min(self.text_rows - 1, self._cursor_row))
            cc = max(0, min(self.text_cols - 1, self._cursor_col))
            out.write(f'{esc}[{cr + 1};{cc + 1}H')
            out.flush()
        except Exception:
            pass
        self._dirty = False

    def mark_dirty(self) -> None:
        self._dirty = True

    def poll(self) -> bool:
        return True

    def pump_events(self) -> None:
        return

    def set_mode(self, mode: int) -> None:
        return

    def set_colour(self, colour: int) -> None:
        """BBC COLOUR / VDU 17: 0-127 text fg, 128-255 text bg (code-128)."""
        code = int(colour) & 255
        if code >= 128:
            logical = code - 128
            # Keep full 0..127 (piechart COLOR 15+128 → sky palette index 15).
            # Classic Acorn flash bg is only 136-143 with logical 0-7.
            self._bg_colour = logical & 255
            self._text_flash = 136 <= code <= 143 and logical < 8
        elif code >= 8:
            self._fg_colour = (code - 8) & 7
            self._text_flash = True
        else:
            self._fg_colour = code & 7
            self._text_flash = False
        # Stream ANSI so hanoi COLOUR bars + digits are visible in terminal mode.
        if not self._positioned and self._open:
            try:
                fg = self._fg_colour
                bg = self._bg_colour & 7
                # Match pygame: black digits on light bars.
                if bg in (3, 6, 7):
                    fg = 0
                elif fg == bg:
                    fg = 7 if bg == 0 else 0
                sys.stdout.write(
                    f'\x1b[0;{self._ANSI_FG[fg]};{self._ANSI_BG[bg]}m'
                )
                sys.stdout.flush()
            except Exception:
                pass

    def plot(self, x: int, y: int, colour: Optional[int] = None) -> None:
        return

    def define_sprite(self, sprite_id: int, pixels: Sequence[Sequence[int]]) -> None:
        return

    def draw_sprite(self, sprite_id: int, x: int, y: int) -> None:
        return

    def hold_open(self) -> None:
        return

    @property
    def is_open(self) -> bool:
        return self._open


class _TeletextLineState:
    """Per-line Teletext attributes (MODE 7)."""

    __slots__ = (
        'fg', 'bg', 'flash', 'graphics', 'gfx_fg',
        'separated', 'concealed', 'hold', 'hold_pattern',
    )

    def __init__(self) -> None:
        self.fg = 7
        self.bg = 0
        self.flash = False
        self.graphics = False
        self.gfx_fg = 7
        self.separated = False
        self.concealed = False
        self.hold = False
        self.hold_pattern: Optional[int] = None

    def reset(self) -> None:
        self.__init__()


class PygameDisplay(DisplayBackend):
    """SDL window with scaled text grid and low-resolution pixel framebuffer."""

    def __init__(
        self,
        *,
        text_cols: int = 80,
        text_rows: int = 30,
        graphics_width: int = 320,
        graphics_height: int = 256,
        cell_width: int = 8,
        cell_height: int = 8,
        scale: int = 2,
        scale_locked: bool = False,
        caption: str = 'mini_basic',
        fps_limit: int = 60,
    ) -> None:
        try:
            import pygame
        except ImportError as exc:
            raise ImportError(
                'pygame is required for display="pygame". Install with: pip install pygame-ce'
            ) from exc
        self._pygame = pygame
        self.text_cols = text_cols
        self.text_rows = text_rows
        self.graphics_width = graphics_width
        self.graphics_height = graphics_height
        self._default_cell_width = cell_width
        self._default_cell_height = cell_height
        self.cell_width = cell_width
        self.cell_height = cell_height
        self._par_w = 1
        self._par_h = 1
        self._plot_enabled = True
        self._teletext_lines: List[_TeletextLineState] = []
        self._requested_scale = max(1, scale)
        self.scale_locked = bool(scale_locked)
        self.scale = self._requested_scale
        self.caption = caption
        self.fps_limit = fps_limit

        self._mode = 8
        self._fg_colour = 7
        self._bg_colour = 0
        self._cursor_row = 0
        self._cursor_col = 0
        self._print_at_graphics = False
        self._graphics_print_layers: List[Tuple[str, int, int, int]] = []
        # VDU 23,n,r0..r7 — user-defined 8×8 glyphs (welcome CHR$255 solid block).
        self._user_chars: Dict[int, Tuple[int, ...]] = {}
        self._text: List[List[Tuple[str, int]]] = []
        self._sprites: Dict[int, object] = {}
        self._sprite_placements: List[Tuple[int, int, int]] = []
        self._screen = None
        self._canvas = None
        self._font = None
        self._clock = None
        self._open = False
        self._dirty = True
        # True when text/sprites/mode need a full compose (not just a pixel patch).
        self._compose_full = True
        self._text_flash = False
        self._gfx: Optional[BBCGraphics] = None
        self._palette_rgb: Dict[int, Tuple[int, int, int]] = {}
        self._mouse_x = 0
        self._mouse_y = 0
        self._mouse_buttons = 0
        self._reset_text_grid()
        self._apply_mode_spec(bbc_mode_spec(self._mode))
        self._init_gfx()

    def _init_gfx(self) -> None:
        x_scale, y_scale = bbc_os_scales(self.graphics_width, self.graphics_height)
        self._gfx = BBCGraphics(
            self.graphics_width,
            self.graphics_height,
            x_scale=x_scale,
            y_scale=y_scale,
        )

    def is_graphics_mode(self) -> bool:
        return self._plot_enabled and self.graphics_width > 0

    def is_teletext_mode(self) -> bool:
        return self._mode == 7

    def _apply_mode_spec(self, spec: Optional[BBCModeSpec]) -> None:
        if spec is None:
            self.cell_width = self._default_cell_width
            self.cell_height = self._default_cell_height
            self._par_w = 1
            self._par_h = 1
            self._plot_enabled = self.graphics_width > 0
            return
        self.graphics_width = spec.gfx_width
        self.graphics_height = spec.gfx_height
        self.text_cols = spec.text_cols
        self.text_rows = spec.text_rows
        self.cell_width = spec.cell_width
        self.cell_height = spec.cell_height
        self._par_w = spec.par_w
        self._par_h = spec.par_h
        self._plot_enabled = spec.plot_enabled
        if self._open and self._gfx is not None:
            self._init_gfx()

    def _effective_cell_width(self) -> int:
        if self.is_graphics_mode() and self.text_cols > 0:
            return max(1, self.graphics_width // self.text_cols)
        return max(1, self.cell_width)

    def _effective_cell_height(self) -> int:
        if self.is_graphics_mode() and self.text_rows > 0:
            return max(1, self.graphics_height // self.text_rows)
        return max(1, self.cell_height)

    def _use_mos_font(self) -> bool:
        """True when text should use the Acorn MOS 8x8 matrix (BBC modes 0–8)."""
        if self.is_teletext_mode():
            return False
        return self._effective_cell_width() == 8

    def _refresh_font(self) -> None:
        if self._pygame is None or not self._pygame.get_init():
            return
        if self._use_mos_font():
            self._font = None
            return
        cw = self._effective_cell_width()
        ch = self._effective_cell_height()
        size = max(6, min(cw, ch))
        size = max(6, min(cw, ch) - 1)
        try:
            self._font = self._pygame.font.SysFont(
                'consolas,couriernew,monaco,monospace',
                size,
            )
        except Exception:
            self._font = self._pygame.font.Font(None, size)

    def _blit_glyph(
        self,
        ch: str,
        colour: int,
        x: int,
        y: int,
        *,
        clip_w: Optional[int] = None,
        clip_h: Optional[int] = None,
    ) -> None:
        assert self._canvas is not None
        cw = clip_w if clip_w is not None else self._effective_cell_width()
        ch_h = clip_h if clip_h is not None else self._effective_cell_height()
        pygame = self._pygame
        prev_clip = self._canvas.get_clip()
        self._canvas.set_clip(pygame.Rect(x, y, cw, ch_h))
        try:
            code = ord(ch) if ch else 0
            user = self._user_chars.get(code)
            if user is not None:
                self._blit_user_char(user, colour, x, y, cw, ch_h)
                return
            if self._use_mos_font():
                blit_mos_char(
                    self._canvas,
                    ch,
                    self._pixel_rgb(colour),
                    x,
                    y,
                    cell_w=cw,
                    cell_h=ch_h,
                )
                return
            self._ensure_text_font()
            if self._font is None:
                return
            # Fallback for non-standard cell sizes (antialiasing off on graphics).
            aa = not self.is_graphics_mode()
            surf = self._font.render(ch, aa, self._pixel_rgb(colour))
            gw, gh = surf.get_size()
            if gw > cw or gh > ch_h:
                # Clip to the cell — scaling glyphs makes MODE 1 captions unreadable.
                sub_w = min(gw, cw)
                sub_h = min(gh, ch_h)
                surf = surf.subsurface((0, 0, sub_w, sub_h))
                gw, gh = sub_w, sub_h
            x_off = max(0, (cw - gw) // 2)
            y_off = max(0, (ch_h - gh) // 2)
            self._canvas.blit(surf, (x + x_off, y + y_off))
        finally:
            self._canvas.set_clip(prev_clip)

    def define_user_char(self, code: int, rows: Tuple[int, ...]) -> None:
        """VDU 23,n,r0..r7 — 8×8 bitmap for character n (welcome solid CHR$255)."""
        code = int(code) & 0xFF
        bits = tuple(int(r) & 0xFF for r in rows[:8])
        if len(bits) < 8:
            bits = bits + (0,) * (8 - len(bits))
        self._user_chars[code] = bits
        self.mark_compose_full()

    def _blit_user_char(
        self,
        rows: Tuple[int, ...],
        colour: int,
        x: int,
        y: int,
        cell_w: int,
        cell_h: int,
    ) -> None:
        assert self._canvas is not None
        rgb = self._pixel_rgb(colour)
        scale_y = max(1, cell_h // 8)
        scale_x = max(1, cell_w // 8)
        for row_i, row_byte in enumerate(rows[:8]):
            for col_i in range(8):
                if row_byte & (0x80 >> col_i):
                    px = x + col_i * scale_x
                    py = y + row_i * scale_y
                    if scale_x == 1 and scale_y == 1:
                        self._canvas.set_at((px, py), rgb)
                    else:
                        self._canvas.fill(rgb, (px, py, scale_x, scale_y))

    def _scale_surface(self, surface, target_w: int, target_h: int):
        """Upscale/downscale; integer ratios use crisp pixel replication."""
        pygame = self._pygame
        sw, sh = surface.get_width(), surface.get_height()
        if sw == target_w and sh == target_h:
            return surface
        if sw > 0 and sh > 0 and target_w % sw == 0 and target_h % sh == 0:
            x_factor = target_w // sw
            y_factor = target_h // sh
            if x_factor >= 1 and y_factor >= 1:
                if x_factor == y_factor and hasattr(pygame.transform, 'scale_by'):
                    return pygame.transform.scale_by(surface, x_factor)
                if x_factor == 1 and y_factor > 1:
                    return self._replicate_rows(surface, y_factor)
                if y_factor == 1 and x_factor > 1:
                    return self._replicate_columns(surface, x_factor)
        return pygame.transform.scale(surface, (target_w, target_h))

    def _replicate_rows(self, surface, factor: int):
        pygame = self._pygame
        sw, sh = surface.get_width(), surface.get_height()
        wide = pygame.Surface((sw, sh * factor))
        for row in range(sh):
            line = surface.subsurface((0, row, sw, 1))
            for duplicate in range(factor):
                wide.blit(line, (0, row * factor + duplicate))
        return wide

    def _replicate_columns(self, surface, factor: int):
        pygame = self._pygame
        sw, sh = surface.get_width(), surface.get_height()
        tall = pygame.Surface((sw * factor, sh))
        for col in range(sw):
            stripe = surface.subsurface((col, 0, 1, sh))
            for duplicate in range(factor):
                tall.blit(stripe, (col * factor + duplicate, 0))
        return tall

    def _pixel_block_size(self) -> Tuple[int, int]:
        """Screen pixels per logical pixel (width, height).

        MODE 0 (par 1:2) is taller; MODE 5 (par 2:1) is wider. Stretch both axes.
        """
        par_w = max(1, self._par_w)
        par_h = max(1, self._par_h)
        pw = max(1, self.scale * par_w)
        ph = max(1, self.scale * par_h)
        return pw, ph

    def _window_client_size_at_scale(self, scale: int) -> Tuple[int, int]:
        logical_w, logical_h = self._logical_canvas_size()
        par_w = max(1, self._par_w)
        par_h = max(1, self._par_h)
        # MODE 5 was tiny: old formula only scaled height by par_h/par_w (//2 → 0).
        pw = max(1, scale * par_w)
        ph = max(1, scale * par_h)
        return logical_w * pw, logical_h * ph

    def _window_client_size(self) -> Tuple[int, int]:
        return self._window_client_size_at_scale(self.scale)

    def _erase_cursor_cell(self) -> None:
        if self._cursor_col <= 0:
            return
        self._cursor_col -= 1
        self._text[self._cursor_row][self._cursor_col] = self._blank_text_cell()
        self._dirty = True

    def backspace_input_char(self) -> None:
        """Remove the character before the text cursor (INPUT editing)."""
        self._erase_cursor_cell()

    def _reset_teletext_lines(self) -> None:
        self._teletext_lines = [_TeletextLineState() for _ in range(self.text_rows)]

    def _blank_text_cell(self) -> Tuple[str, int, int, bool]:
        # Unwritten cells use bg=0 so graphics-mode present() does not repaint the
        # whole canvas with COLOUR background every frame (soccerball green-only).
        # Explicit PRINT after COLOUR n+128 still stores the live bg via _store_text_cell
        # (hanoi discs need coloured spaces).
        return (' ', self._fg_colour, 0, False)

    @staticmethod
    def _decode_text_cell(cell: Tuple) -> Tuple[str, int, int, bool]:
        """Normal/graphics text cell: (ch, fg, bg, flash), with older tuple lengths supported."""
        if len(cell) >= 6:
            ch, fg, bg = cell[0], cell[1], cell[2]
            return ch, fg, bg, bool(cell[5])
        if len(cell) >= 4:
            return cell[0], cell[1], cell[2], bool(cell[3])
        if len(cell) == 3:
            third = cell[2]
            if isinstance(third, bool):
                return cell[0], cell[1], 0, third
            return cell[0], cell[1], int(third), False
        if len(cell) == 2:
            return cell[0], cell[1], 0, False
        return ' ', 7, 0, False

    def _store_text_cell(self, ch: str) -> None:
        self._text[self._cursor_row][self._cursor_col] = (
            ch,
            self._fg_colour,
            self._bg_colour,
            self._text_flash,
        )

    def _display_text_colour(self, logical: int) -> int:
        return map_mode_text_colour(logical, self._mode)

    def _reset_text_grid(self) -> None:
        self._text_flash = False
        blank = self._blank_text_cell()
        self._text = [[blank for _ in range(self.text_cols)] for _ in range(self.text_rows)]
        if self.is_teletext_mode():
            self._reset_teletext_lines()

    def _logical_canvas_size(self) -> Tuple[int, int]:
        if self.is_graphics_mode():
            return self.graphics_width, self.graphics_height
        return self.text_cols * self.cell_width, self.text_rows * self.cell_height

    def _par_display_size(self) -> Tuple[int, int]:
        w, h = self._logical_canvas_size()
        if self.is_teletext_mode():
            return w, h * self._par_h // max(1, self._par_w)
        return w * self._par_w // max(1, self._par_h), h

    def _surface_size(self) -> Tuple[int, int]:
        """Window client area: logical resolution with PAR and --scale applied."""
        return self._window_client_size()

    def pump_events(self) -> None:
        """Keep the SDL queue alive without consuming keyboard/text events."""
        pygame = self._pygame
        if not self._open or not pygame.get_init():
            return
        pygame.event.pump()

    def _open_window(self, *, center: bool = False) -> None:
        pygame = self._pygame
        if not pygame.get_init():
            pygame.init()
        base_w, base_h = self._window_client_size_at_scale(1)
        max_fit = fit_display_scale(
            base_w,
            base_h,
            self._requested_scale,
            max_scale=99 if self.scale_locked else 8,
        )
        if self.scale_locked:
            # CLI --scale N: honour N exactly. Clamping to max_fit made --scale 3
            # and --scale 4 identical on typical desktops (MODE 8 640×512 only
            # fits 2× on 1080p/1440p height).
            self.scale = max(1, self._requested_scale)
            win_w, win_h = self._window_client_size_at_scale(self.scale)
            self._screen = pygame.display.set_mode((win_w, win_h))
            self.pump_events()
            if center:
                self._center_window()
        else:
            start_scale = min(self._requested_scale, max_fit)
            for scale in range(start_scale, 0, -1):
                self.scale = scale
                win_w, win_h = self._window_client_size_at_scale(self.scale)
                self._screen = pygame.display.set_mode((win_w, win_h))
                self.pump_events()
                if center:
                    self._center_window()
                if self._window_fits_on_screen():
                    break
            win_w, win_h = self._window_client_size()
        spec = bbc_mode_spec(self._mode)
        if spec is not None and spec.plot_enabled and spec.gfx_width:
            mode_note = f' MODE{self._mode} {spec.gfx_width}x{spec.gfx_height}'
        elif self.is_teletext_mode():
            mode_note = ' MODE7 Teletext'
        else:
            mode_note = f' MODE{self._mode}' if self._mode <= 7 else ''
        pygame.display.set_caption(
            f'{self.caption}{mode_note} ({self.scale}x, {win_w}x{win_h})'
        )
        logical_w, logical_h = self._logical_canvas_size()
        self._canvas = pygame.Surface((logical_w, logical_h))
        if self._font is None:
            self._refresh_font()
        if self._clock is None:
            self._clock = pygame.time.Clock()

    def _center_window(self) -> None:
        pygame = self._pygame
        if not hasattr(pygame, 'Window'):
            return
        try:
            window = pygame.Window.from_display_module()
            screen_w, screen_h = desktop_size(pygame)
            client_w, client_h = window.size
            x = max(0, (screen_w - client_w) // 2)
            y = max(0, (screen_h - client_h - _TITLE_BAR_ESTIMATE) // 2)
            window.position = (x, y)
        except Exception:
            return

    def _window_fits_on_screen(self) -> bool:
        pygame = self._pygame
        w, h = self._window_client_size()
        screen_w, screen_h = desktop_size(pygame)
        win_w = w + _WINDOW_CHROME_WIDTH
        win_h = h + _TITLE_BAR_ESTIMATE + _WINDOW_MARGIN
        if sys.platform == 'win32' and win_h > int(screen_h * 0.92):
            return False
        if not hasattr(pygame, 'Window'):
            return win_h <= screen_h and win_w <= screen_w
        try:
            window = pygame.Window.from_display_module()
            x, y = window.position
            client_w, client_h = window.size
            bottom = y + client_h + _TITLE_BAR_ESTIMATE
            right = x + client_w + _WINDOW_CHROME_WIDTH
            return x >= 0 and y >= 0 and bottom <= screen_h and right <= screen_w
        except Exception:
            return win_h <= screen_h and win_w <= screen_w

    @property
    def is_open(self) -> bool:
        return bool(self._open and self._screen is not None)

    def mark_closed(self) -> None:
        """User closed the window (X / Escape): free surfaces for a later reopen."""
        if self._screen is not None:
            try:
                self._pygame.display.quit()
            except Exception:
                pass
        self._screen = None
        self._canvas = None
        self._open = False
        try:
            if self._pygame.get_init():
                self._pygame.quit()
        except Exception:
            pass

    def begin_run(self) -> None:
        if self._screen is None:
            self._open_window(center=True)
        self._open = True
        try:
            self._pygame.event.set_grab(False)
        except Exception:
            pass
        self.clear()
        self.present()

    def end_run(self) -> None:
        if self._open or self._screen is not None:
            pygame = self._pygame
            if self._screen is not None:
                try:
                    pygame.display.quit()
                except Exception:
                    pass
            self._screen = None
            self._canvas = None
            try:
                if pygame.get_init():
                    pygame.quit()
            except Exception:
                pass
        self._open = False

    def clear(self) -> None:
        assert self._canvas is not None
        # Honour COLOR n,r,g,b custom palette (piechart sky = index 15).
        self._canvas.fill(self._pixel_rgb(self._bg_colour))
        self._reset_text_grid()
        self._cursor_row = 0
        self._cursor_col = 0
        self._sprite_placements = []

        if self._gfx is not None:
            self._gfx.clear_graphics(self._bg_colour)
        self._graphics_print_layers = []

        self._dirty = True
        self._compose_full = True

    def set_graphics_print_mode(self, enabled: bool) -> None:
        self._print_at_graphics = bool(enabled)

    def reset_text_colours(self) -> None:
        """BBC MODE/VDU 20 default: white foreground on black background."""
        self._fg_colour = 7
        self._bg_colour = 0
        if self._gfx is not None:
            self._gfx.gcol_fg = (0, 7)
            self._gfx.gcol_bg = (0, 0)

    def set_mode(self, mode: int) -> None:
        self._mode = int(mode)
        self._apply_mode_spec(bbc_mode_spec(self._mode))
        self.reset_text_colours()
        self._reset_text_grid()
        self._cursor_row = 0
        self._cursor_col = 0
        if self._screen is not None:
            self._open_window(center=False)
            if self.is_graphics_mode():
                self._init_gfx()
            else:
                self._gfx = None
            self._refresh_font()
            self.clear()
            self.present()
            self.pump_events()
        else:
            self._refresh_font()

    def set_text_dimensions(self, cols: int, rows: int) -> None:
        self.text_cols = max(1, int(cols))
        self.text_rows = max(1, int(rows))
        self._cursor_row = min(self._cursor_row, self.text_rows - 1)
        self._cursor_col = min(self._cursor_col, self.text_cols - 1)
        self._reset_text_grid()
        if self._screen is not None and self._open:
            self._open_window(center=False)
        self._dirty = True

    def set_colour(self, colour: int) -> None:
        """BBC COLOUR / VDU 17 text colour.

        * ``0..7`` — foreground (and clear flash)
        * ``8..15`` — flashing foreground (logical colour ``n-8``)
        * ``128..255`` — background colour ``n-128`` (full index; MODE 8 palette)
        * ``136..143`` with logical 0-7 — classic flashing background

        ``COLOR 15+128`` (piechart sky) must keep index 15, not ``15 & 7`` → 7 gray.
        Hanoi MODE 3 still maps via ``map_mode_text_colour`` when blitting.
        """
        code = int(colour) & 255
        if code >= 128:
            logical = code - 128
            self._bg_colour = logical & 255
            self._text_flash = 136 <= code <= 143 and logical < 8
            if self._gfx is not None:
                self._gfx.gcol_bg = (0, self._bg_colour)
            return
        if code >= 8:
            self._fg_colour = (code - 8) & 7
            self._text_flash = True
            return
        self._fg_colour = code
        self._text_flash = False

    def goto(self, row: int, col: int) -> None:
        self._cursor_row = max(0, min(self.text_rows - 1, int(row)))
        self._cursor_col = max(0, min(self.text_cols - 1, int(col)))

    def write(self, text: str) -> None:
        if not text:
            return
        if self.is_teletext_mode():
            self._write_teletext(text)
            return
        if self.is_graphics_mode():
            if self._print_at_graphics:
                self._write_graphics_os_text(text)
            else:
                self._write_graphics_text(text)
            return
        for ch in text:
            if ch == '\n':
                self.newline()
                continue
            code = ord(ch)
            if code == 136:
                self._text_flash = True
                continue
            if code == 137:
                self._text_flash = False
                continue
            if self._cursor_col >= self.text_cols:
                self.newline()
            self._store_text_cell(ch)
            self._cursor_col += 1
        self.mark_compose_full()

    def _teletext_line_state(self) -> _TeletextLineState:
        row = max(0, min(self._cursor_row, self.text_rows - 1))
        return self._teletext_lines[row]

    def _write_teletext(self, text: str) -> None:
        for ch in text:
            if ch == '\n':
                self.newline()
                continue
            if self._cursor_col >= self.text_cols:
                self.newline()
            code = ord(ch)
            state = self._teletext_line_state()
            if code in TELETEXT_FG_COLOURS:
                state.fg = TELETEXT_FG_COLOURS[code]
                state.graphics = False
                self._cursor_col += 1
                continue
            if code in TELETEXT_GFX_COLOURS:
                state.gfx_fg = TELETEXT_GFX_COLOURS[code]
                state.graphics = True
                self._cursor_col += 1
                continue
            if code == 136:
                state.flash = True
                self._cursor_col += 1
                continue
            if code == 137:
                state.flash = False
                self._cursor_col += 1
                continue
            if code == 140:
                self._cursor_col += 1
                continue
            if code == 141:
                self._cursor_col += 1
                continue
            if code == 154:
                state.separated = True
                self._cursor_col += 1
                continue
            if code == 155:
                state.separated = False
                self._cursor_col += 1
                continue
            if code == 156:
                state.bg = 0
                self._cursor_col += 1
                continue
            if code == 157:
                state.bg = state.fg if not state.graphics else state.gfx_fg
                self._cursor_col += 1
                continue
            if code == 158:
                state.hold = True
                self._cursor_col += 1
                continue
            if code == 159:
                state.hold = False
                state.hold_pattern = None
                self._cursor_col += 1
                continue
            mosaic = teletext_mosaic_pattern(code)
            if mosaic is not None and state.graphics:
                if state.hold and state.hold_pattern is not None:
                    mosaic = state.hold_pattern
                elif state.hold:
                    state.hold_pattern = mosaic
                if not state.concealed:
                    self._text[self._cursor_row][self._cursor_col] = (
                        chr(code),
                        state.gfx_fg,
                        state.bg,
                        mosaic,
                        state.separated,
                        state.flash,
                    )
                self._cursor_col += 1
                continue
            if 32 <= code < 127 and not state.graphics:
                self._text[self._cursor_row][self._cursor_col] = (
                    ch,
                    state.fg,
                    state.bg,
                    -1,
                    False,
                    state.flash,
                )
                self._cursor_col += 1
                continue
            if 32 <= code < 127 and state.graphics:
                self._cursor_col += 1
                continue
            self._cursor_col += 1
        self.mark_compose_full()

    def _write_graphics_text(self, text: str) -> None:
        for ch in text:
            if ch == '\n':
                self.newline()
                continue
            code = ord(ch)
            if code == 136:
                self._text_flash = True
                continue
            if code == 137:
                self._text_flash = False
                continue
            if self._cursor_col >= self.text_cols:
                self.newline()
            self._store_text_cell(ch)
            self._cursor_col += 1
        # Text is composed onto the graphics canvas only on a full rebuild.
        # Patch presents (hand/line dirty rects) return early and skip
        # _blit_text_grid — so PRINT must force compose_full or digital/title
        # text never appears (Clock.bas MODE 8).
        self.mark_compose_full()

    def _write_graphics_os_text(self, text: str) -> None:
        """VDU 5: PRINT at the BBC graphics cursor using full GCOL (mode + colour).

        piechart uses ``GCOL 3,15`` (XOR) so labels invert against each slice —
        solid mode-0 colour 15 (sky) was hard to read. Burn into the framebuffer
        with the current GCOL action (not mode 0 only).
        """
        if self._gfx is None or not text:
            return
        mode, colour = self._gfx.gcol_fg
        gcol = (int(mode), int(colour) & 0xFF)
        x_user = int(self._gfx.cursor_x)
        y_user = int(self._gfx.cursor_y)
        step_x = self._effective_cell_width() * self._gfx.x_scale
        step_y = self._effective_cell_height() * self._gfx.y_scale
        for ch in text:
            if ch == '\n':
                y_user -= step_y
                continue
            self._plot_vdu5_glyph_to_gfx(ch, gcol, x_user, y_user)
            x_user += step_x
        self._gfx.cursor_x = x_user
        self._gfx.cursor_y = y_user
        self._dirty = True
        # Force full compose so a late VDU 5 label (e.g. test_fps4 "N fps") is not
        # lost on a dirty-rect path that only has soccerball fill dirtied earlier.
        self.mark_compose_full()

    def _plot_vdu5_glyph_to_gfx(
        self,
        ch: str,
        gcol: Tuple[int, int],
        user_x: int,
        user_y: int,
    ) -> None:
        """Plot one VDU 5 character into the palette framebuffer (top-left = cursor)."""
        if self._gfx is None:
            return
        from mini_basic.bbc_font import glyph_rows

        code = ord(ch) if ch else 0
        rows = self._user_chars.get(code)
        if rows is None:
            rows = glyph_rows(ch)
        cw = self._effective_cell_width()
        ch_h = self._effective_cell_height()
        scale_x = max(1, cw // 8)
        scale_y = max(1, ch_h // 8)
        # Cursor is top-left of cell in OS units (same as layer path).
        sx0, sy0 = self._gfx._to_screen(int(user_x), int(user_y))
        put = getattr(self._gfx, '_put_screen_pixel', None)
        if put is None:
            return
        for row_i, row_byte in enumerate(rows[:8]):
            for col_i in range(8):
                if not (row_byte & (0x80 >> col_i)):
                    continue
                for dy in range(scale_y):
                    for dx in range(scale_x):
                        put(
                            sx0 + col_i * scale_x + dx,
                            sy0 + row_i * scale_y + dy,
                            gcol,
                        )

    def _blit_graphics_print_layers(self) -> None:
        # Legacy path: layers may still hold text from older sessions; prefer empty.
        if not self._graphics_print_layers or self._gfx is None:
            return
        assert self._canvas is not None
        for ch, colour, abs_x, abs_y in self._graphics_print_layers:
            if hasattr(self._gfx, '_absolute_os_to_screen'):
                sx, sy = self._gfx._absolute_os_to_screen(abs_x, abs_y)
            else:
                sx, sy = self._gfx._to_screen(abs_x, abs_y)
            self._blit_glyph(ch, colour, sx, sy)

    def newline(self) -> None:
        self._cursor_row += 1
        self._cursor_col = 0
        if self._cursor_row >= self.text_rows:
            self._scroll_text()
        elif self.is_teletext_mode():
            self._teletext_lines[self._cursor_row].reset()
        self._dirty = True

    def _scroll_text(self) -> None:
        self._text.pop(0)
        if self.is_teletext_mode():
            self._teletext_lines.pop(0)
            self._teletext_lines.append(_TeletextLineState())
            blank: Tuple[object, ...] = (' ', 7, 0, -1, False, False)
        else:
            blank = (' ', self._fg_colour, False)
        self._text.append([blank for _ in range(self.text_cols)])
        self._cursor_row = self.text_rows - 1

    def gcol(self, mode: int, colour: int) -> None:
        if not self._plot_enabled or self._gfx is None:
            return
        self._gfx.gcol(mode, colour)
        if int(mode) == 0:
            self._apply_gfx_truecolour(int(colour))
        self._dirty = True

    def plot_code(self, code: int, x: int, y: int) -> None:
        if not self._plot_enabled or self._gfx is None:
            return
        self._gfx.plot_code(code, x, y)
        # Pixel patch only — keep _compose_full false so present can blit dirty rect.
        self._dirty = True

    def move_absolute(self, x: int, y: int) -> None:
        if not self._plot_enabled or self._gfx is None:
            return
        self._gfx.move_absolute(x, y)
        # Cursor-only: no pixel change; avoid forcing a full recompose.

    def move_relative(self, dx: int, dy: int) -> None:
        if not self._plot_enabled or self._gfx is None:
            return
        self._gfx.move_relative(dx, dy)

    def fill_rectangle(self, x: int, y: int, width: int, height: int) -> None:
        if not self._plot_enabled or self._gfx is None:
            return
        self._gfx.fill_rectangle(x, y, width, height)
        self._dirty = True

    def set_graphics_size(
        self,
        width: int,
        height: int,
        *,
        charx: int = 8,
        chary: int = 16,
        ncols: int = 16,
        charset: int = 0,
    ) -> None:
        """Resize graphics (VDU 23,22). charx/chary set text cell size and grid."""
        self.graphics_width = max(1, int(width))
        self.graphics_height = max(1, int(height))
        cx = max(1, int(charx))
        cy = max(1, int(chary))
        self.cell_width = cx
        self.cell_height = cy
        self.text_cols = max(1, self.graphics_width // cx)
        self.text_rows = max(1, self.graphics_height // cy)
        self._plot_enabled = True
        self._mode = 0  # custom / non-table mode
        self._reset_text_grid()
        self._cursor_row = 0
        self._cursor_col = 0
        self._init_gfx()
        if charset & 128:
            self._fg_colour = 0
            self._bg_colour = 7
        self._refresh_font()
        if self._screen is not None and self._open:
            self._open_window(center=False)
            self.clear()
        self.mark_compose_full()

    def set_palette_rgb(self, index: int, rgb: Tuple[int, int, int]) -> None:
        self._palette_rgb[int(index)] = tuple(int(channel) for channel in rgb[:3])
        self._palette_dirty = True

    def _apply_gfx_truecolour(self, colour: int) -> None:
        if not self._plot_enabled or self._gfx is None:
            return
        if colour >= 128:
            self._gfx.clear_truecolour()
            return
        custom = self._palette_rgb.get(int(colour))
        if custom is not None:
            self._gfx.set_truecolour(custom)
        else:
            self._gfx.clear_truecolour()

    def mouse_state(self) -> Tuple[int, int, int]:
        return self._mouse_x, self._mouse_y, self._mouse_buttons

    def _pixel_rgb(self, index: int) -> Tuple[int, int, int]:
        custom = self._palette_rgb.get(int(index))
        if custom is not None:
            return custom
        return colour_to_rgb(int(index))

    def draw_relative(self, dx: int, dy: int) -> None:
        if not self._plot_enabled or self._gfx is None:
            return
        self._gfx.draw_relative(dx, dy)
        self._dirty = True  # patch present OK

    def draw_absolute(self, x: int, y: int) -> None:
        if not self._plot_enabled or self._gfx is None:
            return
        self._gfx.draw_absolute(x, y)
        self._dirty = True

    def clear_graphics(self) -> None:
        if not self._plot_enabled:
            return
        self._sprite_placements = []
        # Do not clear VDU 5 print layers here — CLG does not erase prior
        # graphics-cursor text on a real Beeb; welcome keeps DISC SYSTEM.
        if self._gfx is not None:
            self._gfx.clear_graphics()
        self.mark_compose_full()

    def set_graphics_viewport(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """VDU 24 — store window and apply to CLG clipping."""
        if self._gfx is not None:
            self._gfx.set_graphics_viewport(x1, y1, x2, y2)

    def set_graphics_origin(self, x: int, y: int) -> None:
        if not self._plot_enabled or self._gfx is None:
            return
        self._gfx.set_origin(x, y)

    def point_colour(self, x: int, y: int) -> int:
        if not self._plot_enabled or self._gfx is None:
            return 0
        return self._gfx.point_colour(x, y)

    def plot(self, x: int, y: int, colour: Optional[int] = None) -> None:
        if not self._plot_enabled or self._gfx is None:
            return
        if colour is not None:
            self._gfx.gcol(self._gfx.gcol_fg[0], int(colour))
        self.plot_code(69, int(x), int(y))

    def define_sprite(
        self,
        sprite_id: int,
        pixels: Sequence[Sequence[int]],
    ) -> None:
        pygame = self._pygame
        height = len(pixels)
        width = len(pixels[0]) if height else 0
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for y, row in enumerate(pixels):
            for x, colour in enumerate(row):
                if colour < 0:
                    continue
                surface.set_at((x, y), colour_to_rgb(int(colour)))
        self._sprites[int(sprite_id)] = surface

    def draw_sprite(self, sprite_id: int, x: int, y: int) -> None:
        if self._sprites.get(int(sprite_id)) is None:
            return
        self._sprite_placements.append((int(sprite_id), int(x), int(y)))
        self._dirty = True

    def _blit_sprites(self) -> None:
        assert self._canvas is not None
        for sprite_id, x, y in self._sprite_placements:
            sprite = self._sprites.get(sprite_id)
            if sprite is None:
                continue
            self._canvas.blit(sprite, (x, y))

    def _render_text_mode(self) -> None:
        assert self._canvas is not None
        self._ensure_text_font()
        self._canvas.fill((0, 0, 0))
        if self.is_teletext_mode():
            self._blit_teletext_grid()
        else:
            self._blit_text_grid()

    def _text_cell_origin(self, row: int, col: int) -> Tuple[int, int]:
        cw = self._effective_cell_width()
        ch = self._effective_cell_height()
        x = col * cw
        if self.is_graphics_mode():
            return x, row * ch
        return x, row * ch

    def _blit_teletext_mosaic(
        self,
        x: int,
        y: int,
        pattern: int,
        fg: int,
        bg: int,
        separated: bool,
    ) -> None:
        assert self._canvas is not None
        cw = self._effective_cell_width()
        ch = self._effective_cell_height()
        fg_rgb = colour_to_rgb(fg)
        bg_rgb = colour_to_rgb(bg)
        # Partition cell exactly into 2 cols x 3 rows (sums to cw, ch)
        col_ws = [cw // 2 + (1 if i < (cw % 2) else 0) for i in range(2)]
        # Balanced thirds for better visual proportions (e.g. 20px -> [7,6,7])
        base = ch // 3
        rem = ch % 3
        row_hs = [base] * 3
        # Distribute remainder preferring ends for symmetry, then middle
        for k in range(rem):
            row_hs[[0, 2, 1][k]] += 1
        gap = 1 if separated else 0
        for sy in range(3):
            for sx in range(2):
                idx = sy * 2 + sx
                filled = teletext_sextant_filled(pattern, idx)
                rx = x + sum(col_ws[:sx]) + (gap if sx else 0)
                ry = y + sum(row_hs[:sy]) + (gap if sy else 0)
                rw = col_ws[sx] - gap
                rh = row_hs[sy] - gap
                colour = fg_rgb if filled else bg_rgb
                if rw > 0 and rh > 0:
                    self._canvas.fill(colour, (rx, ry, rw, rh))

    def _blit_teletext_grid(self) -> None:
        assert self._canvas is not None
        self._ensure_text_font()
        if self._font is None:
            return
        flash_on = (self._pygame.time.get_ticks() // 500) % 2 == 0
        cw = self._effective_cell_width()
        ch_h = self._effective_cell_height()
        for row in range(self.text_rows):
            for col in range(self.text_cols):
                cell = self._text[row][col]
                x, y = self._text_cell_origin(row, col)
                if len(cell) < 6:
                    ch, colour = cell[0], cell[1]
                    if ch == ' ':
                        continue
                    self._canvas.fill(
                        colour_to_rgb(self._bg_colour),
                        (x, y, cw, ch_h),
                    )
                    self._blit_glyph(ch, colour, x, y, clip_w=cw, clip_h=ch_h)
                    continue
                ch, fg, bg, mosaic, separated, flash = cell
                fg = self._display_text_colour(fg)
                bg = self._display_text_colour(bg)
                self._canvas.fill(colour_to_rgb(bg), (x, y, cw, ch_h))
                if flash and not flash_on:
                    continue
                if mosaic >= 0:
                    self._blit_teletext_mosaic(x, y, mosaic, fg, bg, separated)
                    continue
                if ch == ' ':
                    continue
                self._blit_glyph(ch, fg, x, y, clip_w=cw, clip_h=ch_h)

    @staticmethod
    def _contrasting_text_fg(fg: int, bg: int) -> int:
        """Pick a readable glyph colour on COLOUR backgrounds (hanoi discs).

        The original program never sets foreground — default white vanishes on
        yellow/cyan/white bars. Prefer black on light bars, white on dark.
        """
        light = {3, 6, 7}  # yellow, cyan, white
        if bg in light:
            return 0
        if fg == bg:
            return 7 if bg == 0 else 0
        return fg

    def _ensure_text_font(self) -> None:
        """Create pygame font when MOS 8×8 is not used (custom cell sizes)."""
        if self._use_mos_font():
            return
        if self._font is None:
            self._refresh_font()

    def _blit_text_grid(self) -> None:
        assert self._canvas is not None
        self._ensure_text_font()
        if not self._use_mos_font() and self._font is None:
            return  # no pygame yet — skip glyphs rather than assert
        cw = self._effective_cell_width()
        ch_h = self._effective_cell_height()
        flash_on = (self._pygame.time.get_ticks() // 500) % 2 == 0
        for row in range(self.text_rows):
            for col in range(self.text_cols):
                cell = self._text[row][col]
                ch, fg, bg, flash = self._decode_text_cell(cell)
                # Skip unwritten blanks (bg 0). Painted COLOUR backgrounds (hanoi)
                # store non-zero bg on spaces and must still fill.
                if ch == ' ' and bg == 0 and not flash:
                    continue
                x, y = self._text_cell_origin(row, col)
                fg = self._display_text_colour(fg)
                bg = self._display_text_colour(bg)
                if bg != 0 or ch != ' ':
                    self._canvas.fill(colour_to_rgb(bg), (x, y, cw, ch_h))
                # Flash dark half: keep background, omit glyph (BBC-style).
                if flash and not flash_on:
                    continue
                if ch == ' ':
                    continue
                glyph_fg = self._contrasting_text_fg(fg, bg)
                self._blit_glyph(ch, glyph_fg, x, y, clip_w=cw, clip_h=ch_h)

    def _ensure_np_palette(self):
        import numpy as np
        if not hasattr(self, '_np_palette') or getattr(self, '_palette_dirty', True):
            palette = []
            for i in range(256):
                custom = self._palette_rgb.get(i)
                if custom:
                    palette.append(custom)
                elif i < len(BBC_PALETTE):
                    palette.append(BBC_PALETTE[i])
                else:
                    palette.append((0, 0, 0))
            self._np_palette = np.array(palette, dtype=np.uint8)
            self._palette_dirty = False
        return self._np_palette

    def _pixels_as_numpy(self, pixels):
        """View or copy framebuffer as uint8 ndarray (H, W)."""
        import numpy as np
        if getattr(self._gfx, 'pixels_is_numpy', False):
            return pixels
        return np.asarray(pixels, dtype=np.uint8)

    def _render_graphics_mode(self, *, force_full: bool = True) -> None:
            assert self._canvas is not None and self._gfx is not None
            import time
            t0 = time.monotonic()
            pygame = self._pygame
            pixels = self._gfx.pixels
            h = self.graphics_height
            w = self.graphics_width
            dirty = None
            if not force_full and hasattr(self._gfx, 'peek_dirty_rect'):
                dirty = self._gfx.peek_dirty_rect()
            # Patch path only for pure pixel updates (no text/sprites/print layers).
            # force_full is set by mark_compose_full() after grid PRINT so text is
            # not skipped by the early return below.
            use_patch = (
                dirty is not None
                and not force_full
                and not self._graphics_print_layers
                and not self._sprite_placements
            )
            try:
                import numpy as np
                palette = self._ensure_np_palette()
                idx = self._pixels_as_numpy(pixels)
                rgb_layer = getattr(self._gfx, 'rgb_pixels', None)

                if use_patch:
                    x0, y0, x1, y1 = dirty
                    # Expand 1px so scaled/adjacent ink does not leave holes.
                    x0 = max(0, x0 - 1)
                    y0 = max(0, y0 - 1)
                    x1 = min(w - 1, x1 + 1)
                    y1 = min(h - 1, y1 + 1)
                    patch = idx[y0 : y1 + 1, x0 : x1 + 1]
                    rgb = palette[patch]
                    if rgb_layer is not None and self._gfx.rgb_dirty:
                        # rgb_dirty entries are (sx, sy) screen coords (see bbc_graphics).
                        for sx, sy in list(self._gfx.rgb_dirty):
                            if y0 <= sy <= y1 and x0 <= sx <= x1:
                                if 0 <= sy < h and 0 <= sx < w:
                                    val = rgb_layer[sy][sx]
                                    if val is not None:
                                        rgb[sy - y0, sx - x0] = val
                    if rgb.size:
                        surf = pygame.surfarray.make_surface(
                            np.transpose(rgb, (1, 0, 2))
                        )
                        self._canvas.blit(surf, (x0, y0))
                    if hasattr(self._gfx, 'consume_dirty_rect'):
                        self._gfx.consume_dirty_rect()
                    t3 = time.monotonic()
                    if DEBUG:
                        print(
                            f"DEBUG render patch: {x1-x0+1}x{y1-y0+1} "
                            f"total={t3-t0:.3f}",
                            flush=True,
                        )
                    return

                t1 = time.monotonic()
                rgb = palette[idx]
                t2 = time.monotonic()
                if rgb_layer is not None:
                    # rgb_dirty entries are (sx, sy) screen coords (see bbc_graphics).
                    for sx, sy in self._gfx.rgb_dirty:
                        if 0 <= sy < h and 0 <= sx < w:
                            val = rgb_layer[sy][sx]
                            if val is not None:
                                rgb[sy, sx] = val
                surf = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
                self._canvas.blit(surf, (0, 0))
                if hasattr(self._gfx, 'consume_dirty_rect'):
                    self._gfx.consume_dirty_rect()
                t3 = time.monotonic()
                if DEBUG:
                    print(
                        f"DEBUG render full: blit={t3-t2:.3f} total={t3-t0:.3f}",
                        flush=True,
                    )
            except ImportError:
                # No numpy: still prefer dirty-rect updates over full scans.
                rgb_layer = getattr(self._gfx, 'rgb_pixels', None)
                if use_patch:
                    x0, y0, x1, y1 = dirty
                    x0 = max(0, x0 - 1)
                    y0 = max(0, y0 - 1)
                    x1 = min(w - 1, x1 + 1)
                    y1 = min(h - 1, y1 + 1)
                    for sy in range(y0, y1 + 1):
                        for sx in range(x0, x1 + 1):
                            colour = int(self._gfx.pixels[sy][sx])
                            if rgb_layer is not None and rgb_layer[sy][sx] is not None:
                                self._canvas.set_at((sx, sy), rgb_layer[sy][sx])
                            else:
                                self._canvas.set_at((sx, sy), self._pixel_rgb(colour))
                    if hasattr(self._gfx, 'consume_dirty_rect'):
                        self._gfx.consume_dirty_rect()
                    return
                self._canvas.fill((0, 0, 0))
                for sy in range(self.graphics_height):
                    for sx in range(self.graphics_width):
                        colour = int(self._gfx.pixels[sy][sx])
                        if colour == 0:
                            continue
                        if rgb_layer is not None and rgb_layer[sy][sx] is not None:
                            self._canvas.set_at((sx, sy), rgb_layer[sy][sx])
                        else:
                            self._canvas.set_at((sx, sy), self._pixel_rgb(colour))
                if hasattr(self._gfx, 'consume_dirty_rect'):
                    self._gfx.consume_dirty_rect()
            self._blit_graphics_print_layers()
            self._blit_text_grid()
            self._blit_sprites()

    def mark_dirty(self) -> None:
        self._dirty = True

    def mark_compose_full(self) -> None:
        """Text / sprites / MODE changed — next present rebuilds the whole canvas."""
        self._compose_full = True
        self._dirty = True

    def present(self, *, force: bool = False) -> None:
        if not self._open or self._screen is None or self._canvas is None:
            return
        if force or self._dirty:
            logical_w, logical_h = self._logical_canvas_size()
            if self._canvas.get_width() != logical_w or self._canvas.get_height() != logical_h:
                self._canvas = self._pygame.Surface((logical_w, logical_h))
                self._compose_full = True
            if self.is_graphics_mode():
                self._render_graphics_mode(force_full=force or self._compose_full)
            else:
                self._render_text_mode()
                self._compose_full = False
            target_w, target_h = self._screen.get_width(), self._screen.get_height()
            scaled = self._scale_surface(self._canvas, target_w, target_h)
            self._screen.fill((0, 0, 0))
            self._screen.blit(scaled, (0, 0))
            self._pygame.display.flip()
            self._dirty = False
            self._compose_full = False
        if self._clock is not None:
            # fps_limit 0: measure interval only (no cap); >0: cap frame rate.
            # During pure plot patches, skip tick when fps_limit would only add wait —
            # still tick if a limit is set so we do not free-run the GPU path.
            if self.fps_limit > 0:
                self._clock.tick(self.fps_limit)
            else:
                self._clock.tick(0)

    def _update_mouse_state(self) -> None:
        if not self._open or self._gfx is None:
            return
        pygame = self._pygame
        buttons = pygame.mouse.get_pressed(3)
        self._mouse_buttons = sum(bit << index for index, bit in enumerate(buttons))
        screen_x, screen_y = pygame.mouse.get_pos()
        if self._screen is None:
            return
        logical_w, logical_h = self._logical_canvas_size()
        if self._screen.get_width() <= 0 or self._screen.get_height() <= 0:
            return
        sx = int(screen_x * logical_w / self._screen.get_width())
        sy = int(screen_y * logical_h / self._screen.get_height())
        self._mouse_x, self._mouse_y = self._gfx.from_screen(sx, sy)

    def poll(self) -> bool:
        if not self._open:
            return False
        if os.environ.get('SDL_VIDEODRIVER', '').lower() == 'dummy':
            return True
        pygame = self._pygame
        pygame.event.pump()
        preserved = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._open = False
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._open = False
                return False
            preserved.append(event)
        for event in preserved:
            pygame.event.post(event)
        self._update_mouse_state()
        return True

    def read_line(
        self,
        *,
        max_length: int = 255,
        tee: Optional[Callable[[str], None]] = None,
    ) -> str:
        pygame = self._pygame
        if not self._open or os.environ.get('SDL_VIDEODRIVER', '').lower() == 'dummy':
            return ''
        buffer: List[str] = []
        limit = max(1, int(max_length))
        pygame.key.start_text_input()
        try:
            while self._open:
                pygame.event.pump()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self._open = False
                        return ''
                    if event.type == pygame.TEXTINPUT:
                        # Printables only via TEXTINPUT (not KEYDOWN too —
                        # duplicate handling used to drop repeated digits).
                        for ch in event.text:
                            if not ch.isprintable():
                                continue
                            if len(buffer) >= limit:
                                break
                            buffer.append(ch)
                            self.write(ch)
                            self.present()
                            if tee is not None:
                                tee(ch)
                        continue
                    if event.type != pygame.KEYDOWN:
                        continue
                    if event.key == pygame.K_ESCAPE:
                        raise KeyboardInterrupt
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.newline()
                        self._dirty = True
                        self.present()
                        if tee is not None:
                            tee('\n')
                        return ''.join(buffer)
                    if event.key == pygame.K_BACKSPACE:
                        if buffer:
                            buffer.pop()
                            self._erase_cursor_cell()
                            self.present()
                            if tee is not None:
                                tee('\b')
                        continue
                    # Ignore other KEYDOWN printables while TEXTINPUT is active.
                    continue
                if self._dirty:
                    self.present()
                if self._clock is not None and self.fps_limit > 0:
                    self._clock.tick(self.fps_limit)
        finally:
            pygame.key.stop_text_input()
        return ''.join(buffer)

    def hold_open(self) -> None:
        if not self._open or self._screen is None:
            return
        pygame = self._pygame
        pygame.display.set_caption(
            f'{self.caption} ({self.scale}x) — press Escape to close'
        )
        self.present()
        while self._open:
            if not self.poll():
                break
            self.present()

    def capture_framebuffer(self) -> List[List[int]]:
        if self._gfx is None:
            return []
        pixels = self._gfx.pixels
        if getattr(self._gfx, 'pixels_is_numpy', False):
            return pixels.tolist()
        return [list(row) for row in pixels]

    def _surface_rgb_rows(self, surface) -> List[List[Tuple[int, int, int]]]:
        width = surface.get_width()
        height = surface.get_height()
        rows: List[List[Tuple[int, int, int]]] = []
        for y in range(height):
            row: List[Tuple[int, int, int]] = []
            for x in range(width):
                colour = surface.get_at((x, y))
                row.append((int(colour[0]), int(colour[1]), int(colour[2])))
            rows.append(row)
        return rows

    def capture_canvas_rgb(self) -> Tuple[int, int, List[List[Tuple[int, int, int]]]]:
        if self._gfx is None:
            return 0, 0, []
        logical_w, logical_h = self._logical_canvas_size()
        if self._canvas is None or (
            self._canvas.get_width() != logical_w
            or self._canvas.get_height() != logical_h
        ):
            self._canvas = self._pygame.Surface((logical_w, logical_h))
        if self._open:
            self.present()
        elif self.is_graphics_mode():
            self._render_graphics_mode()
        else:
            self._render_text_mode()
        rows = self._surface_rgb_rows(self._canvas)
        return logical_w, logical_h, rows

    def capture_screen_rgb(self) -> Tuple[int, int, List[List[Tuple[int, int, int]]]]:
        if not self._open or self._screen is None:
            return self.capture_canvas_rgb()
        self.present()
        rows = self._surface_rgb_rows(self._screen)
        return self._screen.get_width(), self._screen.get_height(), rows


def desktop_size(pygame) -> Tuple[int, int]:
    sizes = pygame.display.get_desktop_sizes()
    if sizes:
        return sizes[0]
    info = pygame.display.Info()
    return info.current_w or 1920, info.current_h or 1080


def fit_display_scale(
    base_w: int,
    base_h: int,
    requested_scale: int,
    *,
    max_scale: int = 3,
) -> int:
    """Pick the largest pixel scale that should fit on screen."""
    try:
        import pygame

        if not pygame.get_init():
            os.environ.setdefault('SDL_VIDEO_CENTERED', '1')
            pygame.init()
        screen_w, screen_h = desktop_size(pygame)
    except Exception:
        return max(1, min(requested_scale, max_scale))

    limit_w = screen_w - _WINDOW_CHROME_WIDTH - _WINDOW_MARGIN
    limit_h = screen_h - _WINDOW_CHROME_HEIGHT - _WINDOW_MARGIN
    fit = min(
        limit_w // max(1, base_w),
        limit_h // max(1, base_h),
        max_scale,
        max(1, requested_scale),
    )
    return max(1, fit)


def auto_display_scale(
    *,
    graphics_width: int = 320,
    graphics_height: int = 256,
    text_cols: int = 40,
    text_rows: int = 24,
    cell_size: int = 8,
    max_scale: int = 3,
) -> int:
    """Pick the largest scale that keeps the pygame window fully visible."""
    base_w = max(graphics_width, text_cols * cell_size)
    base_h = max(graphics_height, text_rows * cell_size)
    return fit_display_scale(base_w, base_h, max_scale, max_scale=max_scale)


def create_display(
    backend: str,
    *,
    text_cols: int = 80,
    text_rows: int = 30,
    graphics_width: int = 320,
    graphics_height: int = 256,
    scale: int = 2,
    scale_locked: bool = False,
    caption: str = 'mini_basic',
    fps_limit: int = 60,
) -> DisplayBackend:
    if backend in ('none', 'null'):
        return NullDisplay()
    if backend in ('', 'terminal'):
        return TerminalDisplay(text_cols=text_cols, text_rows=text_rows)
    if backend == 'pygame':
        return PygameDisplay(
            text_cols=text_cols,
            text_rows=text_rows,
            graphics_width=graphics_width,
            graphics_height=graphics_height,
            scale=scale,
            scale_locked=scale_locked,
            caption=caption,
            fps_limit=max(0, int(fps_limit)),
        )
    raise ValueError(f'unknown display backend: {backend}')


def ensure_no_pygame_leftovers() -> None:
    """Force-kill any active pygame state to prevent leftover SDL windows.

    Especially important in autonomous agent runs, scheduled heartbeats,
    test probes, and after crashes. Safe to call unconditionally.

    In cooperative (user-present) mode, the user may intentionally keep
    a window open via hold_display_open; this should not be called until
    the user has confirmed they are done.
    """
    try:
        import pygame  # type: ignore
        if pygame.get_init():
            try:
                pygame.display.quit()
            except Exception:
                pass
            try:
                pygame.quit()
            except Exception:
                pass
    except Exception:
        # pygame not installed or other import/runtime issue; ignore
        pass
