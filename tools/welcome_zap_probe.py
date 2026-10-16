#!/usr/bin/env python3
"""Non-interactive probe: welcome swoosh end positions vs letter target.

Runs the same integer math as PROCSWOOSH (M8 steps), optionally executes it
under the BBC interpreter with final invert-erase skipped, and prints a table.

Usage:
  python tools/welcome_zap_probe.py
  python tools/welcome_zap_probe.py --run-gfx   # also exercise PLOT 6 path
"""
from __future__ import annotations

import argparse
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# welcome.bbc constants
M0, M1, M2, M3, M4, M5, M8 = 650, 500, 708, 104, 288, 550, 5


def swoosh_ends(i: int, y: int, m8: int = M8) -> dict:
    """Integer steps matching welcome PROCSWOOSH after FOR J0%=1 TO M8."""
    xl, xr, yd, yu = 0, 1272, 0, 1020
    u1 = (i + 32 - xl) // m8
    v1 = (y - 16 - yd) // m8
    u2 = (i + 32 - xr) // m8
    v2 = (y - 16 - yu) // m8
    x1 = x2 = xl
    x3 = x4 = xr
    y1 = y3 = yd
    y2 = y4 = yu
    for _ in range(m8):
        x1 += u1
        x2 += u1
        x3 += u2
        x4 += u2
        y1 += v1
        y2 += v2
        y3 += v1
        y4 += v2
    tx, ty = i + 32, y - 16
    return {
        "I%": i,
        "Y%": y,
        "tgt": (tx, ty),
        "X1,Y1": (x1, y1),
        "X2,Y2": (x2, y2),
        "X3,Y3": (x3, y3),
        "X4,Y4": (x4, y4),
        "d1": (x1 - tx, y1 - ty),
        "d2": (x2 - tx, y2 - ty),
        "d3": (x3 - tx, y3 - ty),
        "d4": (x4 - tx, y4 - ty),
        "U1,V1": (u1, v1),
        "U2,V2": (u2, v2),
    }


def print_table(rows: list[dict]) -> None:
    print(
        f"{'I%':>5} {'Y%':>4} {'tgt':>12} {'X1,Y1':>12} {'d1':>10} "
        f"{'X3,Y3':>12} {'d3':>10}"
    )
    for r in rows:
        print(
            f"{r['I%']:5d} {r['Y%']:4d} "
            f"{str(r['tgt']):>12} {str(r['X1,Y1']):>12} {str(r['d1']):>10} "
            f"{str(r['X3,Y3']):>12} {str(r['d3']):>10}"
        )
    print()
    print("Note: welcome ends with an extra PROCPLOT that invert-erases the rays.")
    print("Letter sits at MOVE I%,Y (block) / text near I%+6,Y+2 — ray target is I%+32,Y-16.")


def run_gfx_once() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    from mini_basic import BASICInterpreter, InterpreterConfig

    interp = BASICInterpreter(
        InterpreterConfig(
            dialect="bbc",
            display="pygame",
            display_locked=True,
            hold_display_open=False,
        )
    )
    interp._shutdown_display = lambda **k: None  # type: ignore[method-assign]
    # One swoosh, no final erase; report vars from interpreter.
    prog = {
        10: "MODE 5",
        20: "M8=5:I%=500:Y%=650",
        30: "GCOL 0,135:CLG",
        40: "PROCSWOOSH(Y%)",
        50: 'PRINT "X1=";X1%;" Y1=";Y1%;" X3=";X3%;" Y3=";Y3%',
        60: 'PRINT "tgt=";I%+32;",";Y%-16',
        70: "END",
        100: "DEF PROCSWOOSH(Y%)",
        110: "XL%=0:XR%=1272:YD%=0:YU%=1020",
        120: "U1%=(I%+32-XL%) DIV M8:V1%=(Y%-16-YD%) DIV M8",
        130: "U2%=(I%+32-XR%) DIV M8:V2%=(Y%-16-YU%) DIV M8",
        140: "X1%=XL%:X2%=XL%:X3%=XR%:X4%=XR%:Y1%=YD%:Y2%=YU%:Y3%=YD%:Y4%=YU%",
        150: "PROCPLOT",
        160: "FOR J0%=1 TO M8",
        170: "PROCPLOT",
        180: "X1%=X1%+U1%:X2%=X2%+U1%:X3%=X3%+U2%:X4%=X4%+U2%",
        190: "Y1%=Y1%+V1%:Y2%=Y2%+V2%:Y3%=Y3%+V1%:Y4%=Y4%+V2%",
        200: "PROCPLOT",
        210: "NEXT",
        220: "ENDPROC",
        240: "DEF PROCPLOT",
        250: "MOVE X1%-U1%,Y1%-V1%:PLOT 6,X1%,Y1%:MOVE X2%-U1%,Y2%-V2%:PLOT 6,X2%,Y2%",
        260: "MOVE X3%-U2%,Y1%-V1%:PLOT 6,X3%,Y3%:MOVE X4%-U2%,Y4%-V2%:PLOT 6,X4%,Y4%",
        270: "ENDPROC",
    }
    out = StringIO()
    with redirect_stdout(out), redirect_stderr(StringIO()), patch("time.sleep"):
        for n, s in prog.items():
            interp.program[n] = s
        interp.run()
    print("--- interpreter after I%=500 swoosh (no final erase) ---")
    print(out.getvalue().strip())
    exp = swoosh_ends(500, 650)
    print("expected", exp["X1,Y1"], exp["X3,Y3"], "tgt", exp["tgt"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--run-gfx",
        action="store_true",
        help="Also run one swoosh under pygame dummy display",
    )
    args = ap.parse_args()

    print("=== BBC letter row (PROCSWOOSH M0=650) ===")
    rows = [swoosh_ends(i, M0) for i in range(M1, M2 + 1, M3)]
    print_table(rows)

    print("=== DISC SYSTEM row (PROCSWOOSH M5=550) ===")
    rows = [swoosh_ends(M4 + 64 * j, M5) for j in range(11)]
    print_table(rows)

    if args.run_gfx:
        run_gfx_once()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
