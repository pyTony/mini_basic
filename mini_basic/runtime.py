"""mini-BASIC interpreter — runtime facade.

``BASICInterpreter`` is composed of mixins under ``runtime_parts/``.
Module-level REPL/CLI helpers and ``main`` remain in this file (extracted
from the former monorepo). The full pre-split monorepo is archived as
``backup/runtime_monolith.py``.

See ``RUNTIME_MODULARIZATION_STATUS.md`` for history.
"""
import fnmatch
import json
import math
import random
import re
import os
import struct
import sys
import time

from .config import DEFAULT_CONFIG, InterpreterConfig, SYSTEM_VAR_SPEC
from .dialect_hint import DialectHint, parse_comment_dialect_line, split_dialect_hints
from .constants import (
    CLI_EXIT_WORDS as _CLI_EXIT_WORDS,
    EXIT_HOLD_CONSOLE,
    EXPR_RESERVED_WORDS as _EXPR_RESERVED_WORDS,
    NUMERIC_BUILTIN_FUNCS as _NUMERIC_BUILTIN_FUNCS,
    NUMERIC_BUILTIN_FUNC_RE as _NUMERIC_BUILTIN_FUNC_RE,
    SAFE_EVAL_GLOBALS as _SAFE_EVAL_GLOBALS,
)
from .expr.compile import CompiledExpr, int_slot
from .expr.patterns import (
    RE_ARRAY_HEAD as _RE_ARRAY_HEAD,
    RE_COND_EQ as _RE_COND_EQ,
    RE_COND_NE as _RE_COND_NE,
    RE_DEF_PROC as _RE_DEF_PROC,
    RE_DYNAMIC_CALL_REMAINS as _RE_DYNAMIC_CALL_REMAINS,
    RE_FILE_FUNC as _RE_FILE_FUNC,
    RE_FILE_FUNC_BBC as _RE_FILE_FUNC_BBC,
    RE_FN_CALL as _RE_FN_CALL,
    RE_FUNC_CALL as _RE_FUNC_CALL,
    RE_HAS_LETTER as _RE_HAS_LETTER,
    RE_INKEY_CALL as _RE_INKEY_CALL,
    RE_INT_DIV as _RE_INT_DIV,
    RE_MOD as _RE_MOD,
    RE_NUMERIC_FUNC_CALL as _RE_NUMERIC_FUNC_CALL,
    RE_PROC_CALL as _RE_PROC_CALL,
    RE_TIME as _RE_TIME,
    RE_VAR_BASE_FULL as _RE_VAR_BASE_FULL,
    VAR_BASE_PATTERN as _VAR_BASE_PATTERN,
)

from .format import UsingFormatter
from .format.save_case import (
    Fold as _SaveFold,
    fold_from_save_case as _fold_from_save_case,
    format_program_line as _format_program_line_save_case,
    format_statement_part as _format_statement_part_save_case,
)
from .repl.completion import configure_readline as _configure_repl_readline
from .repl.help_browser import run_help_browser as _run_help_browser
from .util import (
    basic_truth as _basic_truth,
    hard_exit as _hard_exit,
    near_equal as _near_equal,
    near_equal_sig as _near_equal_sig,
    probe_float_platform as _probe_float_platform,
)
from .type_system import (
    ArrayStorage,
    BasicRuntimeError,
    ChainTransfer,
    DataItem,
    Dialect,
    FieldBuffer,
    FileChannel,
    FnReturn,
    CaseBlockLayout,
    CaseFrame,
    IfBlockLayout,
    IfFrame,
    ListCommand,
    LoopFrame,
    ProcReturn,
    ProgramExit,
    UserFunction,
    UserProcedure,
    VarKind,
)
from typing import Callable, Dict, List, Optional, Set, TextIO, Tuple

_SYSTEM_VAR_SPEC = SYSTEM_VAR_SPEC

       
# BBC Micro MODE specs (text grid, graphics resolution, PAR) — see bbc_modes.py.
from mini_basic.bbc_modes import bbc_mode_spec

from .runtime_parts.core import RuntimeCoreMixin
from .runtime_parts.program import RuntimeProgramMixin
from .runtime_parts.expr import RuntimeExprMixin
from .runtime_parts.defs import RuntimeDefsMixin
from .runtime_parts.execution import RuntimeExecutionMixin
from .runtime_parts.io import RuntimeIoMixin
from .runtime_parts.graphics import RuntimeGraphicsMixin
from .runtime_parts.dialect import RuntimeDialectMixin

