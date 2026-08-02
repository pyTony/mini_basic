"""User approval: whole programs only, gated on agent verification."""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_USER_APPROVAL_PATH = _PROJECT_ROOT / 'USER_APPROVAL.txt'
_AGENT_RESULTS_PATH = _PROJECT_ROOT / 'USER_APPROVAL_AGENT.txt'
_SNIPPET_RESULTS_PATH = _PROJECT_ROOT / 'USER_VERIFY_SNIPPETS.txt'

ProgramCheckFn = Callable[[], Tuple[bool, str, List[Tuple[str, bool, str]]]]


def project_root() -> Path:
    return _PROJECT_ROOT


def _normalize_label(label: str) -> str:
    return ' '.join(label.strip().split())


def parse_user_approval_line(raw: str) -> Optional[Tuple[bool, str]]:
    line = raw.strip()
    if not line or line.startswith('#'):
        return None
    match = re.match(r'^\[(x|X| )\]\s*(.+)$', line)
    if not match:
        return None
    return match.group(1).lower() == 'x', _normalize_label(match.group(2))


def load_user_approval_labels() -> Tuple[List[str], List[str]]:
    pending: List[str] = []
    approved: List[str] = []
    if not _USER_APPROVAL_PATH.is_file():
        return pending, approved
    for raw in _USER_APPROVAL_PATH.read_text(encoding='utf-8').splitlines():
        parsed = parse_user_approval_line(raw)
        if parsed is None:
            continue
        done, label = parsed
        if done:
            approved.append(label)
        else:
            pending.append(label)
    return pending, approved


def _parse_agent_results_line(raw: str) -> Optional[Tuple[str, str, str]]:
    line = raw.strip()
    if not line or line.startswith('#'):
        return None
    match = re.match(r'^(OK|FAIL|PENDING)\s+(.+?)(?:\s+::\s+(.+))?$', line, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).upper(), _normalize_label(match.group(2)), (match.group(3) or '').strip()


def load_agent_program_results() -> Dict[str, Tuple[Optional[bool], str]]:
    results: Dict[str, Tuple[Optional[bool], str]] = {}
    if not _AGENT_RESULTS_PATH.is_file():
        return results
    for raw in _AGENT_RESULTS_PATH.read_text(encoding='utf-8').splitlines():
        parsed = _parse_agent_results_line(raw)
        if parsed is None:
            continue
        status, label, detail = parsed
        if status == 'OK':
            results[label] = (True, detail or 'all agent checks passed')
        elif status == 'FAIL':
            results[label] = (False, detail or 'agent checks failed')
        else:
            results[label] = (None, detail or 'not checked yet')
    return results


def load_snippet_results() -> List[Tuple[str, bool, str]]:
    """Return (program, ok, detail) snippet rows for diagnostics."""
    rows: List[Tuple[str, bool, str]] = []
    if not _SNIPPET_RESULTS_PATH.is_file():
        return rows
    for raw in _SNIPPET_RESULTS_PATH.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        match = re.match(r'^(OK|FAIL)\s+([^:]+):\s*(.+?)(?:\s+::\s+(.+))?$', line, re.IGNORECASE)
        if not match:
            continue
        ok = match.group(1).upper() == 'OK'
        program = _normalize_label(match.group(2))
        snippet = match.group(3).strip()
        detail = (match.group(4) or '').strip()
        rows.append((f'{program}: {snippet}', ok, detail))
    return rows


def write_agent_results(
    program_lines: List[str],
    snippet_lines: Optional[List[str]] = None,
    *,
    stamp: Optional[str] = None,
) -> None:
    if stamp is None:
        stamp = time.strftime('%Y-%m-%d %H:%M:%S')
    program_body = [
        '# Whole-program agent verification (user approves programs only)',
        f'# Updated {stamp}',
        '# Only OK programs appear in status.html user approval section',
        '',
        *program_lines,
        '',
    ]
    tmp = _AGENT_RESULTS_PATH.with_suffix('.tmp')
    tmp.write_text('\n'.join(program_body), encoding='utf-8')
    os.replace(tmp, _AGENT_RESULTS_PATH)

    if snippet_lines is not None:
        snippet_body = [
            '# Snippet diagnostics (failure points — not separate user approval)',
            f'# Updated {stamp}',
            '# User runs full program test: python verify_program.py <name>',
            '',
            *snippet_lines,
            '',
        ]
        stmp = _SNIPPET_RESULTS_PATH.with_suffix('.tmp')
        stmp.write_text('\n'.join(snippet_body), encoding='utf-8')
        os.replace(stmp, _SNIPPET_RESULTS_PATH)


def agent_verify_command_for(program: str) -> str:
    """Agent automated snippet checks — not user verification."""
    name = program.strip()
    if name.lower() == 'corpus runnable audit':
        return 'python verify_program.py corpus'
    return f'python verify_program.py {name}'


def user_run_command_for(program: str) -> str:
    """How the user runs the real program (interactive / visual)."""
    from utils.program_run_guide import run_command_for

    return run_command_for(program)


def _animal_program_check() -> Tuple[bool, str, List[Tuple[str, bool, str]]]:
    from test.verify_animal_step import STEPS

    snippets: List[Tuple[str, bool, str]] = []
    for label, fn in STEPS:
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, str(exc)
        snippets.append((label, ok, detail))
    failed = [name for name, ok, _ in snippets if not ok]
    ok = not failed
    if ok:
        summary = f'all {len(snippets)} snippet checks passed'
    else:
        summary = f'{len(failed)} snippet failure(s): {", ".join(failed)}'
    return ok, summary, snippets


