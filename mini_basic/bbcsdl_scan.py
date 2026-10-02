"""Scan BBC BASIC for SDL 2.0 example sources for mini_basic compatibility blockers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# Weighted blockers: higher weight = harder to support in mini_basic today.
#
# Pruned 2026-10 against actual current support (several patterns here used
# to flag features mini_basic has since implemented, badly inflating scores
# for programs that only use them in passing — e.g. the universal
# `ON ERROR ... PRINT REPORT$` boilerplate, or `i%%` as an ordinary 64-bit
# int loop counter). Keep this list to things that genuinely don't run yet;
# re-verify with a grep of mini_basic/ before re-adding a pattern here.
#
# pygame is itself an SDL wrapper, so "OSCLI LOAD/FONT/MDISPLAY" (image/font
# loading) and "ON MOUSE"/"ON MOVE" event hooks are plausible future work,
# not dismiss-and-forget like SYS/OpenGL/Box2D/inline-asm/raw fn-pointers —
# weighted lower accordingly, but still counted as real gaps.
BLOCKER_PATTERNS: Tuple[Tuple[str, int, str], ...] = (
    (r'\bSYS\s+"', 10, 'SYS'),
    (r'`[A-Za-z_][A-Za-z0-9_]*`', 8, 'fn_ptr'),
    (r'\bINSTALL\b', 7, 'INSTALL'),
    (r'\bON\s+(MOUSE|MOVE|CLOSE|SYS)\b', 4, 'on_event'),  # parsed as no-ops; SDL-feasible
    (r'(?m)^\s*\[(?:opt|equ|def|fn|fp)', 6, 'asm'),
    (r'\bgl[A-Z]\w+', 8, 'opengl'),
    (r'\bshaderlib\b|\bshader\b', 7, 'shader'),
    (r'\bBox2D\b|\bHello_Box2D\b', 9, 'box2d'),
    (r'\bOSCLI\s+"LOAD\b', 3, 'oscli_load'),  # image/data load — SDL-feasible
    (r'\bOSCLI\s+"FONT\b', 2, 'oscli_font'),  # SDL_ttf-feasible
    (r'\bOSCLI\s+"MDISPLAY\b', 3, 'oscli_mdisplay'),  # SDL_image-feasible
    (r'\bPTR#|\bEXT#|\bGET\$\s*#', 3, 'file_ptr'),  # random-access file I/O, not just PTR()/EXT()
    (r'\bCALL\b|\bUSR\b', 4, 'call_usr'),
)

_COMPILED = tuple(
    (re.compile(pattern, re.IGNORECASE), weight, name)
    for pattern, weight, name in BLOCKER_PATTERNS
)


@dataclass
class BlockerHit:
    name: str
    weight: int
    count: int


@dataclass
class ScanResult:
    path: str
    lines: int
    score: int
    blockers: List[BlockerHit] = field(default_factory=list)
    tier: str = 'unknown'

    def blocker_names(self) -> Tuple[str, ...]:
        return tuple(hit.name for hit in self.blockers)


def _strip_rem_comments(source: str) -> str:
    """Remove REM lines and inline REM segments (approximate)."""
    out: List[str] = []
    for raw in source.splitlines():
        upper = raw.upper()
        rem_at = upper.find('REM')
        if rem_at >= 0:
            before = raw[:rem_at]
            if not before.strip() or rem_at == 0:
                continue
            raw = before
        out.append(raw)
    return '\n'.join(out)


def scan_bbcsdl_source(source: str, *, strip_rem: bool = True) -> ScanResult:
    text = _strip_rem_comments(source) if strip_rem else source
    counts: Dict[str, Tuple[int, int]] = {}
    for pattern, weight, name in _COMPILED:
        matches = pattern.findall(text)
        if matches:
            prev = counts.get(name)
            count = len(matches)
            if prev:
                counts[name] = (prev[0], prev[1] + count)
            else:
                counts[name] = (weight, count)

    blockers = [
        BlockerHit(name=name, weight=weight, count=count)
        for name, (weight, count) in sorted(counts.items(), key=lambda item: -item[1][0])
    ]
    score = sum(hit.weight * hit.count for hit in blockers)
    lines = source.count('\n') + (1 if source and not source.endswith('\n') else 0)
    tier = classify_tier(score, blockers)
    return ScanResult(path='', lines=lines, score=score, blockers=blockers, tier=tier)


def classify_tier(score: int, blockers: Sequence[BlockerHit]) -> str:
    names = {hit.name for hit in blockers}
    if names & {'opengl', 'shader', 'box2d', 'fn_ptr', 'asm'} or score >= 40:
        return 'D'  # BBCSDL specialist (GPU/physics/SDL internals/raw ASM)
    if names & {'SYS', 'INSTALL', 'call_usr'} or score >= 20:
        return 'C'  # Full BBCSDL desktop app (raw OS calls)
    if score >= 6:
        return 'B'  # SDL-feasible gaps only (event hooks, image/font load)
    return 'A'  # Already runs, or trivially close


def scan_bbcsdl_file(path: Path, *, strip_rem: bool = True) -> ScanResult:
    source = path.read_text(encoding='utf-8', errors='replace')
    result = scan_bbcsdl_source(source, strip_rem=strip_rem)
    result.path = str(path)
    return result


def scan_bbcsdl_tree(
    root: Path,
    *,
    pattern: str = '*.txt',
    strip_rem: bool = True,
) -> List[ScanResult]:
    results: List[ScanResult] = []
    for path in sorted(root.rglob(pattern)):
        if not path.is_file():
            continue
        if path.name.upper() == 'README.TXT':
            continue
        results.append(scan_bbcsdl_file(path, strip_rem=strip_rem))
    return sorted(results, key=lambda item: (item.score, item.path))


def format_scan_report(results: Sequence[ScanResult], *, limit: int = 30) -> str:
    lines = [
        'BBCSDL corpus compatibility scan',
        f'Programs: {len(results)}',
        '',
        f'{"tier":<4} {"score":>5}  {"lines":>5}  blockers  path',
        '-' * 72,
    ]
    for item in results[:limit]:
        blockers = ','.join(
            f'{hit.name}({hit.count})' for hit in item.blockers[:6]
        )
        rel = Path(item.path).name
        lines.append(
            f'{item.tier:<4} {item.score:>5}  {item.lines:>5}  {blockers:<24}  {rel}'
        )
    if len(results) > limit:
        lines.append(f'... {len(results) - limit} more')
    return '\n'.join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Scan BBCSDL example sources for blockers')
    parser.add_argument(
        'path',
        nargs='?',
        default='test/corpus/bbcsdl',
        help='Corpus directory (default: test/corpus/bbcsdl)',
    )
    parser.add_argument('--limit', type=int, default=40, help='Max rows in report')
    parser.add_argument('--tier', help='Only show this tier (A/B/C/D)')
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.path)
    if not root.is_dir():
        print(f'Not a directory: {root}', file=sys.stderr)
        return 1

    results = scan_bbcsdl_tree(root)
    if args.tier:
        tier = args.tier.upper()
        results = [item for item in results if item.tier == tier]
    print(format_scan_report(results, limit=args.limit))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