class BASICInterpreter(RuntimeCoreMixin, RuntimeProgramMixin, RuntimeExprMixin, RuntimeDefsMixin, RuntimeExecutionMixin, RuntimeIoMixin, RuntimeGraphicsMixin, RuntimeDialectMixin):
    """BBC/mini BASIC interpreter (mixin composition)."""

    _VAR_MAX_LEN = 255
    _VAR_BASE_PATTERN = _VAR_BASE_PATTERN
    _RE_VAR_BASE_FULL = _RE_VAR_BASE_FULL
    _RE_MOD = _RE_MOD
    _RE_INT_DIV = _RE_INT_DIV
    _RE_TIME = _RE_TIME
    _RE_HAS_LETTER = _RE_HAS_LETTER
    _RE_COND_NE = _RE_COND_NE
    _RE_COND_EQ = _RE_COND_EQ
    _RE_PARSE_CMD = re.compile(
        r'^(PRINT#|INPUT#|WRITE#|CLOSE#|PRINT(?!#)|INPUT(?!#)|WRITE(?!#)|ENDIF|ELSEIF|ELIF|ELSE|ENDCASE|OTHERWISE|WHEN|CASE|ENDPROC|END(?!IF)|REPEAT|REPORT|UNTIL|EXIT|FOR|NEXT|WHILE|WEND|BREAK|CONTINUE|RESTORE|READ|DATA|DEF|DIM|LOCAL|LET|IF|GOTO|GOSUB|RESUME|RETURN|REM|MODE|VDU|COLOUR|COLOR|CLS|CLG|GCOL|RECTANGLE|CIRCLE|MOUSE|WIDTH|TRACE|OFF|ON|MOVE|DRAW|ORIGIN|PLOT|SPRITEDEF|SPRITE|STOP|OSCLI|CHAIN|RUN|WAIT|INSTALL|SOUND|ENVELOPE)\s*(.*)$',
        re.IGNORECASE,
    )
    _RE_PARSE_CMD_BBC = re.compile(
        r'^(PRINT#|INPUT#|WRITE#|CLOSE#|PRINT(?!#)|INPUT(?!#)|WRITE(?!#)|ENDIF|ELSEIF|ELIF|ELSE|ENDCASE|OTHERWISE|WHEN|CASE|ENDPROC|END(?!IF)|REPEAT|REPORT|UNTIL|EXIT|FOR|NEXT|WHILE|WEND|BREAK|CONTINUE|RESTORE|READ|DATA|DEF|DIM|LOCAL|LET|IF|GOTO|GOSUB|RESUME|RETURN|REM|MODE|VDU|COLOUR|COLOR|CLS|CLG|GCOL|RECTANGLE|CIRCLE|MOUSE|WIDTH|TRACE|OFF|ON|MOVE|DRAW|ORIGIN|PLOT|SPRITEDEF|SPRITE|STOP|OSCLI|CHAIN|RUN|WAIT|INSTALL|SOUND|ENVELOPE)\s*(.*)$',
    )
    _RE_PROC_CALL = _RE_PROC_CALL
    _RE_DEF_PROC = _RE_DEF_PROC
    _RE_ARRAY_HEAD = _RE_ARRAY_HEAD
    _RE_FILE_FUNC = _RE_FILE_FUNC
    _RE_FILE_FUNC_BBC = _RE_FILE_FUNC_BBC
    _RE_HASH_FILE_CMD = re.compile(
        r'^(PRINT|INPUT|WRITE|CLOSE)\s+#\s*',
        re.IGNORECASE,
    )
    _RE_FUNC_CALL = _RE_FUNC_CALL
    _RE_INKEY_CALL = _RE_INKEY_CALL
    _RE_NUMERIC_FUNC_CALL = _RE_NUMERIC_FUNC_CALL
    _RE_FN_CALL = _RE_FN_CALL
    _RE_DYNAMIC_CALL_REMAINS = _RE_DYNAMIC_CALL_REMAINS
    _RE_GOTO_GOSUB = re.compile(r'\b(?:GOTO|GOSUB)\s+\S+', re.IGNORECASE)
    _RE_ON_ERROR = re.compile(
        r'^ON\s+ERROR\s+(GOTO|GOSUB)\s+(\S+)\s*$',
        re.IGNORECASE,
    )
    _RE_ON_GOTO_GOSUB = re.compile(
        r'^ON\s+(.+?)\s+(GOTO|GOSUB)\s+(.+)$',
        re.IGNORECASE,
    )
    _MITS_FORBIDDEN_CMDS = frozenset({
        'WHILE', 'WEND', 'ENDIF', 'ELSEIF', 'ELIF', 'CONTINUE', 'BREAK',
        'REPEAT', 'UNTIL', 'PROC', 'ENDPROC', 'EXIT',
    })
    _UNIMPLEMENTED_COMMANDS = {
        # Platform-bound / OS / machine language commands are not implemented in this interpreter.
        # Per user guidance: document and do not directly test them in core Phase-1 (non-graphics).
        # They report ? Unimplemented: instead of silent fail.
        # See test_unknown_syntax.py for coverage of error reporting (non-platform ones prioritized).
        'SYS': 'SYS (RISC OS / OS call)',
        'CALL': 'CALL (machine-code subroutine)',
        'USR': 'USR (machine-code function)',
        'INSTALL': 'INSTALL (library load)',
        'OSASM': 'OSASM (inline assembler)',
        'MENU': 'MENU (RISC OS WIMP)',
        'ATTACH': 'ATTACH (RISC OS WIMP)',
        'DETACH': 'DETACH (RISC OS WIMP)',
        'ICON': 'ICON (RISC OS WIMP)',
        'WINDOW': 'WINDOW (RISC OS WIMP)',
        # SOUND: timing-only (no audio). ENVELOPE: accepted no-op (welcome.bbc).
    }
    _NOT_IMPLEMENTED_STATEMENTS = {
        'ELLIPSE': 'ELLIPSE (and ELLIPSE FILL)',
        'FLOOD': 'FLOOD (flood fill)',
        # Add others as identified (e.g. some advanced VDU, VOICE etc. if top-level)
    }
    _MINI_ONLY_CMDS = frozenset({'BREAK', 'CONTINUE'})
    _MINI_ONLY_FUNCS = frozenset({
        'ARG', 'FG$', 'BG$', 'RGB$', 'BGRGB$', 'ANSI$', 'RESET$',
    })
    _NUMBERED_GOTO_DIALECTS = frozenset({'mits', 'commodore', 'tiny'})
    _IF_GOTO_DIALECTS = frozenset({'mini', 'mits', 'bbc', 'commodore'})
    _IF_THEN_LINE_DIALECTS = frozenset({'mini', 'mits', 'bbc', 'commodore'})
    _GRAPHICS_CMDS = frozenset({
        'MODE', 'CLG', 'GCOL', 'MOVE', 'DRAW', 'ORIGIN', 'PLOT',
        'SPRITEDEF', 'SPRITE', 'RECTANGLE', 'CIRCLE',
    })
    _BBC_DISPLAY_CMDS = frozenset({
        'MODE', 'CLS', 'CLG', 'COLOUR', 'COLOR', 'VDU', 'WAIT',
    })
    _GRAPHICS_DIALECTS = frozenset({'mini', 'bbc'})
    _END_KEYWORD_HINTS = {
        'IF': 'ENDIF',
        'FN': 'END DEF',
        'WHILE': 'WEND',
        'PROC': 'ENDPROC',
    }
    _BBC_BARE_STRING_ARG_FUNCS = frozenset({'LEN', 'VAL'})
    _BBC_BARE_NO_ARG_FUNCS = frozenset({'PI', 'POS', 'VPOS', 'GET', 'INKEY'})
    _FILE_CHANNEL_HASH_FUNCS = frozenset({'EOF', 'LOF', 'LOC', 'PTR', 'EXT'})
    _RE_BAD_PERCENT_MOD = re.compile(
        r'(?:\d|\))\s*%'
        rf'|{_VAR_BASE_PATTERN}\s*%\s*\d'
    )
    # Arithmetic compounds only (+= -= *= /=). Not AND=/OR= (not BASIC; broke aand=).
    _COMPOUND_ASSIGN_RE = re.compile(
        r'^([_A-Za-z][A-Za-z0-9_]*[%$!#&]?(?:\s*\(.*\))?)\s*'
        r'([+\-*/]=)\s*(.+)$',
        re.DOTALL,
    )
    _STMT_KEYWORDS = (
        'PRINT', 'INPUT', 'WRITE', 'FOR', 'NEXT', 'WHILE', 'WEND', 'REPEAT', 'UNTIL',
        'BREAK', 'CONTINUE', 'EXIT', 'PROC', 'ENDPROC',
        'LET', 'IF', 'ELSE', 'ELSEIF', 'ELIF', 'ENDIF', 'CASE', 'WHEN', 'OTHERWISE', 'ENDCASE',
        'GOTO', 'GOSUB', 'RESUME', 'RETURN',
        'DATA', 'DEF', 'DIM', 'READ', 'RESTORE', 'END', 'REM',
        'MODE', 'VDU', 'COLOUR', 'COLOR', 'CLS', 'CLG', 'GCOL', 'RECTANGLE', 'CIRCLE', 'MOUSE',
        'WIDTH', 'OFF', 'ON', 'MOVE', 'DRAW',
        'ORIGIN', 'PLOT', 'SPRITEDEF', 'SPRITE', 'STOP', 'OSCLI', 'CHAIN', 'RUN', 'WAIT',
    )
    _GLUABLE_AFTER_KEYWORDS = frozenset([
        'FOR', 'LET', 'DIM', 'READ', 'INPUT', 'LOCAL', 'DEF', 'PROC', 'FN',
        'GOTO', 'GOSUB', 'RESUME', 'RETURN', 'RESTORE', 'ON', 'DATA',
        'NEXT', 'UNTIL', 'WEND', 'REPEAT',
    ])