def _soccerball_program_check() -> Tuple[bool, str, List[Tuple[str, bool, str]]]:
    from test.verify_soccerball_step import STEPS

    snippets: List[Tuple[str, bool, str]] = []
    for label, fn in STEPS:
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, str(exc)
        snippets.append((label, ok, detail))
    failed = [name for name, ok, _ in snippets if not ok]
    ok = not failed
    if ok:
        summary = f'all {len(snippets)} snippet checks passed'
    else:
        summary = f'{len(failed)} snippet failure(s): {", ".join(failed)}'
    return ok, summary, snippets


def _wheel_program_check() -> Tuple[bool, str, List[Tuple[str, bool, str]]]:
    from test.verify_wheel_step import STEPS

    snippets: List[Tuple[str, bool, str]] = []
    for label, fn in STEPS:
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, str(exc)
        snippets.append((label, ok, detail))
    failed = [name for name, ok, _ in snippets if not ok]
    ok = not failed
    if ok:
        summary = f'all {len(snippets)} snippet checks passed'
    else:
        summary = f'{len(failed)} snippet failure(s): {", ".join(failed)}'
    return ok, summary, snippets


PROGRAM_CHECKERS: Dict[str, ProgramCheckFn] = {
    'animal.txt': _animal_program_check,
    'soccerball.txt': _soccerball_program_check,
    'wheel.txt': _wheel_program_check,
}


def run_agent_approval_checks(
    labels: Optional[List[str]] = None,
) -> Tuple[List[str], List[str]]:
    if labels is None:
        pending, approved = load_user_approval_labels()
        labels = pending + approved

    program_lines: List[str] = []
    snippet_lines: List[str] = []
    for label in labels:
        checker = PROGRAM_CHECKERS.get(label)
        if checker is None:
            program_lines.append(f'PENDING {label} :: no automated checker yet')
            continue
        try:
            ok, summary, snippets = checker()
        except Exception as exc:
            ok, summary, snippets = False, str(exc), []
        status = 'OK' if ok else 'FAIL'
        program_lines.append(f'{status} {label} :: {summary}')
        for snippet_name, snippet_ok, detail in snippets:
            snippet_status = 'OK' if snippet_ok else 'FAIL'
            snippet_lines.append(
                f'{snippet_status} {label}: {snippet_name} :: {detail}',
            )
    return program_lines, snippet_lines


def build_approval_checklist(current_program: str = '') -> Dict[str, object]:
    pending_labels, approved_labels = load_user_approval_labels()
    agent_results = load_agent_program_results()
    snippet_rows = load_snippet_results()

    awaiting_user: List[str] = []
    agent_pending: List[str] = []
    agent_failed: List[str] = []
    verify_commands: List[Dict[str, str]] = []
    agent_snippets: List[str] = []

    program = (current_program or '').lower()
    focus_program = current_program if current_program and current_program != 'None' else ''

    for label in pending_labels:
        agent = agent_results.get(label)
        if agent is None:
            agent_pending.append(label)
        else:
            agent_ok, detail = agent
            if agent_ok is True:
                awaiting_user.append(label)
            elif agent_ok is False:
                agent_failed.append(f'{label} :: {detail}')
            else:
                agent_pending.append(label)

        prog_key = label.lower()
        is_focus = bool(focus_program and focus_program.lower() == prog_key)
        is_ready = label in awaiting_user
        has_checker = label in PROGRAM_CHECKERS
        if (is_focus or is_ready) and has_checker:
            from utils.program_run_guide import run_guide_for

            guide = run_guide_for(label)
            verify_commands.append({
                'program': label,
                'command': user_run_command_for(label),
                'agent_command': agent_verify_command_for(label),
                'kind': (guide or {}).get('kind', ''),
                'try_notes': (guide or {}).get('try_notes', []),
                'cwd': 'mini_basic',
            })

    for snippet_label, ok, detail in snippet_rows:
        if not ok:
            text = f'{snippet_label} :: {detail}' if detail else snippet_label
            if program and program not in snippet_label.lower():
                if focus_program and focus_program.lower() not in snippet_label.lower():
                    continue
            agent_snippets.append(text)

    if program and program != 'none':
        awaiting_user = _sort_current_first(awaiting_user, program)
        agent_pending = _sort_current_first(agent_pending, program)
        agent_failed = _sort_current_first(agent_failed, program)
        verify_commands = _sort_verify_current_first(verify_commands, program)

    return {
        'current_program': current_program or 'None',
        'pending': awaiting_user,
        'pending_count': len(awaiting_user),
        'agent_pending': agent_pending,
        'agent_failed': agent_failed,
        'agent_snippets': agent_snippets[:8],
        'verify_commands': verify_commands,
        'approved': approved_labels[-6:],
        'approved_more': max(0, len(approved_labels) - 6),
        'note': (
            'Approve whole programs only. Run the program yourself (mini_basic.py) '
            'with varied inputs; verify_program.py is agent-only. Reply OK in chat; '
            'agent marks [x] in USER_APPROVAL.txt'
        ),
    }


def _sort_current_first(items: List[str], program: str) -> List[str]:
    current = [item for item in items if program in item.lower()]
    other = [item for item in items if program not in item.lower()]
    return current + other


def _sort_verify_current_first(
    items: List[Dict[str, str]],
    program: str,
) -> List[Dict[str, str]]:
    current = [item for item in items if program in item['program'].lower()]
    other = [item for item in items if program not in item['program'].lower()]
    return current + other