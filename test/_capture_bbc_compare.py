"""Internal: capture outputs for several bbcsdl corpus entries using --dialect bbc display=none."""
import io
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from mini_basic import BASICInterpreter, InterpreterConfig

CORPUS = _ROOT / "test" / "corpus" / "bbcsdl"

PROGRAMS = [
    "samples/tier_a_poem.txt",
    # fast or early-printing ones only for quick compare runs
]

def run_one(rel: str):
    p = CORPUS / rel
    if not p.exists():
        return rel, None, f"missing: {p}"
    interp = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none", optimization_level=0))
    try:
        interp.load(str(p))
    except Exception as e:
        return rel, None, f"load-err: {e}"
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            interp.run()
        return rel, buf.getvalue(), None
    except Exception as e:
        return rel, buf.getvalue(), f"run-err: {e}"

def main():
    results = []
    for prog in PROGRAMS:
        name, out, err = run_one(prog)
        results.append((name, out, err))
    for name, out, err in results:
        print("=" * 60)
        print("PROGRAM:", name)
        if err:
            print("ERROR:", err)
        if out:
            short = out if len(out) < 1200 else out[:1200] + "...[truncated]"
            print("OUTPUT:")
            print(short)
        print()

if __name__ == "__main__":
    main()
