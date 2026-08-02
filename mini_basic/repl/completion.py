"""Tab-completion helpers for the interactive REPL.

Completion uses GNU readline (Unix) or pyreadline3/pyreadline (Windows). The REPL
must call ``configure_readline()`` once before the input loop; without a readline
backend, ``input()`` behaves as usual and Tab inserts a literal tab.

Supported contexts (filename completion in ``working_dir``):

- ``LOAD path`` — ``*.bas`` and common backup names (``.bak``, ``.backup``, ``~``, …)
- ``SAVE [PRETTY] path`` — same extensions as LOAD
- ``RUN path.bas`` (``.bas`` / ``.mbs`` preferred, all files allowed)
- ``CD path`` (directories only; all commands include ``subdir/`` for navigation)
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

# After BBC/VAX abbrev expansion (LO. → LOAD, SA. → SAVE, …).
_FILE_COMMAND_RE = re.compile(
    r'^(?:LOAD|SAVE(?:\s+PRETTY)?|RUN|CD)(\s+)(.*)$',
    re.IGNORECASE,
)

_RUN_PREFERRED_EXTS = frozenset({'.bas', '.mbs', '.cmd', '.txt', '.bbc'})

# LOAD/SAVE: BASIC programs and typical editor/OS backup suffixes.
_LOAD_SAVE_EXTS = frozenset({'.bas', '.bak', '.backup', '.orig', '.old','.bbc'})


def _completion_name_sort_key(name: str) -> tuple[int, str]:
    """Shorter names first, then case-insensitive alphabetical."""
    return len(name), name.lower()


def _case_common_prefix(matches: Sequence[str]) -> str:
    """Longest case-insensitive prefix shared by all ``matches``."""
    if not matches:
        return ''
    lower = [m.lower() for m in matches]
    prefix = os.path.commonprefix(lower)
    if not prefix:
        return ''
    shortest = min(matches, key=_completion_name_sort_key)
    return shortest[: len(prefix)]


def is_load_save_file(name: str) -> bool:
    """True if ``name`` looks like a BASIC source file or a backup of one."""
    lower = name.lower()
    if lower.endswith('~'):
        return True
    ext = os.path.splitext(lower)[1]
    if ext in _LOAD_SAVE_EXTS:
        return True
    # e.g. program.bas.bak
    stem, ext = os.path.splitext(lower)
    return ext == '.bak' and stem.endswith('.bas')


@dataclass(frozen=True)
class FileCompletionContext:
    """Parsed REPL line ready for filename completion."""

    command: str
    partial_path: str
    quoted: bool


def split_partial_path(fragment: str) -> tuple[str, str]:
    """Split a partial path into ``(directory, basename_prefix)``.

    ``directory`` uses forward slashes internally (may be empty). ``basename_prefix``
    is the incomplete final path component. Handles an opening quote without a
    closing quote.
    """
    fragment = fragment.strip()
    if not fragment:
        return '', ''

    quoted = False
    if fragment[0] in '"\'':
        quoted = True
        fragment = fragment[1:]
        if fragment.endswith(fragment[0]) and len(fragment) > 1:
            fragment = fragment[:-1]

    fragment = fragment.replace('/', os.sep)
    if os.sep in fragment:
        directory, _, base = fragment.rpartition(os.sep)
        return directory, base
    return '', fragment


def file_command_context(line: str) -> Optional[FileCompletionContext]:
    """Return completion context if ``line`` is a partial LOAD/SAVE/RUN/CD command."""
    if not line:
        return None
    match = _FILE_COMMAND_RE.match(line)
    if match is None:
        return None
    arg = match.group(2)
    header = line[: match.start(2)]
    command = 'SAVE' if header.upper().startswith('SAVE') else header.split(None, 1)[0].upper()
    quoted = arg.lstrip().startswith(('"', "'"))
    partial = arg.strip()
    if quoted and partial and partial[0] in '"\'':
        partial = partial[1:]
    directory, base = split_partial_path(partial)
    joined = os.path.join(directory, base) if directory else base
    return FileCompletionContext(
        command=command,
        partial_path=joined,
        quoted=quoted,
    )


def _resolve_search_dir(working_dir: str, directory: str) -> Optional[str]:
    if not directory:
        return working_dir
    if os.path.isabs(directory):
        candidate = os.path.normpath(directory)
    else:
        candidate = os.path.normpath(os.path.join(working_dir, directory))
    if os.path.isdir(candidate):
        return candidate
    # User may be mid-typing a new directory component — try parent.
    parent = os.path.dirname(candidate)
    if parent and os.path.isdir(parent):
        return parent
    return None


def _display_name(name: str, is_dir: bool, command: str) -> str:
    if is_dir:
        return name + os.sep
    return name


def iter_filename_completions(
    working_dir: str,
    context: FileCompletionContext,
) -> Iterable[str]:
    """Yield display strings that complete ``context.partial_path``."""
    directory, base = split_partial_path(context.partial_path)
    search_dir = _resolve_search_dir(working_dir, directory)
    if search_dir is None:
        return

    base_lower = base.lower()
    try:
        names = os.listdir(search_dir)
    except OSError:
        return

    dirs: List[str] = []
    files: List[str] = []
    for name in names:
        if name.startswith('.'):
            continue
        if not name.lower().startswith(base_lower):
            continue
        full = os.path.join(search_dir, name)
        if os.path.isdir(full):
            dirs.append(name)
        else:
            files.append(name)

    dirs.sort(key=_completion_name_sort_key)
    files.sort(key=_completion_name_sort_key)

    if context.command == 'CD':
        for name in dirs:
            yield _display_name(name, True, context.command)
        return

    if context.command == 'RUN':
        preferred = sorted(
            (n for n in files if os.path.splitext(n)[1].lower() in _RUN_PREFERRED_EXTS),
            key=_completion_name_sort_key,
        )
        other = sorted(
            (n for n in files if n not in preferred),
            key=_completion_name_sort_key,
        )
        for group in (preferred, other):
            for name in group:
                yield name
        for name in dirs:
            yield _display_name(name, True, context.command)
        return

    # LOAD / SAVE — .bas and backup files, then subdirectories for navigation.
    if context.command in ('LOAD', 'SAVE'):
        files = [n for n in files if is_load_save_file(n)]
    for name in files:
        yield name
    for name in dirs:
        yield _display_name(name, True, context.command)


def compute_matches(
    working_dir: str,
    line: str,
    text: str,
) -> List[str]:
    """Return readline-style matches (each starts with ``text``)."""
    context = file_command_context(line)
    if context is None:
        return []

    directory, base = split_partial_path(context.partial_path)
    candidates: List[str] = []
    for item in iter_filename_completions(working_dir, context):
        if directory:
            completion = f'{directory}{os.sep}{item}'
        else:
            completion = item
        if context.quoted and ' ' in completion:
            completion = f'"{completion}"'
        candidates.append(completion)

    if not text:
        return candidates
    text_lower = text.lower()
    return [m for m in candidates if m.lower().startswith(text_lower)]


@dataclass
class TabCompletionCycle:
    """State for repeated Tab presses over the same completion set."""

    matches: Tuple[str, ...]
    index: int
    prefix: str


def accept_unique_completion(prefix: str, matches: Sequence[str]) -> Optional[str]:
    """If exactly one match extends ``prefix``, return that full match."""
    narrowed = [
        m for m in matches
        if len(m) > len(prefix) and m.lower().startswith(prefix.lower())
    ]
    if len(narrowed) == 1:
        return narrowed[0]
    return None


def advance_tab_completion(
    prefix: str,
    matches: Sequence[str],
    cycle: TabCompletionCycle | None,
) -> Tuple[str, TabCompletionCycle | None]:
    """Return ``(replacement, cycle)`` after one Tab press.

    First Tab extends to the case-insensitive common prefix when possible.
    If only one candidate shares that prefix, the full match is applied
    (including a trailing ``/`` on directories). Further Tab presses cycle.
    """
    if not matches:
        return prefix, None
    if len(matches) == 1:
        return matches[0], None

    normalized = tuple(matches)
    common = _case_common_prefix(normalized)

    if cycle is None or cycle.prefix != prefix or cycle.matches != normalized:
        unique = accept_unique_completion(prefix, normalized)
        if unique is not None:
            return unique, None
        if len(common) > len(prefix):
            unique = accept_unique_completion(common, normalized)
            if unique is not None:
                return unique, None
            return common, TabCompletionCycle(normalized, -1, common)
        cycle = TabCompletionCycle(normalized, -1, prefix)

    next_index = (cycle.index + 1) % len(normalized)
    return normalized[next_index], TabCompletionCycle(normalized, next_index, prefix)


def configure_readline(
    working_dir: Callable[[], str],
    expand_abbrev: Callable[[str], str],
    get_readline: Callable[[], object | None],
) -> bool:
    """Install the REPL tab completer. Returns True if readline is available."""
    readline = get_readline()
    if readline is None:
        return False

    readline.set_completer_delims(' \t\n;')
    for binding in (
        'tab: complete',
        'set show-all-if-ambiguous on',
    ):
        try:
            readline.parse_and_bind(binding)
        except (AttributeError, ValueError):
            pass

    cache: dict[str, List[str]] = {'matches': []}

    def completer(text: str, state: int) -> Optional[str]:
        if state == 0:
            buffer = readline.get_line_buffer()
            endidx = readline.get_endidx()
            fragment = buffer[:endidx]
            line = expand_abbrev(fragment)
            # Abbrev expander strips whitespace; restore trailing space for "LO. " → "LOAD ".
            if fragment.endswith((' ', '\t')) and line and not line.endswith((' ', '\t')):
                line += fragment[len(fragment.rstrip()):]
            cache['matches'] = compute_matches(working_dir(), line, text)
        try:
            return cache['matches'][state]
        except IndexError:
            return None

    readline.set_completer(completer)
    return True


__all__ = [
    'FileCompletionContext',
    'TabCompletionCycle',
    'accept_unique_completion',
    'advance_tab_completion',
    'compute_matches',
    'configure_readline',
    'file_command_context',
    'is_load_save_file',
    'iter_filename_completions',
    'split_partial_path',
]