def _get_readline_module():
    try:
        import readline
        return readline
    except ImportError:
        pass
    try:
        import importlib
        for name in ('pyreadline3', 'pyreadline'):
            try:
                return importlib.import_module(name)
            except ImportError:
                continue
    except ImportError:
        pass
    return None


def _windows_arrow_action(getwch, prefix: str) -> Optional[str]:
    """Map special keys (arrows, Home/End, Ctrl+Left/Right, …)."""
    from .repl.windows_input import parse_special_key

    return parse_special_key(getwch, prefix)


def _windows_apply_arrow(
    action: str,
    buffer: List[str],
    cursor: int,
    default: str,
) -> Tuple[List[str], int, bool]:
    """Apply named line-edit action (shared with REPL)."""
    from .repl.windows_input import apply_line_edit

    return apply_line_edit(action, buffer, cursor, default=default)


def _windows_editing_input(
    prompt: str,
    default: str = '',
    getwch=None,
) -> str:
    """AUTO/EDIT line editor: Home/End, word motion, kill keys (like terminal)."""
    from .repl.windows_input import windows_editing_input

    # Keep C0 controls out of program source (same as helpers path).
    def _sanitize(text: str) -> str:
        return ''.join(ch for ch in text if ch == '\t' or (ord(ch) >= 32 and ord(ch) != 127))

    text = windows_editing_input(prompt, default=_sanitize(default), getwch=getwch)
    return _sanitize(text)


def _prompt_editing_input(prompt: str, default: str = '') -> str:
    """
    Prompt for editable BASIC source (EDIT, AUTO, bare line number).

    Prefer readline (GNU on Unix, pyreadline3 on Windows) so Unicode and
    history work without the custom msvcrt redraw path. Fall back to that
    editor only when no readline backend is available.
    """
    def _sanitize(text: str) -> str:
        return ''.join(ch for ch in text if ch == '\t' or (ord(ch) >= 32 and ord(ch) != 127))

    default = _sanitize(default)
    readline = _get_readline_module()
    if readline is not None:

        def _prefill_hook() -> None:
            readline.set_startup_hook(None)
            if default:
                readline.insert_text(default)
                if hasattr(readline, 'redisplay'):
                    readline.redisplay()

        # Do not clear_history(): that wiped pastable history when editing lines.
        readline.set_startup_hook(_prefill_hook)
        try:
            return _sanitize(input(prompt).rstrip())
        finally:
            readline.set_startup_hook(None)

    if sys.platform == 'win32' and sys.stdin.isatty():
        try:
            return _windows_editing_input(prompt, default)
        except (ImportError, OSError, ValueError):
            pass

    return _sanitize(input(prompt).rstrip())


def _parse_path_arg(text: str) -> str:
    text = text.strip()
    if not text:
        raise ValueError('missing path')
    if text[0] in '"\'':
        quote = text[0]
        end = 1
        while end < len(text):
            if text[end] == quote:
                if end + 1 < len(text) and not text[end + 1].isspace():
                    raise ValueError('unexpected text after quoted path')
                return text[1:end]
            end += 1
        raise ValueError('unterminated quoted path')
    return text


def _parse_file_command(text: str, command: str) -> Optional[str]:
    match = re.match(rf'^{command}\s+(.*)$', text.strip(), re.IGNORECASE)
    if not match:
        return None
    try:
        return _parse_path_arg(match.group(1))
    except ValueError:
        return None


def _parse_auto_command(text: str) -> Tuple[int, int]:
    match = re.match(r'^AUTO(?:\s+(\d+)(?:\s*,\s*(\d+))?)?$', text.strip(), re.IGNORECASE)
    if not match:
        raise ValueError('invalid AUTO command')
    start = int(match.group(1)) if match.group(1) else 10
    step = int(match.group(2)) if match.group(2) else 10
    return start, step


def _parse_renumber_command(text: str) -> Optional[Tuple[int, int]]:
    match = re.match(
        r'^(?:RENUMBER|REN)(?:\s+(\d+)(?:\s*,\s*(\d+))?)?$',
        text.strip(),
        re.IGNORECASE,
    )
    if not match:
        return None
    start = int(match.group(1)) if match.group(1) else 10
    step = int(match.group(2)) if match.group(2) else 10
    if step <= 0:
        raise ValueError('invalid RENUMBER step')
    return start, step


def _parse_list_range(text: str) -> Optional[Tuple[Optional[int], Optional[int]]]:
    text = text.strip()
    if not text:
        return None
    # Explicit two-sided range: "120,150" or "120-150"
    range_match = re.fullmatch(r'(\d+)\s*[-,]\s*(\d+)', text)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        if start > end:
            start, end = end, start
        return start, end
    # Open-ended to the end: "120," or "120-"
    open_end_match = re.fullmatch(r'(\d+)\s*[-,]', text)
    if open_end_match:
        return int(open_end_match.group(1)), None
    # Open-ended from the start: ",150" or "-150"
    open_start_match = re.fullmatch(r'[-,]\s*(\d+)', text)
    if open_start_match:
        return None, int(open_start_match.group(1))
    # Bare single line number: list only that line
    if re.fullmatch(r'\d+', text):
        n = int(text)
        return n, n
    return None


