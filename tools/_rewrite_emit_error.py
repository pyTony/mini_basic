"""Rewrite diagnostic print('?...') to self._emit_error(...) in runtime_parts."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "mini_basic" / "runtime_parts"


def should_rewrite(args: str) -> bool:
    s = args.strip()
    if s.startswith("f'") or s.startswith('f"'):
        return len(s) > 2 and s[2] == "?"
    if s.startswith("'") or s.startswith('"'):
        return len(s) > 1 and s[1] == "?"
    return False


def rewrite_file(path: Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    count = 0
    out: list[str] = []
    for line in lines:
        raw = line.rstrip("\r\n")
        ending = line[len(raw) :]
        m = re.match(r"^(\s*)print\((.*)\)\s*$", raw)
        if not m:
            out.append(line)
            continue
        indent, args = m.group(1), m.group(2)
        if not should_rewrite(args):
            out.append(line)
            continue
        out.append(f"{indent}self._emit_error({args}){ending}")
        count += 1
    if count:
        path.write_text("".join(out), encoding="utf-8")
    return count


def main() -> None:
    total = 0
    for path in sorted(PARTS.glob("*.py")):
        n = rewrite_file(path)
        if n:
            print(f"{path.relative_to(ROOT)}: {n}")
            total += n
    print(f"total {total}")


if __name__ == "__main__":
    main()
