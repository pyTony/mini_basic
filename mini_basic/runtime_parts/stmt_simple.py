"""Simple independent statement handlers (dict dispatch).

These statements do not participate in structured control-flow matching
(IF/ENDIF, FOR/NEXT, WHILE/WEND, DEF body layout, CASE/WHEN). They are
looked up by command name after ``_parse_command`` in ``_execute_statement``.

Structured / multi-word forms (END DEF, ON ERROR, IF … THEN, …) stay in
``execution.py`` as explicit branches.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from ..type_system import BasicRuntimeError, ProgramExit

# Handler return: None = continue line, -1 = stop program, int = jump target.
SimpleHandler = Callable[..., Optional[int]]


def _h_rem(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    return None


def _h_install(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    # BBCSDL library load — stub (PROCs/FNs error if missing).
    return None


def _h_data(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    return None


def _h_off(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    return None


def _h_cls(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    interp._clear_screen()
    return None


def _h_clg(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    if not interp._graphics_plot_enabled():
        return None
    interp._ensure_display()
    if interp._display_enabled():
        interp._display.clear_graphics()
        interp._sync_graphics()
    return None


def _h_stop(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    interp._save_stop_position(line_num, stmt_index, stmt_count, line_nums)
    print(f'Break in {line_num}')
    return -1


def _h_oscli(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    try:
        interp._execute_oscli(rest)
    except Exception as exc:
        interp._runtime_error(
            interp._error_message('? OSCLI error', exc),
            line_num,
            stmt_index,
            stmt_count=stmt_count,
            statement=statement,
        )
    return None


def _h_wait(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    try:
        interp._execute_wait(
            rest,
            line_num,
            stmt_index,
            stmt_count=stmt_count,
            statement=statement,
        )
    except (KeyboardInterrupt, ProgramExit):
        raise
    return None


def _h_sound(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    interp._execute_sound(
        rest,
        line_num,
        stmt_index,
        stmt_count=stmt_count,
        statement=statement,
    )
    return None


def _h_envelope(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    """BBC ENVELOPE — accepted no-op (no audio engine; welcome.bbc must not error)."""
    # Parse args so RND() side effects still run if present.
    try:
        if rest.strip():
            for part in interp._split_args(rest.strip()):
                try:
                    interp._eval_numeric(part)
                except Exception:
                    pass
    except Exception:
        pass
    return None


def _h_trace(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    try:
        interp._configure_trace(rest)
    except Exception as exc:
        interp._runtime_error(
            interp._error_message('? TRACE error', exc),
            line_num,
            stmt_index,
            stmt_count=stmt_count,
            statement=statement,
        )
    return None


def _h_lvar(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    if rest.strip():
        interp._runtime_error(
            '? LVAR error',
            line_num,
            stmt_index,
            stmt_count=stmt_count,
            statement=statement,
        )
        return None
    try:
        interp._list_variables()
    except Exception as exc:
        interp._runtime_error(
            interp._error_message('? LVAR error', exc),
            line_num,
            stmt_index,
            stmt_count=stmt_count,
            statement=statement,
        )
    return None


def _h_width(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    try:
        width = int(interp._eval_numeric(rest.strip()))
        if width <= 0:
            width = 10
        interp.print_field_width = width
        interp.bbc_at_percent = (interp.bbc_at_percent & 0xFF00) | (width & 0xFF)
    except Exception:
        interp._runtime_error(
            '? WIDTH error',
            line_num,
            stmt_index,
            stmt_count=stmt_count,
            statement=statement,
        )
    return None


def _h_mouse(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    """BBC ``MOUSE x,y,b`` read, or ``MOUSE ON [n]`` / ``MOUSE OFF`` pointer control."""
    try:
        text = rest.strip()
        up = text.upper()
        # MOUSE ON [pointer] / MOUSE OFF — enable pointer (no-op without GUI is fine).
        if up == 'OFF' or up.startswith('OFF ') or up == 'ON' or up.startswith('ON'):
            # Optional: remember pointer style for displays that support it.
            if up == 'OFF' or up.startswith('OFF'):
                setattr(interp, '_mouse_pointer_on', False)
            else:
                setattr(interp, '_mouse_pointer_on', True)
                # MOUSE ON 3 → pointer shape 3 (ignored on terminal/dummy).
                parts = text.split(None, 1)
                if len(parts) > 1:
                    try:
                        setattr(
                            interp,
                            '_mouse_pointer_shape',
                            int(interp._eval_numeric(parts[1].strip())),
                        )
                    except Exception:
                        setattr(interp, '_mouse_pointer_shape', 0)
            display = getattr(interp, '_display', None)
            if display is not None:
                setter = getattr(display, 'set_mouse_visible', None)
                if callable(setter):
                    setter(bool(getattr(interp, '_mouse_pointer_on', True)))
            return None
        args = interp._split_args(text)
        if len(args) != 3:
            raise ValueError('MOUSE needs three variables (or ON/OFF)')
        interp._update_mouse_from_display()
        values = [interp._mouse_x, interp._mouse_y, interp._mouse_buttons]
        for token, value in zip(args, values):
            interp._write_lvalue(interp._read_lvalue(token), value)
    except Exception:
        interp._runtime_error(
            '? MOUSE error',
            line_num,
            stmt_index,
            stmt_count=stmt_count,
            statement=statement,
        )
    return None


def _h_kill(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    try:
        interp._kill_file(rest)
    except BasicRuntimeError:
        raise
    except Exception as exc:
        interp._runtime_error(
            interp._error_message('? KILL error', exc),
            line_num,
            stmt_index,
            stmt_count=stmt_count,
            statement=statement,
        )
    return None


def _h_erase(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    try:
        interp._erase_arrays(rest)
    except BasicRuntimeError:
        raise
    except Exception as exc:
        interp._runtime_error(
            interp._error_message('? ERASE error', exc),
            line_num,
            stmt_index,
            stmt_count=stmt_count,
            statement=statement,
        )
    return None


def _h_quit(
    interp: Any,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[int]:
    raise ProgramExit()


# Command name (as returned by _parse_command) → handler.
SIMPLE_STMT_HANDLERS: Dict[str, SimpleHandler] = {
    'REM': _h_rem,
    'INSTALL': _h_install,
    'DATA': _h_data,
    'OFF': _h_off,
    'CLS': _h_cls,
    'CLG': _h_clg,
    'STOP': _h_stop,
    'OSCLI': _h_oscli,
    'WAIT': _h_wait,
    'SOUND': _h_sound,
    'ENVELOPE': _h_envelope,
    'TRACE': _h_trace,
    'LVAR': _h_lvar,
    'WIDTH': _h_width,
    'MOUSE': _h_mouse,
    'KILL': _h_kill,
    'ERASE': _h_erase,
    'QUIT': _h_quit,
    'BYE': _h_quit,
    'GOODBYE': _h_quit,
}


def dispatch_simple_stmt(
    interp: Any,
    cmd: str,
    rest: str,
    *,
    line_num: int,
    stmt_index: int,
    stmt_count: int,
    statement: str,
    line_nums: List[int],
) -> Optional[Optional[int]]:
    """Run a simple handler if ``cmd`` is registered.

    Returns:
      * the handler's result (``None`` / ``-1`` / jump line) when dispatched
      * the sentinel ``MISSING`` when ``cmd`` is not a simple statement
        (caller continues the big branch ladder)
    """
    handler = SIMPLE_STMT_HANDLERS.get(cmd)
    if handler is None:
        return MISSING
    return handler(
        interp,
        rest,
        line_num=line_num,
        stmt_index=stmt_index,
        stmt_count=stmt_count,
        statement=statement,
        line_nums=line_nums,
    )


class _MissingType:
    __slots__ = ()

    def __repr__(self) -> str:
        return 'MISSING'


MISSING = _MissingType()