def _parse_list_command(text: str) -> Optional[ListCommand]:
    match = re.match(r'^LIST(?:\s+(.*))?$', text.strip(), re.IGNORECASE)
    if not match:
        return ListCommand()
    args = (match.group(1) or '').strip()
    if not args:
        return ListCommand()

    mode = 'standard'
    mode_match = re.fullmatch(r'(PRETTY|REFS?)', args, re.IGNORECASE)
    if mode_match:
        mode = mode_match.group(1).lower()
        if mode == 'ref':
            mode = 'refs'
        return ListCommand(mode=mode)

    range_part = args
    mode_token = re.search(r'\b(PRETTY|REFS?)\b', args, re.IGNORECASE)
    if mode_token:
        mode = mode_token.group(1).lower()
        if mode == 'ref':
            mode = 'refs'
        range_part = re.sub(
            r'\b(PRETTY|REFS?)\b',
            '',
            args,
            flags=re.IGNORECASE,
        ).strip()

    if not range_part:
        return ListCommand(mode=mode)

    parsed_range = _parse_list_range(range_part)
    if parsed_range is None:
        return None
    start_line, end_line = parsed_range
    return ListCommand(mode=mode, start_line=start_line, end_line=end_line)


def _parse_save_command(text: str) -> Tuple[Optional[str], str]:
    """Parse SAVE [PRETTY|REFS|NUMBERED] [filename].

    Returns (filename_or_None, mode) where mode is ``standard``, ``pretty``,
    ``refs``, or ``numbered`` (force line numbers even if source was unnumbered).
    """
    stripped = text.strip()
    mode = 'standard'
    mode_match = re.match(
        r'^SAVE\s+(PRETTY|REFS?|NUMBERED|LINES)\b',
        stripped,
        re.IGNORECASE,
    )
    if mode_match:
        token = mode_match.group(1).upper()
        if token.startswith('REF'):
            mode = 'refs'
        elif token in ('NUMBERED', 'LINES'):
            mode = 'numbered'
        else:
            mode = 'pretty'
    if re.fullmatch(
        r'SAVE(?:\s+(?:PRETTY|REFS?|NUMBERED|LINES))?',
        stripped,
        re.IGNORECASE,
    ):
        return None, mode
    match = re.match(
        r'^SAVE(?:\s+(?:PRETTY|REFS?|NUMBERED|LINES))?\s+(.+)$',
        stripped,
        re.IGNORECASE,
    )
    if not match:
        return None, mode
    try:
        filename = _parse_path_arg(match.group(1))
    except ValueError:
        return None, mode
    return filename, mode


def _resolve_save_filename(interp: BASICInterpreter, filename: Optional[str]) -> Optional[str]:
    if filename:
        return filename
    if interp.loaded_filename:
        return interp.loaded_filename
    try:
        prompted = input('Save as: ').strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return None
    if not prompted:
        print('? SAVE filename')
        return None
    return prompted


def _parse_dir_command(text: str) -> Tuple[bool, Optional[str]]:
    match = re.match(r'^DIR(?:\s+(.+))?$', text.strip(), re.IGNORECASE)
    if not match:
        return False, None
    if not match.group(1):
        return True, None
    return True, match.group(1).strip().strip('"\'') or None


def _parse_cd_command(text: str) -> Tuple[bool, Optional[str]]:
    match = re.match(r'^CD(?:\s+(.*))?$', text.strip(), re.IGNORECASE)
    if not match:
        return False, None
    arg = match.group(1)
    if arg is None or not arg.strip():
        return True, None
    try:
        return True, _parse_path_arg(arg)
    except ValueError:
        return False, None


def _parse_edit_command(text: str) -> Optional[int]:
    match = re.match(r'^EDIT(?:\s+(\d+))?$', text.strip(), re.IGNORECASE)
    if not match:
        return None
    if match.group(1):
        return int(match.group(1))
    return -1


_REPL_COMMAND_WORDS = (
    'LIST', 'RUN', 'CONT', 'NEW', 'SAVE', 'LOAD', 'DIR', 'CD', 'AUTO', 'EDIT',
    'RENUMBER', 'REN', 'HELP', 'MATRIX', 'COMPAT', 'DIALECTS', 'DIALECT', 'CASE',
    'EXIT', 'QUIT', 'BYE', 'GOODBYE',
)

# BBC/VAX dotted abbrevs; L.=LIST and LO.=LOAD disambiguate LOAD vs LIST.
_REPL_DOT_ABBREVS: Dict[str, str] = {
    'L': 'LIST',
    'LI': 'LIST',
    'LO': 'LOAD',
    'R': 'RUN',
    'N': 'NEW',
    'SA': 'SAVE',
    'SV': 'SAVE',
    'D': 'DIR',
    'E': 'EDIT',
    'A': 'AUTO',
    'H': 'HELP',
    'HE': 'HELP',
    'MA': 'MATRIX',
    'MAT': 'MATRIX',
    'RE': 'RENUMBER',
    'REN': 'RENUMBER',
}


def _expand_repl_abbrev(text: str) -> str:
    """Expand BBC/VAX-style dotted command abbrevs (L.=LIST, LO.=LOAD, ...)."""
    stripped = text.strip()
    match = re.match(r'^(\S+)(.*)$', stripped, re.DOTALL)
    if not match:
        return text
    word, rest = match.group(1), match.group(2)
    if re.fullmatch(r'\d+', word):
        return text

    upper = word.upper()
    if upper.endswith('.'):
        prefix = upper[:-1]
        if not prefix:
            return text
        expanded = _REPL_DOT_ABBREVS.get(prefix)
        if expanded is None:
            candidates = [cmd for cmd in _REPL_COMMAND_WORDS if cmd.startswith(prefix)]
            if len(candidates) == 1:
                expanded = candidates[0]
        if expanded is None:
            return text
        return expanded + rest

    if upper.isalpha() and len(upper) >= 2:
        candidates = [cmd for cmd in _REPL_COMMAND_WORDS if cmd.startswith(upper)]
        if len(candidates) == 1:
            return candidates[0] + rest
    return text


