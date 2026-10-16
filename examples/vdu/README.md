# VDU demo programs (Phases A–C)

These examples show the **VDU control codes** implemented for mini_basic 1.00 work
(see `docs/PLAN_1.00_AND_VDU.md`). Each program is self-explaining: run it and read
the on-screen captions / REM lines.

**Layout:** every step does `CLS` (or `VDU 26` + `CLS`) so captions stay full-screen.
Inside a text window (`VDU 28`) only short markers are printed, then the window is
reset — that avoids the overlapping mess of printing long explanations inside the viewport.

## How to run

From the mini_basic repo root (use **pytest** for tests; these are demos):

```powershell
# Phase A — colour, cursor, bell, colour/viewport reset
python -m mini_basic --dialect bbc examples/vdu/phase_a_colour_cursor.bas

# Phase B — text + graphics windows
python -m mini_basic --dialect bbc examples/vdu/phase_b_viewports.bas

# Phase C — VDU 23 known + unknown stubs
python -m mini_basic --dialect bbc examples/vdu/phase_c_vdu23.bas
```

Optional:

- `--display pygame` or allow auto-pygame on a desktop
- `--display terminal` for text-only (graphics bits may be limited)
- `WAIT` pauses so you can read each step; press **Ctrl+C** in the terminal to stop

## Phase map

| Program | Codes demonstrated |
|---------|-------------------|
| `phase_a_colour_cursor.bas` | 7, 8–11, 12, 13, 17, 20, 26, 30, 31 |
| `phase_b_viewports.bas` | 24, 26, 28, 30, 31 |
| `phase_c_vdu23.bas` | 23,1 · 23,22 · 23,0 / 23,16 stubs |

Full VDU reference table: `examples/vducodes.txt`.

MODE 7 teletext test page (implemented + **[F]**uture rows):

```powershell
python -m mini_basic --dialect bbc --display pygame examples/teletext/mode7_test_screen.bas
```

See `examples/teletext/README.md` and `pytest -q test/test_teletext_screen.py`.
