"""Scan BBC BASIC for SDL 2.0 example sources for mini_basic compatibility blockers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# Weighted blockers: higher weight = harder to support in mini_basic today.
BLOCKER_PATTERNS: Tuple[Tuple[str, int, str], ...] = (
    (r'\bSYS\s+"', 10, 'SYS'),
    (r'`[A-Za-z_][A-Za-z0-9_]*`', 8, 'fn_ptr'),
    (r'\bINSTALL\b', 7, 'INSTALL'),
    (r'%%', 7, 'pointer'),
    (r'\bON\s+(MOUSE|MOVE|CLOSE|SYS)\b', 6, 'on_event'),
    (r'\bCASE\b|\bWHEN\b|\bENDCASE\b', 1, 'case'),
    (r'\bEVAL\s*\(', 5, 'eval'),
    (r'\bDIM\s+\w+\{', 5, 'structure'),
    (r'(?m)^\s*\[(?:opt|equ|def|fn|fp)', 6, 'asm'),
    (r'\bgl[A-Z]\w+', 8, 'opengl'),
    (r'\bshaderlib\b|\bshader\b', 7, 'shader'),
    (r'\bBox2D\b|\bHello_Box2D\b', 9, 'box2d'),
    (r'\bOSCLI\s+"LOAD\b', 4, 'oscli_load'),
    (r'\bOSCLI\s+"FONT\b', 3, 'oscli_font'),
    (r'\bOSCLI\s+"MDISPLAY\b', 5, 'oscli_mdisplay'),
    (r'\*REFRESH\b', 1, 'star_refresh'),
    (r'@dir\$|@lib\$|@hwnd%|@memhdc%|@platform%|@vdu%|@size\.', 4, 'bbcsdl_vars'),
    (r'\bMOUSE\b', 1, 'mouse'),
    (r'\bSOUND\b|\bENVELOPE\b', 2, 'sound'),
    (r'\bREPORT\$|\bREPORT\b', 2, 'report'),
    (r'\bWIDTH\s*\(', 1, 'width'),
    (r'\bINKEY\s*\(\s*-', 2, 'inkey_neg'),
    (r'\bINKEY\s*\(\s*\d', 2, 'inkey_timeout'),
    (r'\bPTR#|\bEXT#|\bGET\$\s*#', 3, 'file_ptr'),
    (r'\bVDU\s+23\s*,\s*22', 1, 'vdu_custom_mode'),
    (r'\bCALL\b|\bUSR\b', 4, 'call_usr'),
    (r'\bLOCAL\b', 1, 'local'),
    (r'\bSWAP\b', 1, 'swap'),
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
    if names & {'opengl', 'shader', 'box2d', 'fn_ptr'} or score >= 80:
        return 'D'  # BBCSDL specialist (GPU/physics/SDL internals)
    if names & {'SYS', 'pointer', 'INSTALL', 'on_event'} or score >= 35:
        return 'C'  # Full BBCSDL desktop app
    if score >= 12:
        return 'B'  # BBCSDL-ish but mostly BASIC + graphics
    return 'A'  # Acorn-era portable target


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