def _print_dialect_compatibility_matrix() -> None:
    rows: List[Tuple[str, str, str, str, str, str]] = [
        ('Numbered lines', '+', '+', '+', '+', '+'),
        ('Unnumbered lines', '-', '-', '-', '+', '+'),
        ('GOTO / GOSUB / RETURN', '+', '+', '+', '+', '+'),
        ('IF ... GOTO nn', '+', '+', '-', '-', '+'),
        ('IF ... THEN nn (implicit GOTO)', '+', '+', '-', '+', '+'),
        ('ON GOTO / ON GOSUB', '+', '+', '+', '+', '+'),
        ('ON ERROR GOTO/GOSUB / RESUME', '+', '+', '+', '+', '+'),
        ('IF/ENDIF / ELSEIF', '-', '-', '-', '+', '+'),
        ('WHILE / ENDWHILE (SDL)', '-', '-', '-', '+', '+'),
        ('REPEAT / UNTIL', '-', '-', '-', '+', '+'),
        ('EXIT FOR/WHILE/REPEAT (SDL)', '-', '-', '-', '+', '+'),
        ('ON CLOSE QUIT / OFF', '-', '-', '-', '+', '+'),
        ('COLOUR fg,bg (two-arg)', '-', '-', '-', '+', '+'),
        ('INKEY(-256) key scan', '-', '-', '-', '+', '+'),
        ('PROC / DEF PROC / ENDPROC', '-', '-', '-', '+', '+'),
        ('BREAK / CONTINUE (mini ext)', '-', '-', '-', '-', '+'),
        ('INSTR', '-', '-', '-', '+', '+'),
        ('DEF FN one-line', '+', '+', '+', '+', '+'),
        ('DEF FN ... END DEF', '-', '-', '-', '~', '+'),
        ('? shorthand (PRINT)', '+', '+', '+', '+', '+'),
        ('TRUE/FALSE (-1/0)', '+', '+', '+', '+', '+'),
        ('ARG / _argc / CLI args', '-', '-', '-', '-', '+'),
        ('FG$ / BG$ / ANSI colors', '-', '-', '-', '-', '+'),
        ('TIME (centisecond clock)', '+', '+', '+', '+', '+'),
        ('Case-sensitive names (a#A)', '-', '-', '-', '-', '+'),
        ('LIST/SAVE detokenize (_save_case)', '+', '+', '+', '+', '-'),
    ]
    print('=== Dialect compatibility ===')
    print('  mits      = MITS 8K / MS era numbered GOTO (ELIZA.BAS)')
    print('  commodore = Commodore MS BASIC V2 (C64/VIC-20): numbered GOTO, IF GOTO')
    print('  tiny      = Tiny BASIC (1975): numbered, IF THEN stmt only (no line jumps)')
    print('  bbc       = BBC BASIC for SDL 2.0 (EXIT/ENDWHILE); not Acorn RISC OS V')
    print('  mini      = full superset, default (--dialect mini)')
    print()
    print(f'  {"Feature":<28} mits  com tiny  bbc  mini')
    print(f'  {"-" * 28} ----  --- ----  ---  ----')
    for feature, mits, com, tiny, bbc, mini in rows:
        print(f'  {feature:<28} {mits:^4}  {com:^3} {tiny:^4}  {bbc:^3}  {mini:^4}')
    print()
    print('  + = yes   - = rejected in strict dialect   ~ = extension (bbc warns on load)')
    print('  tiny: use GOTO for branches; IF 1 THEN PRINT X ok, IF 1 THEN 100 not ok')
    print('  REPL: --dialect mits|commodore|tiny|bbc|mini   strict: --strict-dialect')
    print('  File: #!bbc  or  1 REM dialect: bbc  at top of .bas (overrides env)')
    print('  REPL: DIALECT [mini|mits|commodore|tiny|bbc]   CASE [on|off|auto]   MATRIX')


def _print_startup_banner() -> None:
    print('=== mini-BASIC ===')
    print('  HELP (menu)   HELP MODES   HELP REPL   HELP FUNCTIONS   MATRIX')


def _parse_dialect_repl_command(text: str) -> Optional[Tuple[Optional[Dialect], Optional[bool]]]:
    match = re.match(r'^DIALECT(?:\s+(.*))?$', text.strip(), re.IGNORECASE)
    if not match:
        return None
    rest = (match.group(1) or '').strip()
    if not rest:
        return None, None
    tokens = rest.split()
    dialect = _normalize_dialect(tokens[0])
    if dialect is None:
        raise ValueError('invalid dialect')
    strict: Optional[bool] = None
    for token in tokens[1:]:
        key = token.lower()
        if key == 'strict':
            strict = True
        elif key in ('loose', 'normal'):
            strict = False
        else:
            raise ValueError('invalid dialect option')
    return dialect, strict


def _parse_case_mode_token(token: str) -> Optional[bool]:
    key = token.strip().lower()
    if key in ('on', '1', 'yes', 'sensitive', 'case'):
        return True
    if key in ('off', '0', 'no', 'fold', 'insensitive'):
        return False
    if key in ('auto', 'default'):
        return None
    raise ValueError('invalid case mode')


def _execute_repl_line(interp: BASICInterpreter, text: str) -> bool:
    """Execute one REPL line. Returns False when the session should end."""
    text = text.rstrip()
    if not text:
        return True
    stripped = text.lstrip()
    if stripped.startswith("'") or re.match(r'^REM\b', stripped, re.IGNORECASE):
        hint = parse_comment_dialect_line(text)
        if hint is not None:
            interp._apply_dialect_hint(hint, announce=True)
        return True
    if text.strip().lower() in _CLI_EXIT_WORDS:
        print('Goodbye!')
        return False

    text = _expand_repl_abbrev(text)
    u = text.upper()
    if u.startswith('LIST'):
        list_cmd = _parse_list_command(text)
        if list_cmd is None:
            print('? LIST error')
        else:
            interp.list_program(list_cmd)
    elif u == 'RUN':
        interp.run()
    elif u == 'CONT':
        interp.cont()
    elif u == 'NEW':
        interp.new()
    elif u.startswith('SAVE'):
        filename, save_mode = _parse_save_command(text)
        resolved = _resolve_save_filename(interp, filename)
        if resolved is None:
            if filename is not None:
                print('? SAVE [PRETTY|REFS|NUMBERED] filename')
        else:
            interp.save(resolved, save_mode)
    elif u.startswith('LOAD'):
        filename = _parse_file_command(text, 'LOAD')
        if filename is None:
            print('? LOAD filename')
        else:
            interp.load(filename)
    elif u.startswith('DIR'):
        ok, pattern = _parse_dir_command(text)
        if not ok:
            print('? DIR [pattern]')
        else:
            interp.list_dir(pattern)
    elif u.startswith('CD'):
        ok, path = _parse_cd_command(text)
        if not ok:
            print('? CD [path]')
        else:
            interp.change_dir(path)
    elif u.startswith('AUTO'):
        try:
            start, step = _parse_auto_command(text)
            interp.auto_entry(start, step)
        except ValueError:
            print('? AUTO [start [,step]]')
    elif u.startswith('EDIT'):
        target = _parse_edit_command(text)
        if target is None:
            print('? EDIT line   (or bare EDIT for usage)')
        elif target == -1:
            # No full-screen BBC editor: usage + LIST (see edit_program).
            interp.edit_program()
        else:
            interp.edit_line(target)
    elif re.match(r'^DIALECT\b', text, re.IGNORECASE):
        try:
            parsed = _parse_dialect_repl_command(text)
            if parsed is None:
                print('? DIALECT error')
                return True
            dialect, strict = parsed
            if dialect is None:
                strict_label = 'on' if interp.config.strict_dialect else 'off'
                print(
                    f'Dialect: {interp.config.dialect}  strict: {strict_label}  '
                    f'case: {interp._case_sensitivity_label()}'
                )
            else:
                if not interp.set_dialect(dialect, strict=strict, announce=True):
                    return True
        except ValueError:
            print('? DIALECT error')
    elif re.match(r'^CASE\b', text, re.IGNORECASE):
        match = re.match(r'^CASE(?:\s+(.*))?$', text.strip(), re.IGNORECASE)
        if not match:
            print('? CASE error')
            return True
        rest = (match.group(1) or '').strip()
        if not rest:
            print(
                f'Case: {interp._case_sensitivity_label()} '
                f'(dialect {interp.config.dialect})'
            )
        else:
            try:
                interp.set_case_sensitivity(_parse_case_mode_token(rest))
            except ValueError:
                print('? CASE error')
    elif u == 'HELP' or u.startswith('HELP '):
        topic = text.split(None, 1)[1] if u.startswith('HELP ') else ''
        _run_help_browser(
            topic,
            print_dialects=_print_dialect_compatibility_matrix,
        )
    elif u in ('MATRIX', 'COMPAT', 'DIALECTS'):
        _print_dialect_compatibility_matrix()
    else:
        renumber_spec = _parse_renumber_command(text)
        if renumber_spec is not None:
            try:
                interp.renumber_program(*renumber_spec)
            except ValueError:
                print('? RENUMBER error')
            return True
        parsed = interp._parse_line_number(text)
        if parsed:
            interp.set_program_line(parsed[0], parsed[1], parsed[2])
        else:
            bare_line = interp._parse_bare_line_number(text)
            if bare_line is not None:
                if bare_line in interp.program:
                    interp.delete_program_line(bare_line)
            elif interp._classify_multiline_def_start(text) is not None:
                interp.def_block_entry(text)
            elif interp.can_execute_immediate(text):
                try:
                    interp.execute_immediate(text)
                except ChainTransfer:
                    # CHAIN from direct mode: the new program was loaded; run it
                    try:
                        interp.run()
                    except Exception:
                        pass  # errors printed inside
            else:
                print('?')
    return True


