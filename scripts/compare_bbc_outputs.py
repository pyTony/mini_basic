#!/usr/bin/env python3
"""Capture text output from mini_basic --dialect bbc for comparison to real BBCSDL.

Usage:
  python compare_bbc_outputs.py test/corpus/bbcsdl/samples/tier_a_poem.txt
  python compare_bbc_outputs.py --all-text   # run several and save to compare_out/

Also prints the command needed to run the same program in real BBC BASIC for SDL 2.0.
"""
from __future__ import annotations

import argparse
import io
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mini_basic import BASICInterpreter, InterpreterConfig  # type: ignore

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

# Optional: set BBCSDL_EXE to the real BBC BASIC for SDL 2.0 binary on this machine.
BBCSDL = os.environ.get(
    'BBCSDL_EXE',
    r'C:\Program Files (x86)\BBC BASIC for SDL 2.0\bbcsdl.exe',
)

TEXT_CANDIDATES = [
    "test/corpus/bbcsdl/samples/tier_a_poem.txt",
    # Add more as we validate they are mostly text + terminate
]


def capture_output(path: str, display: str = "none") -> str:
    interp = BASICInterpreter(
        InterpreterConfig(dialect="bbc", display=display, optimization_level=0)
    )
    interp.load(path)
    buf = io.StringIO()
    with redirect_stdout(buf):
        interp.run()
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("program", nargs="?", help="path to .txt or .bas BBC program")
    ap.add_argument("--all-text", action="store_true", help="run known text candidates")
    ap.add_argument("--outdir", default="compare_out", help="directory for saved outputs")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(exist_ok=True)

    programs: list[str] = []
    if args.program:
        programs = [args.program]
    if args.all_text:
        programs = TEXT_CANDIDATES

    if not programs:
        print("Specify a program or --all-text")
        return 1

    for prog in programs:
        p = Path(prog)
        if not p.exists():
            print(f"? not found: {prog}")
            continue
        print(f"\n=== {prog} ===")
        try:
            out = capture_output(str(p))
            print("MINI OUTPUT (repr):")
            print(repr(out[:2000]))
            # save
            safe = p.name.replace("/", "_")
            (outdir / f"{safe}.mini.txt").write_text(out, encoding="utf-8")
            print(f"(saved to {outdir / (safe + '.mini.txt')})")
        except Exception as exc:
            print(f"RUN ERR: {exc}")
            continue

        print("\nTo compare with real BBC BASIC SDL 2.0 run:")
        print(f'  "{BBCSDL}" "{p.resolve()}"')
        print("  (Observe in SDL window or screenshot it. For loggable text: use wrap_bbcsdl_spool.py or manually add OSCLI SPOOL + *SPOOL around the body in a copy, run, then close the window and read the spool file.)")
        print("  Numbered wrapper example (more reliable load): C:\\temp\\bbc_test\\poem_numbered.bbc (adjust spool path inside)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
