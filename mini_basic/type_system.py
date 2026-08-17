"""Shared types, exceptions, and runtime data structures.

This module has no interpreter logic — only types used across the runtime,
editor, and I/O layers.

Key types
---------
- ``VarKind`` — float / int / str variable kinds
- ``FileChannel``, ``FieldBuffer`` — sequential and random file I/O state
- ``UserFunction``, ``UserProcedure`` — DEF FN / PROC metadata
- ``LoopFrame``, ``IfFrame``, ``IfBlockLayout`` — structured control flow
- Exceptions: ``ProgramExit``, ``FnReturn``, ``ProcReturn``, ``BasicRuntimeError``
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple

VarKind = Literal['float', 'int', 'str']
"""Variable kind for scalars, arrays, and DEF FN parameters."""

Dialect = Literal['mini', 'mits', 'bbc', 'commodore', 'tiny']
"""Language dialect: mini, MITS, BBC, Commodore MS BASIC V2, or Tiny BASIC (1975)."""

ArrayStorage = Tuple[Tuple[int, ...], int, list]
"""Array backing store: (dimension bounds, lower bound, flat data list)."""


class ProgramExit(BaseException):
    """Stop a running BASIC program (typed exit word or EOF/Ctrl+C at INPUT)."""


class ProgramStop(BaseException):
    """STOP / TRACE STEP Escape: unwind PROC/FN back to command mode."""


class FnReturn(BaseException):
    """Return from a multi-line DEF FN body (= expression)."""

    def __init__(self, value: object):
        self.value = value
        super().__init__()


class ProcReturn(BaseException):
    """Return from a PROC body (ENDPROC)."""


class BasicRuntimeError(BaseException):
    """Runtime error while ON ERROR GOTO/GOSUB trap is active."""


class ChainTransfer(BaseException):
    """CHAIN loaded a new program; restart the run loop from line 0."""


@dataclass
class FieldBuffer:
    """In-memory record buffer for MBASIC random file FIELD/GET/PUT."""

    buffer: bytearray
    fields: Dict[str, Tuple[int, int]]
    current_record: int = 0


@dataclass
class FileChannel:
    """One open file channel (#n): text sequential or binary random (mode ``R``)."""

    handle: object
    mode: str
    print_column: int = 0
    filename: str = ''
    eof: bool = False


@dataclass
class DataItem:
    """Single literal from a DATA statement."""

    kind: VarKind
    value: object


@dataclass
class UserFunction:
    """DEF FN definition (single-line or multi-line body)."""

    name: str
    return_kind: VarKind
    params: Tuple[Tuple[str, VarKind], ...]
    array_params: Tuple[str, ...] = ()
    body: str = ''
    multiline: bool = False
    body_start: int = 0
    body_end: int = 0
    header_line: int = 0


@dataclass
class UserProcedure:
    """DEF PROC ... ENDPROC definition."""

    name: str
    params: Tuple[Tuple[str, VarKind], ...]
    array_params: Tuple[str, ...] = ()
    return_params: Tuple[str, ...] = ()
    body_start: int = 0
    body_end: int = 0
    # Same-line body after DEF PROCname(...): e.g. "IF A=0 ENDPROC" (Towers of Hanoi).
    header_stmt: str = ''


@dataclass
class ListCommand:
    """Arguments parsed from a LIST / LIST PRETTY / LIST REFS command."""

    mode: str = 'standard'
    start_line: Optional[int] = None
    end_line: Optional[int] = None


class IfBlockLayout:
    """Precomputed branch targets for IF / ELSEIF / ELSE / ENDIF."""

    def __init__(
        self,
        branch_starts: List[int],
        branch_conds: List[Optional[str]],
        endif_line: int,
        exit_line: int,
    ):
        self.branch_starts = branch_starts
        self.branch_conds = branch_conds
        self.endif_line = endif_line
        self.exit_line = exit_line


class IfFrame:
    """Runtime stack entry while executing an IF block."""

    def __init__(self, layout: IfBlockLayout):
        self.layout = layout
        self.exit_line = layout.exit_line
        self.branch_taken = False


class CaseBlockLayout:
    """Precomputed branch targets for CASE / WHEN / OTHERWISE / ENDCASE."""

    def __init__(
        self,
        case_expr: Optional[str],
        branch_starts: List[int],
        branch_specs: List[str],
        branch_inline: List[Optional[str]],
        otherwise_index: Optional[int],
        endcase_line: int,
        exit_line: int,
    ):
        self.case_expr = case_expr
        self.branch_starts = branch_starts
        self.branch_specs = branch_specs
        self.branch_inline = branch_inline
        self.otherwise_index = otherwise_index
        self.endcase_line = endcase_line
        self.exit_line = exit_line


class CaseFrame:
    """Runtime stack entry while executing a CASE block."""

    def __init__(self, layout: CaseBlockLayout, *, case_value: object):
        self.layout = layout
        self.exit_line = layout.exit_line
        self.case_value = case_value
        self.branch_index: Optional[int] = None
        self.branch_finished = False


class LoopFrame:
    """Runtime stack entry for FOR, WHILE, or REPEAT loops."""

    def __init__(
        self,
        kind: str,
        body_line: int,
        exit_line: int,
        continue_line: int,
        loop_var: str = '',
        end: float = 0.0,
        step: float = 1.0,
        is_int: bool = False,
        condition: str = '',
        while_line: int = 0,
        repeat_line: int = 0,
        until_condition: str = '',
        label: str = '',
        inline: bool = False,
        for_line: int = 0,
        body_stmt: int = 0,
        next_stmt: int = 0,
    ):
        self.kind = kind
        self.body_line = body_line
        self.exit_line = exit_line
        self.continue_line = continue_line
        self.loop_var = loop_var
        self.end = end
        self.step = step
        self.is_int = is_int
        self.condition = condition
        self.while_line = while_line
        self.repeat_line = repeat_line
        self.until_condition = until_condition
        self.label = label
        self.inline = inline
        self.for_line = for_line
        self.body_stmt = body_stmt
        self.next_stmt = next_stmt