def _interactive_repl(interp: BASICInterpreter) -> None:
    readline_ok = _configure_repl_readline(
        working_dir=lambda: interp.working_dir,
        expand_abbrev=_expand_repl_abbrev,
        get_readline=_get_readline_module,
    )
    if sys.platform == 'win32' and sys.stdin.isatty() and not readline_ok:
        print(
            'Note: install pyreadline3 for smoother Windows line editing '
            '(pip install -r requirements-repl.txt)'
        )
    repl_history: List[str] = []

    def _pump_pygame_while_idle() -> bool:
        try:
            return interp.pump_display_idle()
        except ProgramExit:
            return False

    def _read_repl_line() -> str:
        idle = _pump_pygame_while_idle if interp._display_enabled() else None
        # Prefer pyreadline3 / GNU readline (requirements-repl.txt) for Unicode
        # and low-latency editing. Custom msvcrt editor only when pygame must
        # pump the window while waiting for keys, or when no readline backend.
        if idle is not None and sys.platform == 'win32' and sys.stdin.isatty():
            try:
                from .repl.windows_input import windows_repl_input

                return windows_repl_input(
                    '> ',
                    working_dir=lambda: interp.working_dir,
                    expand_abbrev=_expand_repl_abbrev,
                    history=repl_history,
                    idle=idle,
                )
            except (ImportError, OSError, ValueError):
                pass
        if idle is not None and not idle():
            raise ProgramExit()
        return input('> ')

    try:
        while True:
            try:
                if not interp.pump_display_idle():
                    print('Goodbye!')
                    break
                text = _read_repl_line()
                if not _execute_repl_line(interp, text):
                    break
            except ProgramExit:
                print('Goodbye!')
                break
            except KeyboardInterrupt:
                print('\nGoodbye!')
                _hard_exit(0)
            except Exception as e:
                print(f'Error: {e}')
    finally:
        interp._shutdown_display(hold=False)
        from mini_basic.display import ensure_no_pygame_leftovers
        ensure_no_pygame_leftovers()
        interp._restore_console()


_REPL_COMMAND_PREFIXES = (
    'LOAD',
    'RUN',
    'NEW',
    'LIST',
    'SAVE',
    'AUTO',
    'EDIT',
    'DIR',
    'CD',
    'DIALECT',
    'HELP',
    'RENUMBER',
    'CONT',
    'BYE',
    'QUIT',
    'EXIT',
)


def _looks_like_repl_command_script(lines: List[str]) -> bool:
    """True when the first substantive line is a mini_basic REPL/meta command."""
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("'") or line.startswith('#'):
            continue
        if re.match(r'^REM\b', line, re.IGNORECASE):
            continue
        upper = line.upper()
        for prefix in _REPL_COMMAND_PREFIXES:
            if upper == prefix or upper.startswith(prefix + ' '):
                return True
        return False
    return False


