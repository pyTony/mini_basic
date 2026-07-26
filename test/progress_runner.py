"""unittest runner. Only status.html is produced (other phone/log efforts removed)."""
from __future__ import annotations

import html
import json
import os
import re
import sys
import time
import unittest
from collections import OrderedDict
from email.utils import formatdate
from typing import Dict, List, Optional, TextIO, Tuple
from xml.sax.saxutils import escape

# Pygame safety: autonomous status/heartbeat work must never leave windows.
try:
    from mini_basic.display import ensure_no_pygame_leftovers
    ensure_no_pygame_leftovers()
except Exception:
    pass

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_TEST_DIR)
_SOURCE_WATCH_PATHS = (
    os.path.join(_ROOT_DIR, 'mini_basic', 'runtime.py'),
    os.path.join(_TEST_DIR, 'test_mini_basic.py'),
)
_STATUS_HTML_PATH = os.path.join(_ROOT_DIR, 'status.html')
_CURRENT_TASK_PATH = os.path.join(_ROOT_DIR, 'CURRENT_TASK.txt')
_FEATURES_DONE_PATH = os.path.join(_ROOT_DIR, 'FEATURES_DONE.txt')
_CORPUS_RUNNABLE_PATH = os.path.join(_ROOT_DIR, 'CORPUS_RUNNABLE.txt')
_LOG_PATH = os.path.join(_ROOT_DIR, '_run_progress.log')
_RSS_HISTORY_PATH = os.path.join(_ROOT_DIR, '.progress_rss_history.json')
_WORK_LOG_PATH = os.path.join(_ROOT_DIR, 'WORK_LOG.txt')

# Stubs for removed phone / multi-file progress efforts
def _atomic_write_phone(*a, **k): pass
def _phone_safe(s): return s
def _write_phone_files(*a, **k): 
    try:
        from utils.status_updater import StatusUpdater
        StatusUpdater().update()
    except: pass
_PHONE_PATH = None
# (do not clobber the real paths below - they are still used by updater and log functions)
_LOG_PATH = os.path.join(_ROOT_DIR, '_run_progress.log')
_WORK_LOG_PATH = os.path.join(_ROOT_DIR, 'WORK_LOG.txt')

# Feature labels kept only for status.html summary
_FEATURE_LABELS = {
    'def': 'DEF FN / PROC',
    'list': 'LIST',
    'proc': 'PROC',
    'print': 'PRINT',
    'integer': 'Integer variables',
    'bigint': 'Bigint mode',
    'rnd': 'RND',
    'save': 'SAVE / LOAD',
    'load': 'SAVE / LOAD',
    'renumber': 'RENUMBER',
    'dialect': 'Dialect',
    'dim': 'DIM / arrays',
    'local': 'LOCAL',
    'for': 'FOR / NEXT',
    'while': 'WHILE / WEND',
    'if': 'IF / ENDIF',
    'goto': 'GOTO / GOSUB',
    'input': 'INPUT',
    'vdu': 'VDU / graphics',
    'mode': 'MODE',
    'chain': 'CHAIN',
    'oscli': 'OSCLI',
    'mandelbrot': 'Mandelbrot',
    'factorial': 'Factorial',
    'parse': 'Parser',
    'edit': 'EDIT',
    'repl': 'REPL',
    'cli': 'CLI',
    'help': 'HELP',
    'shebang': 'Dialect hints',
    'case': 'Case sensitivity',
    'sprite': 'Sprites',
    'data': 'DATA / READ',
    'on': 'ON GOTO/GOSUB',
    'repeat': 'REPEAT / UNTIL',
    'error': 'ERROR',
    'float': 'FLOAT / numeric',
    'mid': 'String functions',
    'left': 'String functions',
    'right': 'String functions',
    'chr': 'String functions',
    'str': 'String functions',
    'len': 'String functions',
    'val': 'VAL',
    'inkey': 'INKEY',
    'time': 'TIME',
    'wait': 'WAIT',
    'tab': 'TAB / SPC',
    'spc': 'TAB / SPC',
    'using': 'PRINT USING',
    'open': 'File I/O',
    'close': 'File I/O',
    'write': 'File I/O',
    'read': 'File I/O',
    'field': 'FIELD',
    'indent': 'Indent / layout',
    'windows': 'Windows REPL',
    'epsilon': 'System variables',
    'system': 'System variables',
    'detokenize': 'BBC binary / detokenize',
    'binary': 'BBC binary / detokenize',
    'validate': 'Dialect validation',
    'life': 'Life benchmark',
    'bench': 'Benchmarks',
    'calcexe': 'Calc.exe integration',
    'agon': 'Agon corpus',
    'bbc': 'BBC corpus',
    'mits': 'MITS dialect',
    'matrix': 'Dialect matrix',
    'color': 'Colour / ANSI',
    'colour': 'Colour / ANSI',
    'cls': 'CLS / CLG',
    'clg': 'CLS / CLG',
    'gcol': 'GCOL / PLOT',
    'plot': 'GCOL / PLOT',
    'hex': 'Hex literals',
    'star': 'Star commands',
    'filled': 'Graphics primitives',
    'detect': 'Binary detect',
    'user': 'Variables',
    'variable': 'Variables',
    'unknown': 'Edge cases',
    'break': 'BREAK / CONTINUE',
    'continue': 'BREAK / CONTINUE',
    'swap': 'SWAP',
    'bitwise': 'Bitwise XOR/EQV/IMP',
    'div': 'DIV integer division',
    'at': '@dir$ / @lib$ / @usr$',
    'whole': 'Whole-array copy/fill',
    'eval': 'EVAL',
    'report': 'REPORT',
    'restore': 'RESTORE',
    'label': 'Labels',
    'auto': 'AUTO',
    'new': 'NEW / CLEAR',
    'run': 'RUN / END',
    'end': 'RUN / END',
    'stop': 'STOP / CONT',
    'cont': 'STOP / CONT',
    'delete': 'DELETE',
    'rem': 'REM',
    'let': 'LET',
    'sgn': 'Math builtins',
    'abs': 'Math builtins',
    'sqr': 'Math builtins',
    'pi': 'Math builtins',
    'sum': 'SUM',
    'count': 'COUNT',
    'near': 'Float precision',
    'find': 'Float precision',
    'separate': 'Integer separate',
    'glyph': 'Mandelbrot',
    'palette': 'Mandelbrot',
    'reverseprint': 'PROC reverseprint',
    'remove': 'PROC remove_spaces',
    'volume': 'DEF FN examples',
    'fact': 'DEF FN examples',
    'scalar': 'Array FN',
    'hypot': 'DEF FN examples',
    'tag': 'DEF FN string',
    'double': 'DEF FN examples',
    'sign': 'DEF FN examples',
    'add': 'DEF FN examples',
    'absval': 'DEF FN examples',
    'hello': 'DEF PROC examples',
    'reverse': 'PROC examples',
    'spaces': 'PROC remove_spaces',
    'fraction': 'RND',
    'command': 'CLI',
    'script': 'CLI',
    'compat': 'Compatibility',
    'locked': 'Dialect lock',
    'strict': 'Strict dialect',
    'hint': 'Dialect hints',
    'unnumbered': 'Program format',
    'numbered': 'Program format',
    'glossary': 'Glossary',
    'corpus': 'Corpus',
    'optimization': 'System variables',
    'buffering': 'Print buffering',
    'hash': 'File channels',
    'get': 'GET / PUT',
    'put': 'GET / PUT',
    'lset': 'LSET / RSET',
    'rset': 'LSET / RSET',
    'mkd': 'MKI/MKS/MKD',
    'mki': 'MKI/MKS/MKD',
    'mks': 'MKI/MKS/MKD',
    'openin': 'OPENIN/OPENOUT',
    'openout': 'OPENIN/OPENOUT',
    'rgb': 'RGB$ / colour',
    'move': 'MOVE / DRAW',
    'draw': 'MOVE / DRAW',
    'origin': 'ORIGIN',
    'vpos': 'POS / VPOS',
    'pos': 'POS / VPOS',
    'next': 'FOR / NEXT',
    'wend': 'WHILE / WEND',
    'until': 'REPEAT / UNTIL',
    'elsif': 'IF / ENDIF',
    'elif': 'IF / ENDIF',
    'else': 'IF / ENDIF',
    'endif': 'IF / ENDIF',
    'elseify': 'IF / ENDIF',
    'test': 'Misc tests',
}


