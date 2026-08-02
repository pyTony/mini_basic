"""mini-BASIC interpreter package.

The interpreter runtime is a mixin composition: ``runtime.py`` (facade + CLI)
plus ``runtime_parts/*``. Shared types, config, expr patterns, and PRINT USING
are in sibling submodules. See ``README.md`` for layout.

Quick imports::

    from mini_basic import BASICInterpreter, main
    from .config import InterpreterConfig, DEFAULT_CONFIG
    from .types import VarKind, ProgramExit, FileChannel
    from .format import UsingFormatter
    from .expr import CompiledExpr, patterns
"""
from .config import DEFAULT_CONFIG, InterpreterConfig, SYSTEM_VAR_SPEC
from .constants import EXIT_HOLD_CONSOLE
from .expr import CompiledExpr, int_slot, patterns
from .format import UsingFormatter
from .runtime import (
    BASICInterpreter,
    _execute_repl_line,
    _expand_repl_abbrev,
    _get_readline_module,
    _interactive_repl,
    _parse_list_command,
    _parse_renumber_command,
    _print_dialect_compatibility_matrix,
    _run_command_script,
    _script_file_kind,
    _prompt_editing_input,
    _resolve_save_filename,
    _windows_apply_arrow,
    _windows_arrow_action,
    _windows_editing_input,
    main,
)
from .type_system import (
    ArrayStorage,
    BasicRuntimeError,
    DataItem,
    Dialect,
    FieldBuffer,
    FileChannel,
    FnReturn,
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
from .util import hard_exit
from .version import __version__, format_version_report, print_version_report

__all__ = [
    '__version__',
    'ArrayStorage',
    'BASICInterpreter',
    'BasicRuntimeError',
    'CompiledExpr',
    'DEFAULT_CONFIG',
    'DataItem',
    'Dialect',
    'EXIT_HOLD_CONSOLE',
    'FieldBuffer',
    'FileChannel',
    'FnReturn',
    'IfBlockLayout',
    'IfFrame',
    'InterpreterConfig',
    'ListCommand',
    'LoopFrame',
    'ProcReturn',
    'ProgramExit',
    'SYSTEM_VAR_SPEC',
    'UserFunction',
    'UserProcedure',
    'UsingFormatter',
    'VarKind',
    'format_version_report',
    'print_version_report',
    '_execute_repl_line',
    '_expand_repl_abbrev',
    '_get_readline_module',
    '_interactive_repl',
    '_parse_list_command',
    '_parse_renumber_command',
    '_print_dialect_compatibility_matrix',
    '_prompt_editing_input',
    '_run_command_script',
    '_script_file_kind',
    '_resolve_save_filename',
    '_windows_apply_arrow',
    '_windows_arrow_action',
    '_windows_editing_input',
    'hard_exit',
    'int_slot',
    'main',
    'patterns',
]