def _script_file_kind(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == '.bas':
        return 'program'
    if ext in ('.mbs', '.cmd'):
        return 'commands'
    if ext == '.txt':
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                sample = handle.readlines()
        except OSError:
            return 'program'
        return 'commands' if _looks_like_repl_command_script(sample) else 'program'
    return 'program'


def _load_bas_file(interp: BASICInterpreter, path: str, *, announce: bool = True) -> int:
    try:
        resolved = interp.resolve_path(path)
    except ValueError as exc:
        detail = str(exc).strip()
        print(f'File not found: {path}' + (f' ({detail})' if detail else ''))
        return 1
    if not os.path.exists(resolved):
        print(f'File not found: {resolved}')
        return 1
    ok = interp.load(path, announce=announce)
    if not ok or not interp.program:
        return 1
    return 0


def _list_bas_file(
    interp: BASICInterpreter,
    path: str,
    mode: str = 'pretty',
    *,
    announce: bool = False,
) -> int:
    if _load_bas_file(interp, path, announce=announce) != 0:
        return 1
    interp.list_program(ListCommand(mode=mode))
    return 0


def _run_bas_file(interp: BASICInterpreter, path: str) -> int:
    if _load_bas_file(interp, path) != 0:
        return 1
    interp.run()
    # If a runtime error occurred (e.g. unknown statement from BBCSDL-specific code), return non-zero
    if getattr(interp, 'error_line_num', 0):
        return 1
    return 0


def _run_command_script(interp: BASICInterpreter, path: str) -> int:
    try:
        resolved = interp.resolve_path(path)
    except ValueError as exc:
        detail = str(exc).strip()
        print(f'File not found: {path}' + (f' ({detail})' if detail else ''))
        return 1
    if not os.path.exists(resolved):
        print(f'File not found: {resolved}')
        return 1
    try:
        with open(resolved, 'r', encoding='utf-8') as handle:
            lines = handle.readlines()
    except OSError as exc:
        print(f'Load failed: cannot read command script {resolved} ({type(exc).__name__}: {exc})')
        return 1

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("'") or line.startswith('REM '):
            continue
        if line.startswith('#'):
            continue
        if not _execute_repl_line(interp, line):
            break
    return 0


def _normalize_dialect(value: Optional[str]) -> Optional[Dialect]:
    if value is None:
        return None
    key = value.strip().lower()
    if key in ('mini', 'mits', 'bbc', 'commodore', 'tiny'):
        return key  # type: ignore[return-value]
    return None


def _apply_pygame_display_defaults(
    config: InterpreterConfig,
    *,
    gfx_customized: bool = False,
    cols_customized: bool = False,
    rows_customized: bool = False,
    scale_specified: bool = False,
) -> None:
    """Set BBC MODE 8-ish framebuffer and auto scale unless CLI overrode them."""
    mode8 = bbc_mode_spec(8)
    if mode8 is not None:
        if not gfx_customized:
            config.graphics_width = mode8.gfx_width
            config.graphics_height = mode8.gfx_height
        if not cols_customized:
            config.display_cols = mode8.text_cols
        if not rows_customized:
            config.display_rows = mode8.text_rows
    else:
        if not gfx_customized:
            config.graphics_width = 320
            config.graphics_height = 256
        if not cols_customized:
            config.display_cols = 40
        if not rows_customized:
            config.display_rows = 24
    if not scale_specified and not config.display_scale_locked:
        from mini_basic.display import auto_display_scale

        config.display_scale = auto_display_scale(
            graphics_width=config.graphics_width,
            graphics_height=config.graphics_height,
            text_cols=config.display_cols,
            text_rows=config.display_rows,
        )


def _parse_main_args(
    argv: Optional[List[str]] = None,
) -> Tuple[Optional[str], List[str], bool, bool, bool, Optional[str], InterpreterConfig]:
    args = list(argv if argv is not None else sys.argv[1:])
    interactive = False
    quiet = False
    trace = False
    list_mode: Optional[str] = None
    target: Optional[str] = None
    program_args: List[str] = []
    config = InterpreterConfig()
    scale_specified = False
    gfx_customized = False
    cols_customized = False
    rows_customized = False
    env_dialect = _normalize_dialect(
        os.environ.get('MINI_BASIC_DIALECT') or os.environ.get('MINIBASIC_DIALECT')
    )

    if env_dialect is not None:
        config.dialect = env_dialect
    env_slow = os.environ.get('MINIBASIC_SLOW') or os.environ.get('MINI_BASIC_SLOW')
    if env_slow is not None and str(env_slow).strip() != '':
        try:
            config.run_slow_ms = max(0.0, float(env_slow))
        except ValueError:
            pass
    index = 0
    while index < len(args):
        token = args[index]
        if token == '--debug-filter':
            if index + 1 < len(args):
                config.DEBUG = True
                config.DEBUG_FILTER = args[index + 1]
                index += 2
                continue
        if token == '--debug':
            config.DEBUG = True
            index += 1
            continue
        
        if token in ('-i', '--interactive'):
            interactive = True
            index += 1
            continue
        if token in ('-q', '--quiet'):
            quiet = True
            index += 1
            continue
        if token == '--trace':
            trace = True
            index += 1
            continue
        if token in ('-p', '--pretty'):
            list_mode = 'pretty'
            index += 1
            continue
        if token == '--list':
            list_mode = 'standard'
            index += 1
            continue
        if token == '--refs':
            list_mode = 'refs'
            index += 1
            continue
        if token in ('-d', '--dialect'):
            if index + 1 >= len(args):
                print('? --dialect requires mini, mits, commodore, tiny, or bbc')
                raise SystemExit(2)
            dialect = _normalize_dialect(args[index + 1])
            if dialect is None:
                print('? dialect must be mini, mits, commodore, tiny, or bbc')
                raise SystemExit(2)
            config.dialect = dialect
            config.dialect_locked = True
            index += 2
            continue
        if token == '--strict-dialect':
            config.strict_dialect = True
            index += 1
            continue
        if token == '--input-exit':
            config.input_exit_words = True
            index += 1
            continue
        if token == '--pygame':
            config.display = 'pygame'
            config.display_locked = True
            config.hold_display_open = True
            index += 1
            continue
        if token == '--display':
            if index + 1 >= len(args):
                print('? --display requires terminal, pygame, or none')
                raise SystemExit(2)
            backend = args[index + 1].strip().lower()
            if backend not in ('terminal', 'pygame', 'none', 'null'):
                print('? --display must be terminal, pygame, or none')
                raise SystemExit(2)
            config.display = 'none' if backend in ('none', 'null') else backend
            config.display_locked = True
            if config.display == 'pygame':
                config.hold_display_open = True
            index += 2
            continue
        if token == '--fps':
            if index + 1 >= len(args):
                print('? --fps requires a number (0 = unlimited)')
                raise SystemExit(2)
            config.display_fps_limit = max(0, int(args[index + 1]))
            index += 2
            continue
        if token == '--scale':
            if index + 1 >= len(args):
                print('? --scale requires a number')
                raise SystemExit(2)
            config.display_scale = max(1, int(args[index + 1]))
            config.display_scale_locked = True
            config.display_locked = True
            if config.display == 'terminal':
                config.display = 'pygame'
                config.hold_display_open = True
            scale_specified = True
            index += 2
            continue
        if token == '--cols':
            if index + 1 >= len(args):
                print('? --cols requires a number')
                raise SystemExit(2)
            config.display_cols = int(args[index + 1])
            config.display_locked = True
            cols_customized = True
            index += 2
            continue
        if token == '--rows':
            if index + 1 >= len(args):
                print('? --rows requires a number')
                raise SystemExit(2)
            config.display_rows = int(args[index + 1])
            config.display_locked = True
            rows_customized = True
            index += 2
            continue
        if token == '--gfx-width':
            if index + 1 >= len(args):
                print('? --gfx-width requires a number')
                raise SystemExit(2)
            config.graphics_width = int(args[index + 1])
            config.display_locked = True
            gfx_customized = True
            index += 2
            continue
        if token == '--gfx-height':
            if index + 1 >= len(args):
                print('? --gfx-height requires a number')
                raise SystemExit(2)
            config.graphics_height = int(args[index + 1])
            config.display_locked = True
            gfx_customized = True
            index += 2
            continue
        if token == '--no-hold':
            config.hold_display_open = False
            index += 1
            continue
        if token == '--hold':
            config.hold_display_open = True
            index += 1
            continue
        if token == '--slow':
            # --slow  [default 50 ms/line]  or  --slow N  (milliseconds per line)
            ms = 50.0
            if index + 1 < len(args):
                nxt = str(args[index + 1])
                # Only consume a numeric delay — not the program path (foo.bas).
                try:
                    ms = float(nxt)
                except ValueError:
                    pass
                else:
                    if ms < 0:
                        print('? --slow requires a non-negative number (milliseconds per line)')
                        raise SystemExit(2)
                    config.run_slow_ms = float(ms)
                    index += 2
                    continue
            config.run_slow_ms = float(ms)
            index += 1
            continue
        if token == '--tee-terminal':
            config.tee_terminal = True
            index += 1
            continue
        if token in ('-V', '--version'):
            from .version import print_version_report

            print_version_report()
            raise SystemExit(0)
        if token in ('-h', '--help'):
            print('Usage: mini_basic.py [options] file.bas [program args...]')
            print('  file.bas   load and RUN the program')
            print('  file.mbs   run REPL commands (LOAD, RUN, ...)')
            print('  -V, --version  version, implementation status, MINIBASIC_DIR')
            print('  -p, --pretty   load file.bas, LIST PRETTY (structured), exit')
            print('  --list         load file.bas, LIST (standard), exit')
            print('  --refs         load file.bas, LIST REFS (GOTO targets), exit')
            print('  -i, --interactive  stay in REPL after RUN, or after --pretty/--list/--refs')
            print('  -q         suppress startup banner and load messages')
            print('  -d, --dialect mini|mits|commodore|tiny|bbc')
            print('             mini = full superset (default)')
            print('             mits = numbered/GOTO era (ELIZA.BAS)')
            print('             commodore = C64/VIC-20 MS BASIC V2 (IF GOTO, numbered)')
            print('             tiny = Tiny BASIC 1975 (IF THEN stmt only, numbered)')
            print('             bbc  = BBC-style structured (BETH.BAS); GOTO allowed')
            print('  File hint: #!bbc  or  1 REM dialect: bbc  (unless --dialect set)')
            print('  --strict-dialect  treat dialect violations as load errors')
            print('  --input-exit      mini dialect only: bye/quit/exit at INPUT ends RUN')
            print('  --pygame          SDL/pygame window (same as --display pygame)')
            print('  --display pygame|terminal|none')
            print('                    bbc/mini: graphics programs auto-enable pygame when a GUI is available')
            print('                    (text-only Linux/SSH without DISPLAY: stay terminal; use --display pygame to force)')
            print('  --fps N           cap pygame frame rate (0 = unlimited; default 60)')
            print('  --scale N         pixel scale for pygame (exact; default: largest that fits)')
            print('  --cols N --rows N text grid size for pygame')
            print('  --gfx-width N --gfx-height N graphics framebuffer size')
            print('  --hold / --no-hold keep or close pygame window after END')
            print('  --slow [ms]         pause after each BASIC line (default 50 ms); shows graphics frames')
            print('  --tee-terminal      mirror pygame PRINT/INPUT to the terminal')
            print('                      (or set _tee_terminal = 1 in the program)')
            print('  --debug             interpreter debug to stderr + mini_basic.log')
            print('  --debug-filter TAG  only lines containing TAG (HELP DEBUG lists tags)')
            print()
            print('Environment: MINIBASIC_DIR=path   install/launcher tree (see --version)')
            print('             MINI_BASIC_DIALECT=mini|mits|commodore|tiny|bbc')
            print('             MINIBASIC_SLOW=ms    same as --slow (milliseconds per line)')
            print('             MINIBASIC_NO_GRAPHICS=1 or MINIBASIC_DISPLAY=terminal')
            print('             MINI_BASIC_DEBUG=1 / MINI_BASIC_DEBUG_FILTER=TAG')
            print('             (never auto-open pygame; Ctrl+C / ESC in the terminal stops RUN)')
            print()
            print('Program args are available as _argc, ARG$(n), and ARG(n).')
            print()
            print('Examples:')
            print('  mini_basic.py --dialect mits ELIZA.BAS')
            print('  mini_basic.py --dialect bbc BETH.BAS')
            print('  mini_basic.py --pygame examples/mini/sprites_demo.bas')
            print('  mini_basic.py --display pygame --scale 2 examples/mini/bbc_graphics_demo.bas')
            print('  mini_basic.py --pretty --dialect bbc BETH.BAS')
            print('  mini_basic.py --pretty -i BETH.BAS')
            print('  mini_basic.py mandelbrot_color_only.bas 32')
            print('  mini_basic.py beth.mbs')
            print()
            print('REPL: bye/quit/exit at > prompt. INPUT is standard unless --input-exit.')
            raise SystemExit(0)
        if token == '--':
            program_args = args[index + 1:]
            break
        if token.startswith('-'):
            print(f'Unknown option: {token}')
            raise SystemExit()

        if target is None:
            target = token
        else:
            program_args.append(token)
        index += 1
    if config.display == 'pygame':
        _apply_pygame_display_defaults(
            config,
            gfx_customized=gfx_customized,
            cols_customized=cols_customized,
            rows_customized=rows_customized,
            scale_specified=scale_specified,
        )
    return target, program_args, interactive, quiet, trace, list_mode, config


def main(argv: Optional[List[str]] = None) -> int:
    target, program_args, interactive, quiet, trace, list_mode, config = _parse_main_args(argv)
    if target and config.display == 'pygame':
        config.display_caption = os.path.basename(target)
    if not quiet and (target is None or interactive):
        _print_startup_banner()

    from .util.debug import (
        announce_debug,
        reset_announce_for_tests,
        set_active_debug_config,
    )

    set_active_debug_config(config)
    if config.DEBUG:
        # Fresh process always announces once.
        reset_announce_for_tests()
        announce_debug(config)

    interp = BASICInterpreter(config)
    interp.program_args = list(program_args)
    if trace:
        interp.trace_enabled = True

    if list_mode is not None:
        if target is None:
            print('? listing mode requires a .bas file')
            return 2
        if _script_file_kind(target) != 'program':
            print('? listing mode requires a .bas program file')
            return 2
        status = _list_bas_file(
            interp,
            target,
            list_mode,
            announce=not quiet,
        )
        if status != 0:
            if not interactive:
                return status
            # -i: proceed to REPL even on list error (limited usefulness if load failed)
        if not interactive:
            return 0

    if target is not None:
        kind = _script_file_kind(target)
        try:
            status = (
                _run_command_script(interp, target)
                if kind == 'commands'
                else _run_bas_file(interp, target)
            )
        except BasicRuntimeError:
            # Shouldn't normally reach here (run() catches), but be safe
            status = 1
        if status != 0:
            if not interactive:
                return status
            # With -i, stay in interactive mode after a run error so the user
            # can inspect the loaded program (e.g. LIST to see the error line,
            # PRINT ERL, etc.).
        if not interactive:
            if config.display == 'pygame':
                return 0
            return EXIT_HOLD_CONSOLE

    _interactive_repl(interp)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\nGoodbye!')
        _hard_exit(130)