def _flatten_suite(suite: unittest.TestSuite) -> List[unittest.case.TestCase]:
    tests: List[unittest.case.TestCase] = []
    for child in suite:
        if isinstance(child, unittest.TestSuite):
            tests.extend(_flatten_suite(child))
        else:
            tests.append(child)
    return tests


def _feature_from_test(test: unittest.case.TestCase) -> str:
    module = test.__class__.__module__.rsplit('.', 1)[-1]
    if module == 'test_agon_corpus':
        return 'Agon corpus'
    if module == 'test_save_case':
        return 'SAVE case folding'
    method = test._testMethodName
    body = method[5:] if method.startswith('test_') else method
    first = body.split('_')[0].lower()
    return _FEATURE_LABELS.get(first, first.replace('_', ' ').title())


def _build_feature_groups(
    suite: unittest.TestSuite,
) -> "OrderedDict[str, List[str]]":
    groups: "OrderedDict[str, List[str]]" = OrderedDict()
    for test in _flatten_suite(suite):
        feature = _feature_from_test(test)
        groups.setdefault(feature, []).append(test.id())
    return groups


def _phone_safe(text: str) -> str:
    """ASCII-only text safe for tablet Notepad (no Markdown preview glitches)."""
    replacements = {
        '\u2014': '-',  # em dash
        '\u2013': '-',  # en dash
        '\u2192': '->',  # arrow
        '\u2026': '...',  # ellipsis
        '\u2190': '<-',
        '\u2191': '^',
        '\u2193': 'v',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode('ascii', 'replace').decode('ascii')


def _normalize_feature_line(line: str) -> str:
    """Map legacy [x]/[ ] markers to plain OK/-- for phone display."""
    line = _phone_safe(line.strip())
    for mark, plain in (('[x]', 'OK'), ('[>]', '>>'), ('[!]', '!!'), ('[ ]', '--')):
        if line.startswith(mark + ' '):
            return plain + line[len(mark):]
        if line.startswith(mark):
            return plain + line[len(mark):]
    return line


def _load_corpus_runnable_lines() -> List[str]:
    """Programs you can try: CORPUS_RUNNABLE.txt (phone-safe, no paths with slashes)."""
    if not os.path.isfile(_CORPUS_RUNNABLE_PATH):
        return []
    lines: List[str] = []
    with open(_CORPUS_RUNNABLE_PATH, encoding='utf-8') as handle:
        for raw in handle:
            line = _phone_safe(raw.strip())
            if not line or line.startswith('#'):
                continue
            if line.startswith('NEW '):
                lines.append('try new ' + line[4:])
            elif line.startswith('ALL '):
                lines.append(line.lower())
            elif line.startswith('NOT '):
                lines.append('skip ' + line[4:])
            else:
                parts = line.split(' ', 1)
                name = parts[0]
                if not name.lower().endswith('.txt'):
                    continue
                rest = parts[1] if len(parts) > 1 else ''
                bits = rest.split(' ', 1)
                desc = bits[1] if len(bits) > 1 else bits[0] if bits else ''
                hint = f'run {name}'
                if desc:
                    hint += f' {desc}'
                lines.append(hint)
    return lines


def log_work_event(message: str, *, kind: str = 'WORK') -> None:
    """Append one event to WORK_LOG.txt (status.html Recent Work Log).

    Line format: ``YYYY-MM-DD HH:MM:SS KIND message``
    """
    text = ' '.join(str(message).split())
    if not text:
        return
    kind_token = re.sub(r'\W+', '', str(kind or 'WORK').upper()) or 'WORK'
    stamp = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f'{stamp} {kind_token} {text}\n'
    try:
        with open(_WORK_LOG_PATH, 'a', encoding='utf-8', newline='\n') as handle:
            handle.write(line)
    except OSError:
        pass


def _load_work_log_entries() -> List[str]:
    """Chronological work-log lines (oldest first), without blanks/comments."""
    if not os.path.isfile(_WORK_LOG_PATH):
        return []
    entries: List[str] = []
    try:
        with open(_WORK_LOG_PATH, encoding='utf-8') as handle:
            for raw in handle:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                entries.append(line)
    except OSError:
        return []
    return entries


def _load_work_log_recent(limit: int = 20) -> List[str]:
    """Newest-first slice for status dashboard / phone views."""
    entries = _load_work_log_entries()
    if limit <= 0:
        return list(reversed(entries))
    return list(reversed(entries[-limit:]))


def _last_work_log_stamp() -> Optional[str]:
    entries = _load_work_log_entries()
    if not entries:
        return None
    match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', entries[-1])
    return match.group(1) if match else None


def _load_todo_items() -> List[str]:
    items: List[str] = []
    for raw in _load_features_done_lines():
        line = _normalize_feature_line(raw)
        if line.startswith('-- '):
            items.append(line[3:].strip())
    return items


def _load_features_done_lines() -> List[str]:
    """Phone-readable interpreter changelog (FEATURES_DONE.txt)."""
    if not os.path.isfile(_FEATURES_DONE_PATH):
        return []
    lines: List[str] = []
    with open(_FEATURES_DONE_PATH, encoding='utf-8') as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('P') and (' - ' in line or ' — ' in line):
                lines.append(_normalize_feature_line(line))
                continue
            if line.startswith(('OK ', '-- ', '>> ', '!! ')):
                lines.append(_normalize_feature_line(line))
                continue
            if line.startswith(('[x]', '[ ]', '[!]', '[>]')):
                lines.append(_normalize_feature_line(line))
    return lines


def _file_mtime_stamp(path: str) -> Optional[str]:
    try:
        if os.path.isfile(path):
            return time.strftime(
                '%Y-%m-%d %H:%M:%S',
                time.localtime(os.path.getmtime(path)),
            )
    except OSError:
        return None
    return None


def _parse_stamp(stamp: str) -> Optional[float]:
    try:
        return time.mktime(time.strptime(stamp, '%Y-%m-%d %H:%M:%S'))
    except (OSError, ValueError):
        return None


def _format_idle_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f'{hours}h {minutes}m'
    if minutes:
        return f'{minutes}m {secs}s'
    return f'{secs}s'


def _last_work_stamp() -> Optional[str]:
    """Latest logged work event; falls back to last test run stamp."""
    logged = _last_work_log_stamp()
    if logged:
        return logged
    last_test_stamp, _ = _last_test_run_info()
    return last_test_stamp


def _source_newer_than_last_test() -> bool:
    """True when interpreter or test sources changed after the last test stamp."""
    last_test_stamp, _ = _last_test_run_info()
    if not last_test_stamp:
        return False
    test_epoch = _parse_stamp(last_test_stamp)
    if test_epoch is None:
        return False
    for path in _SOURCE_WATCH_PATHS:
        try:
            if os.path.isfile(path) and os.path.getmtime(path) > test_epoch + 2:
                return True
        except OSError:
            continue
    return False


def _last_test_run_info() -> Tuple[Optional[str], Optional[str]]:
    if not os.path.isfile(_LOG_PATH):
        return None, None
    try:
        with open(_LOG_PATH, encoding='utf-8') as handle:
            content = handle.read()
    except OSError:
        return None, None
    run_match = re.search(
        r'=== test run (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ===',
        content,
    )
    run_stamp = run_match.group(1) if run_match else _file_mtime_stamp(_LOG_PATH)
    summary = None
    for line in reversed(content.splitlines()):
        if line.startswith('Finished ') and 'tests in' in line:
            summary = _phone_safe(line)
            break
    return run_stamp, summary


def _last_test_summary_from_log() -> Optional[str]:
    _, summary = _last_test_run_info()
    return summary


def _load_current_task_line() -> Optional[str]:
    if not os.path.isfile(_CURRENT_TASK_PATH):
        return None
    try:
        with open(_CURRENT_TASK_PATH, encoding='utf-8') as handle:
            for raw in handle:
                line = raw.strip()
                if line and not line.startswith('#'):
                    return _phone_safe(line)
    except OSError:
        return None
    return None


def _todo_remaining_count() -> int:
    return sum(
        1
        for raw in _load_features_done_lines()
        if _normalize_feature_line(raw).startswith('-- ')
    )


def _last_test_outcome() -> Tuple[bool, Optional[str]]:
    """Return (all_passed, summary line from log)."""
    _, summary = _last_test_run_info()
    if not summary:
        return False, None
    fail_match = re.search(r'(\d+)\s+failures?', summary, re.IGNORECASE)
    err_match = re.search(r'(\d+)\s+errors?', summary, re.IGNORECASE)
    failures = int(fail_match.group(1)) if fail_match else -1
    errors = int(err_match.group(1)) if err_match else -1
    if failures < 0 or errors < 0:
        return False, summary
    return failures == 0 and errors == 0, summary


def _work_complete() -> bool:
    """Idle only when tests pass, todos are done, and sources match last run."""
    all_passed, summary = _last_test_outcome()
    if not all_passed or not summary:
        return False
    if _todo_remaining_count() > 0:
        return False
    if _source_newer_than_last_test():
        return False
    return True


def _activity_label(
    *,
    heartbeat: bool,
    stamp: str,
    last_test_stamp: Optional[str],
    extra_lines: Optional[List[str]],
) -> str:
    if extra_lines:
        for line in extra_lines:
            lower = line.lower()
            if 'running ' in lower or lower.startswith('starting'):
                return 'testing now'
            if 'tests done' in lower or 'fail' in lower:
                return 'tests just finished'
    todo_count = _todo_remaining_count()
    all_passed, summary = _last_test_outcome()
    if not _work_complete():
        parts: List[str] = ['work pending']
        if not all_passed or not summary:
            parts.append('tests not all pass')
        if _source_newer_than_last_test():
            parts.append('source changed since last test')
        if todo_count:
            item = 'item' if todo_count == 1 else 'items'
            parts.append(f'{todo_count} todo {item}')
        return ' '.join(parts)
    if heartbeat and last_test_stamp and last_test_stamp != stamp:
        return 'idle all work done PC alive'
    if heartbeat:
        return 'idle all work done heartbeat only'
    return 'updated'


def _minimal_status_lines(
    *,
    sync_id: int,
    heartbeat_id: int,
    stamp: str,
    heartbeat: bool,
    test_line: Optional[str],
    progress_line: Optional[str],
    extra_lines: Optional[List[str]] = None,
) -> List[str]:
    """Compact ASCII for OneDrive tablet viewer."""
    last_test_stamp, log_summary = _last_test_run_info()
    last_work_stamp = _last_work_stamp()
    todo_items = _load_todo_items()
    all_passed, _ = _last_test_outcome()
    work_complete = _work_complete()
    activity = _activity_label(
        heartbeat=heartbeat,
        stamp=stamp,
        last_test_stamp=last_test_stamp,
        extra_lines=extra_lines,
    )

    lines = ['minibasic status', f'updated {stamp}']
    if heartbeat:
        lines.append(f'alive check #{heartbeat_id}')
    else:
        lines.append(f'work sync #{sync_id}')

    if last_work_stamp:
        lines.append(f'last work {last_work_stamp}')
    if last_test_stamp:
        lines.append(
            f'last test {last_test_stamp}'
            + (' all pass' if all_passed else ' not all pass')
        )

    try:
        from mini_basic.features.deferred import deferred_rows

        deferred_count = len(deferred_rows())
        lines.append(f'deferred {deferred_count} feature areas (WIMP ASM SYS ...) see 07_deferred.txt')
    except Exception:
        pass

    if todo_items:
        lines.append(f'TODO ({len(todo_items)})')
        for item in todo_items:
            lines.append(f'  -- {item}')
    elif work_complete:
        lines.append('TODO none')

    task = _load_current_task_line()
    if task:
        lines.append(f'in progress {task}')

    if not heartbeat:
        if not work_complete and last_work_stamp:
            work_epoch = _parse_stamp(last_work_stamp)
            now_epoch = _parse_stamp(stamp)
            if work_epoch is not None and now_epoch is not None and now_epoch > work_epoch:
                duration = _format_idle_duration(now_epoch - work_epoch)
                lines.append(f'waiting {duration} since last work')
        elif work_complete and last_work_stamp:
            work_epoch = _parse_stamp(last_work_stamp)
            now_epoch = _parse_stamp(stamp)
            if work_epoch is not None and now_epoch is not None and now_epoch > work_epoch:
                duration = _format_idle_duration(now_epoch - work_epoch)
                lines.append(f'idle {duration} all clear')

    summary = test_line or log_summary or ''
    finished_match = re.search(
        r'Finished (\d+) tests.*?(\d+) failures?.*?(\d+) errors?',
        summary,
        re.IGNORECASE,
    )
    if finished_match:
        total = finished_match.group(1)
        failures = finished_match.group(2)
        errors = finished_match.group(3)
        lines.append(
            f'tests {total} pass 0 fail'
            if failures == '0' and errors == '0'
            else f'tests {total} fail {failures} err {errors}'
        )
    elif progress_line and not heartbeat:
        lines.append(_phone_safe(progress_line).replace(':', ' '))

    work_log = _load_work_log_recent()
    if work_log:
        lines.append('work log newest first')
        lines.extend(work_log)

    if not heartbeat:
        lines.append(f'status {activity}')
        corpus_lines = _load_corpus_runnable_lines()
        if corpus_lines:
            lines.append(
                f'programs {len(corpus_lines)} listed in CORPUS_RUNNABLE.txt'
            )
        audit_path = os.path.join(_ROOT_DIR, 'CORPUS_AUDIT.txt')
        if os.path.isfile(audit_path):
            try:
                with open(audit_path, encoding='utf-8') as handle:
                    audit_head = handle.read(400)
                ok_m = re.search(r'^OK \((\d+)\)', audit_head, re.MULTILINE)
                fail_m = re.search(r'^FAIL \((\d+)\)', audit_head, re.MULTILINE)
                if ok_m and fail_m:
                    lines.append(
                        f'corpus audit ok {ok_m.group(1)} fail {fail_m.group(1)}'
                    )
            except OSError:
                pass
        lines.append('details FEATURES_DONE.txt status.html')
    return lines


def _extract_program_from_task(task: str) -> str:
    match = re.search(r'(\w+\.txt)', task, re.IGNORECASE)
    if match:
        return match.group(1)
    lower = task.lower()
    if 'corpus' in lower:
        return 'corpus audit'
    return ''


def _load_user_approval_checklist(current_program: str = '') -> Dict[str, object]:
    """User sign-off list: only agent-verified items with no observable errors."""
    try:
        from utils.user_approval import build_approval_checklist

        return build_approval_checklist(current_program)
    except Exception:
        return {
            'current_program': current_program or 'None',
            'pending': [],
            'pending_count': 0,
            'agent_pending': [],
            'agent_failed': [],
            'approved': [],
            'approved_more': 0,
            'note': 'Approval checker unavailable',
        }


def _split_dashboard_todos(
    task: str,
    todos: List[str],
) -> Tuple[List[str], List[str]]:
    program = _extract_program_from_task(task)
    current: List[str] = []
    pending: List[str] = []
    for item in todos:
        item_lower = item.lower()
        if program and (
            program.lower() in item_lower
            or (program == 'corpus audit' and 'corpus' in item_lower)
        ):
            current.append(item)
        else:
            pending.append(item)
    return current, pending


def _load_confirmed_ok_items(limit: int = 6) -> Tuple[List[str], int]:
    ok_items = [
        line[3:].strip()
        for line in _load_features_done_lines()
        if line.startswith('OK ')
    ]
    if len(ok_items) <= limit:
        return ok_items, 0
    return ok_items[-limit:], len(ok_items) - limit


def _format_dashboard_work_log(entry: str) -> str:
    match = re.match(
        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\w+\s+(.*)$',
        entry,
    )
    if match:
        return f'{match.group(1)} — {match.group(2)}'
    return entry


def _load_corpus_audit_summary() -> Tuple[Optional[str], List[str]]:
    audit_path = os.path.join(_ROOT_DIR, 'CORPUS_AUDIT.txt')
    if not os.path.isfile(audit_path):
        return None, []
    try:
        with open(audit_path, encoding='utf-8') as handle:
            content = handle.read()
    except OSError:
        return None, []
    ok_match = re.search(r'^OK \((\d+)\)', content, re.MULTILINE)
    fail_match = re.search(r'^FAIL \((\d+)\)', content, re.MULTILINE)
    if not ok_match or not fail_match:
        return None, []
    summary = f'Corpus audit: {ok_match.group(1)} OK, {fail_match.group(1)} FAIL (of 24 claimed runnable)'
    issues: List[str] = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or line.startswith(('OK ', 'FAIL ')):
            continue
        if ' :: ' in line:
            issues.append(line)
    return summary, issues[:5]


def _status_update_kwargs(
    *,
    sync_id: int,
    heartbeat_id: int,
    stamp: str,
    heartbeat: bool,
) -> Dict[str, object]:
    # Lightweight path for heartbeat / repeated agent work to keep small footprint
    if heartbeat:
        task = _load_current_task_line() or ''
        program = _extract_program_from_task(task) or 'None'
        focus = task or 'No active focus'
        # Skip heavy loads (todos, logs, corpus) on pure heartbeat
        return {
            'current_program': program,
            'focus': focus,
            'todos': [],
            'confirmed': [],
            'pending': [],
            'recent_log': [],
            'issues': [],
            'extra_info': 'heartbeat (lightweight)',
            'workload_report': None,
            'user_approval': None,
            'debug_step': None,
            'heartbeat_id': heartbeat_id,
            'sync_id': sync_id,
            'stamp': stamp,
            'started': '',
            'confirmed_more': 0,
            'is_heartbeat': True,
        }

    task = _load_current_task_line() or ''
    all_todos = _load_todo_items()
    current_todos, pending_todos = _split_dashboard_todos(task, all_todos)
    confirmed, confirmed_more = _load_confirmed_ok_items()
    recent_log = [
        _format_dashboard_work_log(entry)
        for entry in _load_work_log_recent(limit=8)
    ]

    program = _extract_program_from_task(task) or 'None'
    focus = task or 'No active focus'
    last_work = _last_work_stamp()
    started = ''
    if last_work:
        try:
            started = time.strftime(
                '%Y-%m-%d %H:%M',
                time.strptime(last_work, '%Y-%m-%d %H:%M:%S'),
            )
        except ValueError:
            started = last_work[:16]

    pending: List[str] = list(pending_todos)
    try:
        from mini_basic.features.deferred import deferred_rows

        pending.append(f'{len(deferred_rows())} deferred features (WIMP, ASM, SYS...)')
    except Exception:
        pass

    audit_summary, audit_failures = _load_corpus_audit_summary()
    if audit_summary and audit_summary not in pending:
        pending.append(audit_summary)

    issues: List[str] = []
    all_passed, test_summary = _last_test_outcome()
    if not all_passed:
        issues.append(
            f'Tests not all pass: {test_summary or "see test/_run_progress.log"}',
        )
    if _source_newer_than_last_test():
        issues.append('Source changed since last test run — rerun tests')
    issues.extend(audit_failures[:3])

    activity = _activity_label(
        heartbeat=heartbeat,
        stamp=stamp,
        last_test_stamp=_last_test_run_info()[0],
        extra_lines=None,
    )
    extra_parts: List[str] = []
    if last_work:
        extra_parts.append(f'last work {last_work}')
    last_test_stamp, _ = _last_test_run_info()
    if last_test_stamp:
        test_note = 'all pass' if all_passed else 'not all pass'
        extra_parts.append(f'last test {last_test_stamp} {test_note}')
    extra_parts.append(f'status {activity}')
    workload_report: Dict[str, object] = {}
    try:
        from utils.agent_resource import verdict_for_status, workload_report_dict

        resource_snippet, resource_issue, report = verdict_for_status()
        workload_report = workload_report_dict(report)
        extra_parts.append(resource_snippet)
        if resource_issue and resource_issue not in issues:
            issues.append(resource_issue)
    except Exception:
        pass

    user_approval = _load_user_approval_checklist(program)

    debug_step = None
    try:
        from utils.debug_step import load_debug_step

        debug_step = load_debug_step()
    except Exception:
        pass

    return {
        'current_program': program,
        'focus': focus,
        'todos': current_todos or all_todos,
        'confirmed': confirmed,
        'confirmed_more': confirmed_more,
        'pending': pending,
        'recent_log': recent_log,
        'issues': issues,
        'workload_report': workload_report,
        'user_approval': user_approval,
        'debug_step': debug_step,
        'extra_info': ' · '.join(extra_parts),
        'heartbeat_id': heartbeat_id,
        'sync_id': sync_id,
        'stamp': stamp,
        'started': started,
        'is_heartbeat': heartbeat,
    }


def _build_status_html(
    lines: List[str],
    *,
    sync_id: int,
    heartbeat_id: int,
    stamp: str,
    heartbeat: bool,
) -> str:
    """Mobile-friendly dashboard page (avoids OneDrive txt black screen)."""
    del lines  # ASCII lines still written to PHONE_PROGRESS.txt
    from utils.status_updater import StatusUpdater

    kwargs = _status_update_kwargs(
        sync_id=sync_id,
        heartbeat_id=heartbeat_id,
        stamp=stamp,
        heartbeat=heartbeat,
    )
    return StatusUpdater().update(**kwargs)


def update_project_status(
    *,
    heartbeat: bool = False,
    **overrides: object,
) -> str:
    """Refresh status.html. Auto-fills from project files; pass fields to override.

    Example::

        from test.progress_runner import update_project_status
        update_project_status(
            current_program='soccerball.txt',
            focus='CIRCLE FILL + matrix rendering',
            todos=['Fix CIRCLE FILL command (BBC dialect)'],
        )

    Or use StatusUpdater directly::

        from utils.status_updater import StatusUpdater
        StatusUpdater().update(current_program='soccerball.txt', ...)
    """
    stamp = time.strftime('%Y-%m-%d %H:%M:%S')
    if heartbeat:
        sync_id = _read_counter('.sync_counter')
        heartbeat_id = _next_counter('.heartbeat_counter')
    else:
        sync_id = _next_counter('.sync_counter')
        heartbeat_id = _read_counter('.heartbeat_counter')
    kwargs = _status_update_kwargs(
        sync_id=sync_id,
        heartbeat_id=heartbeat_id,
        stamp=stamp,
        heartbeat=heartbeat,
    )
    kwargs.update(overrides)
    from utils.status_updater import StatusUpdater

    return StatusUpdater().update(**kwargs)


def write_phone_summary(
    *,
    test_line: Optional[str] = None,
    progress_line: Optional[str] = None,
    heartbeat: bool = False,
    update_rss: Optional[bool] = None,
    extra_lines: Optional[List[str]] = None,
) -> None:
    """Refresh status.html from source .txt poll (or full rebuild if not heartbeat)."""
    del test_line, progress_line, update_rss, extra_lines
    if heartbeat:
        # Scheduled / light path: rebuild only when CURRENT_TASK etc. changed.
        from utils.status_sources import heartbeat_poll

        heartbeat_poll()
        return
    update_project_status(heartbeat=False)


def write_follow_progress(
    lines: List[str],
    *,
    title: str = 'mini_basic — progress',
) -> None:
    """Write a phone-readable todo list (agents or manual updates)."""
    stamp = time.strftime('%Y-%m-%d %H:%M:%S')
    body = [_phone_safe(title), f'time {stamp}'] + [
        _phone_safe(line.rstrip()) for line in lines if line.strip()
    ]
    _write_phone_files(extra_lines=body, update_rss=False)


def _next_counter(name: str) -> int:
    counter_path = os.path.join(_ROOT_DIR, name)
    try:
        with open(counter_path, encoding='utf-8') as handle:
            counter = int(handle.read().strip())
    except (OSError, ValueError):
        counter = 0
    counter += 1
    with open(counter_path, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(str(counter))
    return counter


def _read_counter(name: str) -> int:
    counter_path = os.path.join(_ROOT_DIR, name)
    try:
        with open(counter_path, encoding='utf-8') as handle:
            return int(handle.read().strip())
    except (OSError, ValueError):
        return 0


def _next_sync_ids(*, heartbeat: bool) -> Tuple[int, int]:
    """Return (work_sync_id, heartbeat_id). Work counter bumps only on real updates."""
    heartbeat_id = _next_counter('.heartbeat_counter')
    if heartbeat:
        return _read_counter('.sync_counter'), heartbeat_id
    return _next_counter('.sync_counter'), heartbeat_id


def _atomic_write(path: str, text: str, *, encoding: str = 'utf-8') -> None:
    """Replace file atomically so OneDrive sees a new revision."""
    directory = os.path.dirname(path) or '.'
    os.makedirs(directory, exist_ok=True)
    tmp_path = os.path.join(directory, f'.{os.path.basename(path)}.tmp')
    with open(tmp_path, 'w', encoding=encoding, newline='\r\n') as handle:
        handle.write(text)
    try:
        os.replace(tmp_path, path)
    except PermissionError:
        # OneDrive or lock in some envs; fall back to direct write
        try:
            with open(path, 'w', encoding=encoding, newline='\r\n') as handle:
                handle.write(text)
            os.unlink(tmp_path)
        except Exception:
            pass


def _atomic_write_phone(path: str, text: str) -> None:
    """Tablet-safe: ASCII, CRLF, UTF-8 BOM helps some OneDrive viewers."""
    ascii_text = _phone_safe(text)
    if not ascii_text.endswith('\r\n'):
        ascii_text = ascii_text.rstrip('\r\n') + '\r\n'
    directory = os.path.dirname(path) or '.'
    os.makedirs(directory, exist_ok=True)
    tmp_path = os.path.join(directory, f'.{os.path.basename(path)}.tmp')
    with open(tmp_path, 'wb') as handle:
        handle.write(b'\xef\xbb\xbf')  # UTF-8 BOM
        handle.write(ascii_text.encode('ascii'))
    try:
        os.replace(tmp_path, path)
    except PermissionError:
        try:
            with open(path, 'wb') as handle:
                handle.write(b'\xef\xbb\xbf')
                handle.write(ascii_text.encode('ascii'))
            os.unlink(tmp_path)
        except Exception:
            pass


def _mirror_stub_dirs() -> List[str]:
    """Stale C:\\Users\\Tony\\mini_basic before OneDrive junction is created."""
    stub = _LOCAL_STUB_DIR
    if not os.path.isdir(stub):
        return []
    try:
        if os.path.realpath(stub) == os.path.realpath(_ROOT_DIR):
            return []
    except OSError:
        pass
    if os.path.isfile(os.path.join(stub, 'README.md')):
        return []
    return [stub]


def _stub_redirect_text() -> str:
    return (
        'WRONG FOLDER — stale stub (not the real project)\n'
        '==================================================\n'
        '\n'
        f'Real project (OneDrive, phone + RSS):\n'
        f'  {_ROOT_DIR}\n'
        '\n'
        f'This path is only a mirror until junction is created:\n'
        f'  {_LOCAL_STUB_DIR}\n'
        '\n'
        'Fix permanently:\n'
        '  1. Close Cursor\n'
        '  2. Run finish_junction.ps1 in the OneDrive mini_basic folder\n'
        '  3. Reopen Cursor\n'
        '\n'
        'Follow progress: PROGRESS.rss (see RSS_SETUP.txt on OneDrive)\n'
    )


def _follow_progress_redirect() -> str:
    return (
        'Do not use this file.\n'
        'Open STATUS.txt first.\n'
        'Or PHONE_PROGRESS.txt\n'
        'Pull down to refresh in OneDrive.\n'
    )


def _rss_readme_text() -> str:
    return (
        'skip rss\n'
        'open STATUS.txt on tablet\n'
        'do not open files ending in .rss\n'
    )


def _mirror_to_stub(
    *,
    phone_text: str,
    progress_txt: str,
    status_text: str,
    legacy_text: str,
    stamp_text: str,
    rss_xml: str,
    rss_readme: str,
) -> None:
    for stub_dir in _mirror_stub_dirs():
        _atomic_write_phone(os.path.join(stub_dir, 'PHONE_PROGRESS.txt'), phone_text)
        _atomic_write_phone(os.path.join(stub_dir, 'PROGRESS.txt'), progress_txt)
        _atomic_write_phone(os.path.join(stub_dir, 'STATUS.txt'), status_text)
        _atomic_write_phone(os.path.join(stub_dir, 'FOLLOW_PROGRESS.txt'), legacy_text)
        _atomic_write_phone(os.path.join(stub_dir, 'SYNC_STAMP.txt'), stamp_text)
        _atomic_write(os.path.join(stub_dir, 'PROGRESS.rss'), rss_xml)
        _atomic_write_phone(os.path.join(stub_dir, 'PROGRESS_RSS_README.txt'), rss_readme)
        _atomic_write(os.path.join(stub_dir, 'WHERE_IS_THE_PROJECT.txt'), _stub_redirect_text())


def _write_phone_files(
    *,
    heartbeat: bool = False,
    test_line: Optional[str] = None,
    progress_line: Optional[str] = None,
    extra_lines: Optional[List[str]] = None,
    update_rss: bool = True,
) -> None:
    """Only status.html (all other phone / log / rss files removed)."""
    try:
        from utils.status_updater import StatusUpdater
        StatusUpdater().update()
    except Exception:
        pass
    _mirror_to_stub(
        phone_text=phone_text,
        progress_txt=phone_text,
        status_text=status_text,
        legacy_text=legacy_text,
        stamp_text=stamp_text,
        rss_xml=rss_xml,
        rss_readme=rss_readme,
    )


def _rss_channel_link() -> str:
    if os.path.isfile(_RSS_FEED_URL_PATH):
        with open(_RSS_FEED_URL_PATH, encoding='utf-8') as handle:
            link = handle.read().strip()
            if link and not link.startswith('#'):
                return link
    return 'https://onedrive.live.com/mini_basic/PROGRESS.rss'


def _rss_item_title(phone_text: str, *, sync_id: int) -> str:
    for line in phone_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith('sync #'):
            continue
        if stripped.startswith('('):
            continue
        if 'OneDrive' in stripped and 'PHONE_PROGRESS' in stripped:
            continue
        return f'#{sync_id} {stripped[:120]}'
    return f'#{sync_id} mini_basic progress update'


def _load_rss_history() -> List[dict]:
    if not os.path.isfile(_RSS_HISTORY_PATH):
        return []
    try:
        with open(_RSS_HISTORY_PATH, encoding='utf-8') as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return data
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return []


def _save_rss_history(history: List[dict]) -> None:
    with open(_RSS_HISTORY_PATH, 'w', encoding='utf-8', newline='\n') as handle:
        json.dump(history, handle, indent=2)
        handle.write('\n')


def _build_rss_xml(history: List[dict], *, channel_link: str) -> str:
    build_date = formatdate(usegmt=True)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        '<channel>',
        f'<title>{escape("mini_basic progress")}</title>',
        f'<link>{escape(channel_link)}</link>',
        f'<description>{escape("BBC BASIC interpreter work log - for RSS apps only, not Notepad")}</description>',
        '<language>en</language>',
        f'<lastBuildDate>{build_date}</lastBuildDate>',
        f'<generator>{escape("mini_basic progress_runner")}</generator>',
    ]
    for entry in history:
        title = escape(str(entry.get('title', 'progress update')))
        guid = escape(f"sync-{entry.get('sync_id', 0)}")
        pub_date = str(entry.get('pubDate', build_date))
        body = str(entry.get('body', ''))
        lines.extend(
            [
                '<item>',
                f'<title>{title}</title>',
                f'<description><![CDATA[{body}]]></description>',
                f'<pubDate>{pub_date}</pubDate>',
                f'<guid isPermaLink="false">{guid}</guid>',
                '</item>',
            ]
        )
    lines.extend(['</channel>', '</rss>', ''])
    return '\n'.join(lines)


def _update_rss_feed(phone_text: str, *, sync_id: int, stamp: str) -> str:
    history = _load_rss_history()
    history.insert(
        0,
        {
            'sync_id': sync_id,
            'title': _rss_item_title(phone_text, sync_id=sync_id),
            'body': phone_text,
            'pubDate': formatdate(usegmt=True),
            'stamp': stamp,
        },
    )
    history = history[:_RSS_MAX_ITEMS]
    _save_rss_history(history)
    rss_xml = _build_rss_xml(history, channel_link=_rss_channel_link())
    _atomic_write(_RSS_PATH, rss_xml)
    return rss_xml






class ProgressLoggingRunner(unittest.TextTestRunner):
    """Only status.html is produced now. All other phone/log efforts removed."""

    def run(self, test):
        sys.stderr.write(f'Discovered {test.countTestCases()} tests\n')
        sys.stderr.flush()
        result = super().run(test)
        # Only status.html
        try:
            from utils.status_updater import StatusUpdater
            StatusUpdater().update()
            sys.stderr.write(f'Updated: {_STATUS_HTML_PATH}\n')
        except Exception as e:
            sys.stderr.write(f'(status.html update skipped: {e})\n')
        sys.stderr.flush()
        return result

import concurrent.futures   # add this import near the top if not present

def run_discover(
    start_dir: Optional[str] = None,
    pattern: str = 'test_*.py',
    *,
    verbosity: int = 1,
    timeout: Optional[float] = 180,   # ← NEW: 3 minutes default total timeout
) -> int:
    if start_dir is None:
        start_dir = _TEST_DIR

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=start_dir, pattern=pattern)
    runner = ProgressLoggingRunner(verbosity=verbosity)

    if timeout and timeout > 0:
        print(f"[progress_runner] Starting with overall timeout of {timeout} seconds")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(runner.run, suite)
            try:
                result = future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                print(f"\n*** OVERALL TIMEOUT after {timeout} seconds ***")
                print("Run was terminated. Check the latest log in test/logs/ for details.")
                return 1
    else:
        result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1
