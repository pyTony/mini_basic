#!/usr/bin/env python3
"""List (and optionally kill) leftover Grok/agent Python processes.

Agents MUST run this regularly (see AGENT_POLICY §5b). Hung ``python -c`` probes
and ``test/_probe_*.py`` jobs have burned multi-hour CPU in the past.

Examples:
  python scripts/probe_agent_python.py
  python scripts/probe_agent_python.py --kill-orphans
  python scripts/verify_resources.py   # also prints a short summary
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Command-line fingerprints of agent / Grok automation (not normal user demos).
_AGENT_PATTERNS = (
    re.compile(r'test[/\\]_probe_', re.I),
    re.compile(r'_run_one_probe', re.I),
    re.compile(r'corpus_audit_probe', re.I),
    re.compile(r'progress_runner|progress_heartbeat', re.I),
    re.compile(r'BASICInterpreter|InterpreterConfig', re.I),
    re.compile(r'from mini_basic import', re.I),
    re.compile(r'[\\/]mini_basic[\\/].*[\\/]test[\\/]', re.I),
    re.compile(r'\.grok[\\/]sessions', re.I),
    re.compile(r't_saucer\d*\.py|t_fornest\.py', re.I),
)

# Never auto-kill these even if they match loosely.
_PROTECT_PATTERNS = (
    re.compile(r'mini_basic\.py\b', re.I),  # user demo runs
    re.compile(r'\bpytest\b', re.I),
    re.compile(r'probe_agent_python\.py', re.I),
    re.compile(r'verify_resources\.py', re.I),
)

# Clear orphans safe to kill with --kill-orphans when long-running.
_ORPHAN_PATTERNS = (
    re.compile(r'test[/\\]_probe_', re.I),
    re.compile(r'_run_one_probe', re.I),
    re.compile(r'corpus_audit_probe', re.I),
    re.compile(r't_saucer\d*\.py|t_fornest\.py', re.I),
    # Agent one-liners that hang (CASE/ON ERROR probes, etc.)
    re.compile(
        r'python(?:\.exe)?\s+-c\s+.*(BASICInterpreter|InterpreterConfig|ON ERROR|CASE X OF)',
        re.I | re.S,
    ),
)


@dataclass
class PyProc:
    pid: int
    cpu_seconds: float
    cmdline: str
    create_age_s: float
    is_agent: bool
    is_orphan_candidate: bool
    protected: bool


def _list_windows_python() -> List[PyProc]:
    # PowerShell is reliable for CommandLine on Windows.
    ps = (
        "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe' OR Name = 'pythonw.exe'\" | "
        "ForEach-Object { "
        "$c = $_.CommandLine; if (-not $c) { $c = '' }; "
        "$age = 0; try { $age = [int]((Get-Date) - $_.CreationDate).TotalSeconds } catch {}; "
        # Kernel+User time in 100ns units
        "$cpu = 0.0; try { $cpu = ($_.KernelModeTime + $_.UserModeTime) / 10000000.0 } catch {}; "
        "Write-Output ($_.ProcessId.ToString() + \"`t\" + $cpu.ToString('F1') + \"`t\" + "
        "$age.ToString() + \"`t\" + ($c -replace \"`t\",' ' -replace \"`r|`n\",' ')) "
        "}"
    )
    try:
        out = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f'probe_agent_python: list failed: {exc}', file=sys.stderr)
        return []
    rows: List[PyProc] = []
    me = os.getpid()
    for line in (out.stdout or '').splitlines():
        parts = line.split('\t', 3)
        if len(parts) < 4:
            continue
        try:
            pid = int(parts[0])
            cpu = float(parts[1])
            age = float(parts[2])
        except ValueError:
            continue
        if pid == me:
            continue
        cmd = parts[3].strip()
        if not cmd:
            continue
        protected = any(p.search(cmd) for p in _PROTECT_PATTERNS)
        is_agent = any(p.search(cmd) for p in _AGENT_PATTERNS)
        is_orphan = (not protected) and any(p.search(cmd) for p in _ORPHAN_PATTERNS)
        # Long-running agent -c without protect also orphan-ish
        if (
            not protected
            and is_agent
            and re.search(r'python(?:\.exe)?\s+-c\s+', cmd, re.I)
            and age >= 600
        ):
            is_orphan = True
        rows.append(
            PyProc(
                pid=pid,
                cpu_seconds=cpu,
                cmdline=cmd,
                create_age_s=age,
                is_agent=is_agent or is_orphan,
                is_orphan_candidate=is_orphan,
                protected=protected,
            )
        )
    return rows


def _list_posix_python() -> List[PyProc]:
    try:
        out = subprocess.run(
            ['ps', '-eo', 'pid,etimes,pcpu,args'],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    rows: List[PyProc] = []
    me = os.getpid()
    for line in (out.stdout or '').splitlines()[1:]:
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        try:
            pid = int(parts[0])
            age = float(parts[1])
            # pcpu is percent, not seconds — store 0 and use age for orphan age
            cpu = 0.0
        except ValueError:
            continue
        if pid == me:
            continue
        cmd = parts[3]
        if 'python' not in cmd.lower():
            continue
        protected = any(p.search(cmd) for p in _PROTECT_PATTERNS)
        is_agent = any(p.search(cmd) for p in _AGENT_PATTERNS)
        is_orphan = (not protected) and any(p.search(cmd) for p in _ORPHAN_PATTERNS)
        if (
            not protected
            and is_agent
            and re.search(r'python\d*\s+-c\s+', cmd, re.I)
            and age >= 600
        ):
            is_orphan = True
        rows.append(
            PyProc(
                pid=pid,
                cpu_seconds=cpu,
                cmdline=cmd,
                create_age_s=age,
                is_agent=is_agent or is_orphan,
                is_orphan_candidate=is_orphan,
                protected=protected,
            )
        )
    return rows


def list_python_procs() -> List[PyProc]:
    if sys.platform == 'win32':
        return _list_windows_python()
    return _list_posix_python()


def format_proc(p: PyProc, *, width: int = 100) -> str:
    cmd = p.cmdline.replace('\n', ' ')
    if len(cmd) > width:
        cmd = cmd[: width - 3] + '...'
    tags = []
    if p.protected:
        tags.append('protect')
    if p.is_orphan_candidate:
        tags.append('ORPHAN')
    elif p.is_agent:
        tags.append('agent')
    tag = ','.join(tags) if tags else 'other'
    return (
        f'  pid={p.pid:<6} age={p.create_age_s/60:6.1f}m '
        f'cpu={p.cpu_seconds:8.1f}s  [{tag}]  {cmd}'
    )


def kill_pids(pids: Iterable[int]) -> List[int]:
    killed: List[int] = []
    for pid in pids:
        try:
            if sys.platform == 'win32':
                subprocess.run(
                    ['taskkill', '/PID', str(pid), '/F'],
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
            else:
                os.kill(pid, 9)
            killed.append(pid)
        except (OSError, subprocess.TimeoutExpired):
            pass
    return killed


def scan(
    *,
    kill_orphans: bool = False,
    min_orphan_age_s: float = 300.0,
    min_orphan_cpu_s: float = 60.0,
) -> tuple[List[PyProc], List[int]]:
    """Return (all_agentish, killed_pids)."""
    all_procs = list_python_procs()
    agentish = [p for p in all_procs if p.is_agent or p.is_orphan_candidate]
    killed: List[int] = []
    if kill_orphans:
        targets = [
            p.pid
            for p in agentish
            if p.is_orphan_candidate
            and not p.protected
            and (
                p.create_age_s >= min_orphan_age_s
                or p.cpu_seconds >= min_orphan_cpu_s
            )
        ]
        killed = kill_pids(targets)
    return agentish, killed


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Probe Grok/agent Python leftovers')
    parser.add_argument(
        '--kill-orphans',
        action='store_true',
        help='Force-kill clear orphan probes (not mini_basic.py / pytest)',
    )
    parser.add_argument(
        '--min-age-s',
        type=float,
        default=300.0,
        help='Min process age (seconds) before --kill-orphans (default 300)',
    )
    parser.add_argument(
        '--min-cpu-s',
        type=float,
        default=60.0,
        help='Min CPU seconds before --kill-orphans (default 60)',
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Only print summary line + orphans',
    )
    args = parser.parse_args(argv)

    agentish, killed = scan(
        kill_orphans=args.kill_orphans,
        min_orphan_age_s=args.min_age_s,
        min_orphan_cpu_s=args.min_cpu_s,
    )
    orphans = [p for p in agentish if p.is_orphan_candidate]
    stamp = time.strftime('%Y-%m-%d %H:%M:%S')

    if not agentish:
        print(f'{stamp} agent-python: none found')
        return 0

    print(
        f'{stamp} agent-python: {len(agentish)} agent-related '
        f'({len(orphans)} orphan-candidates)'
        + (f'; killed={killed}' if killed else '')
    )
    show = orphans if args.quiet else agentish
    for p in sorted(show, key=lambda x: -x.cpu_seconds):
        print(format_proc(p))
    if orphans and not args.kill_orphans:
        print(
            '  tip: python scripts/probe_agent_python.py --kill-orphans'
        )
    # Exit 1 if orphans remain (warn); 0 if clean or only non-orphan agent.
    remaining = [
        p for p in orphans if p.pid not in set(killed)
    ]
    return 1 if remaining else 0


if __name__ == '__main__':
    raise SystemExit(main())
