"""BBC Micro MODE specifications (resolution, PAR, text grid).

References: BeebWiki MODE pages; RISC OS BBC BASIC Teletext chapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# Teletext control codes (MODE 7) — RISC OS BBC BASIC manual ch.21.
TELETEXT_FG_COLOURS: Dict[int, int] = {
    129: 1,  # red
    130: 2,  # green
    131: 3,  # yellow
    132: 4,  # blue
    133: 5,  # magenta
    134: 6,  # cyan
    135: 7,  # white
}
TELETEXT_GFX_COLOURS: Dict[int, int] = {
    145: 1,
    146: 2,
    147: 3,
    148: 4,
    149: 5,
    150: 6,
    151: 7,
}

# Mosaic block graphics: 160-191 and 224-255 (2×3 sextant grid, base 160).
TELETEXT_MOSAIC_BASE = 160
TELETEXT_MOSAIC_ALT_BASE = 224

# Sextant bit weights (top-left through bottom-right).
_TELETEXT_SEXTANT_BITS = (1, 2, 4, 8, 16, 32)


@dataclass(frozen=True)
class BBCModeSpec:
    gfx_width: int
    gfx_height: int
    text_cols: int
    text_rows: int
    cell_width: int
    cell_height: int
    par_w: int
    par_h: int
    plot_enabled: bool
    teletext: bool = False

    def logical_canvas_size(self) -> Tuple[int, int]:
        if self.plot_enabled and self.gfx_width > 0:
            return self.gfx_width, self.gfx_height
        return self.text_cols * self.cell_width, self.text_rows * self.cell_height

    def par_display_size(self) -> Tuple[int, int]:
        """Canvas size after pixel-aspect correction (before window scale)."""
        w, h = self.logical_canvas_size()
        if self.teletext:
            return w, h * self.par_h // max(1, self.par_w)
        return w * self.par_w // max(1, self.par_h), h


BBC_MODE_SPECS: Dict[int, BBCModeSpec] = {
    # Graphics modes 0-2 (Model B, 20 KB screen)
    0: BBCModeSpec(640, 256, 80, 32, 8, 8, 1, 2, True),
    1: BBCModeSpec(320, 256, 40, 32, 8, 8, 1, 1, True),
    2: BBCModeSpec(160, 256, 20, 32, 8, 8, 2, 1, True),
    # Text-only bitmapped (PLOT/CLG disabled on real hardware)
    3: BBCModeSpec(0, 0, 80, 25, 8, 10, 1, 2, False),
    # Model A graphics (10 KB screen)
    4: BBCModeSpec(320, 256, 40, 32, 8, 8, 1, 1, True),
    5: BBCModeSpec(160, 256, 20, 32, 8, 8, 2, 1, True),
    6: BBCModeSpec(0, 0, 40, 25, 8, 10, 1, 1, False),
    # Teletext (SAA 5050): 40×25, 16×20 pixel cells (640×500 screen pixels) for wider-than-tall window
    7: BBCModeSpec(0, 0, 40, 25, 16, 20, 1, 1, False, teletext=True),
}

# BBC BASIC for Windows / SDL 2.0 extended modes (manual ch.3 table).
# Tuple: gfx_w, gfx_h, text_cols, text_rows
_BB4W_MODE_TABLE: Dict[int, Tuple[int, int, int, int]] = {
    8: (640, 512, 80, 32),
    9: (640, 512, 40, 32),
    10: (720, 576, 90, 36),
    11: (720, 576, 45, 36),
    12: (960, 768, 120, 48),
    13: (960, 768, 60, 48),
    14: (1280, 1024, 160, 64),
    15: (1280, 1024, 80, 64),
    16: (640, 400, 80, 25),
    17: (640, 400, 40, 25),
    18: (640, 480, 80, 30),
    19: (640, 480, 40, 30),
    20: (800, 600, 100, 30),
    21: (800, 600, 50, 30),
    22: (1024, 768, 128, 48),
    23: (1024, 768, 64, 48),
    24: (1152, 864, 144, 54),
    25: (1152, 864, 72, 54),
    26: (1280, 960, 160, 60),
    27: (1280, 960, 80, 60),
    28: (1440, 1080, 180, 54),
    29: (1440, 1080, 90, 54),
    30: (1600, 1200, 200, 75),
    31: (1600, 1200, 100, 75),
    32: (640, 400, 80, 25),
    33: (640, 400, 40, 25),
}

BB4W_MODE_SPECS: Dict[int, BBCModeSpec] = {
    # SDL/VGA modes use square pixels (4:3 / 5:4 landscape on a PC monitor).
    mode: BBCModeSpec(gfx_w, gfx_h, cols, rows, 8, 8, 1, 1, True)
    for mode, (gfx_w, gfx_h, cols, rows) in _BB4W_MODE_TABLE.items()
}


def bbc_mode_spec(mode: int) -> Optional[BBCModeSpec]:
    key = int(mode)
    if key in BBC_MODE_SPECS:
        return BBC_MODE_SPECS[key]
    return BB4W_MODE_SPECS.get(key)


# Physical text colour depth per BBC mode (see HELP MODES).
MODE_TEXT_COLOUR_DEPTH: Dict[int, int] = {
    0: 2,
    1: 4,
    2: 8,
    # Real Beeb MODE 3/6 are 2-colour hardware, but COLOUR/VDU 17 disc
    # demos (hanoi) need the full 0..7 logical palette on PC displays.
    # Depth 2 collapsed every non-zero colour to white → white digits on
    # white disc bars (invisible) while spaces were also skipped in blit.
    3: 8,
    4: 2,
    5: 4,
    6: 8,
    7: 8,
}

# Default BBC 4-colour mode logical palette (black, red, yellow, white).
_MODE4_TEXT_COLOURS: Tuple[int, ...] = (0, 1, 3, 7)


def map_mode_text_colour(logical: int, mode: int) -> int:
    """Map a BBC logical COLOUR value to the physical palette for the active MODE."""
    code = int(logical) & 255
    if mode >= 8:
        return code
    depth = MODE_TEXT_COLOUR_DEPTH.get(mode)
    if depth is None:
        return code
    if depth == 2:
        return 0 if code == 0 else 7
    if depth == 4:
        return _MODE4_TEXT_COLOURS[code & 3]
    if depth == 8:
        return code & 7
    return code


# BBC MOS graphics units (same for all modes); mapped to pixels per mode.
BBC_OS_X_UNITS = 1280
BBC_OS_Y_UNITS = 1024


def bbc_os_scales(gfx_width: int, gfx_height: int) -> Tuple[int, int]:
    """Return (x_scale, y_scale): OS units per pixel.

    Standard sizes that divide 1280×1024 use matching integer scales
    (e.g. MODE 8 640×512 → 2,2). Mixed scales (old 640×480 → 2,1) elongate
    circles and skew MOUSE vs MOVE (jclock VDU 23,22,640;480). Prefer a
    *uniform* scale when only one axis divides the classical OS grid; other
    custom sizes use 1:1.
    """
    width = max(1, int(gfx_width))
    height = max(1, int(gfx_height))
    x_ok = BBC_OS_X_UNITS % width == 0
    y_ok = BBC_OS_Y_UNITS % height == 0
    if x_ok and y_ok:
        return BBC_OS_X_UNITS // width, BBC_OS_Y_UNITS // height
    if x_ok:
        scale = BBC_OS_X_UNITS // width
        return scale, scale
    if y_ok:
        scale = BBC_OS_Y_UNITS // height
        return scale, scale
    if width == 320 and height == 256:
        return 4, 4
    if width == 160 and height == 256:
        return 8, 8
    return 1, 1


def teletext_mosaic_pattern(code: int) -> Optional[int]:
    """Return 6-bit sextant mask for teletext mosaic character, or None."""
    if TELETEXT_MOSAIC_BASE <= code <= TELETEXT_MOSAIC_BASE + 31:
        return code - TELETEXT_MOSAIC_BASE
    if TELETEXT_MOSAIC_ALT_BASE <= code <= TELETEXT_MOSAIC_ALT_BASE + 31:
        return code - TELETEXT_MOSAIC_ALT_BASE
    return None


def teletext_sextant_filled(pattern: int, index: int) -> bool:
    if index < 0 or index >= len(_TELETEXT_SEXTANT_BITS):
        return False
    return bool(pattern & _TELETEXT_SEXTANT_BITS[index])
