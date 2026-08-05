"""Audit cryptic ? messages and silent exception handlers."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("mini_basic")
SKIP = {"runtime_bak.py", "__pycache__"}


def main() -> None:
    bare: list[tuple[str, int, str]] = []
    short_q: list[tuple[str, int, str]] = []
    silent: list[tuple[str, int, str, str]] = []

    for path in sorted(ROOT.rglob("*.py")):
        if any(s in path.parts for s in SKIP) or path.name in SKIP:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            s = line.strip()
            if re.search(r"""print\(\s*['"]\?['"]\s*\)""", s):
                bare.append((str(path), i, s))
            m = re.search(r"""print\(\s*['"](\?[^'"]*)['"]""", s)
            if m:
                msg = m.group(1)
                # short cryptic: "? " + little detail, or just generic labels
                if msg == "?" or re.fullmatch(
                    r"\? (SAVE|LOAD|LIST|DIR|CD|EDIT|AUTO|CASE|DIALECT|OPEN|GET|PUT|FIELD|"
                    r"EXIT|RESUME|DEF)( error| path| filename)?",
                    msg,
                ):
                    short_q.append((str(path), i, s))
            if re.match(r"except\b", s):
                j = i
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and lines[j].strip() in ("pass", "continue"):
                    silent.append((str(path), i, s, lines[j].strip()))

    print("=== Bare print('?') ===")
    for p, i, s in bare:
        print(f"{p}:{i}: {s}")

    print("\n=== Short/cryptic ? messages (sample patterns) ===")
    for p, i, s in short_q:
        print(f"{p}:{i}: {s}")

    print(f"\n=== except → pass/continue ({len(silent)} total) ===")
    # Focus runtime_parts + runtime.py
    for p, i, e, b in silent:
        if "runtime_parts" in p or p.endswith("runtime.py"):
            # skip pure cleanup / display noise somewhat
            print(f"{p}:{i}: {e}  -> {b}")


if __name__ == "__main__":
    main()
