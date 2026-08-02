"""Interpreter configuration and system-variable metadata.

``InterpreterConfig`` is passed to ``BASICInterpreter(config=...)`` or mutated
via ``interp.config``. Program-visible system variables (``_argc``, ``_erl``,
``_optimization_level``, etc.) are described in ``SYSTEM_VAR_SPEC`` and
resolved at runtime by the interpreter.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .type_system import Dialect


@dataclass
class InterpreterConfig:
    """Runtime settings for PRINT buffering, optimization, dialect, and display."""

    print_line_buffering: bool = False
    print_file_echo: bool = False
    optimization_level: int = 2
    dialect: Dialect = 'mini'
    strict_dialect: bool = False
    dialect_locked: bool = False
    """When True, LOAD shebang hints do not change dialect (CLI --dialect)."""
    identifiers_case_sensitive: Optional[bool] = None
    """None = dialect default (mini on; mits/commodore/tiny/bbc fold names)."""
    display: str = 'terminal'
    display_locked: bool = False
    """When True, CLI or tests fixed the backend; do not auto-enable pygame on LOAD."""
    display_scale: int = 2
    display_scale_locked: bool = False
    """When True, --scale was set on the CLI; do not auto-shrink below it."""
    display_cols: int = 80
    display_rows: int = 30
    graphics_width: int = 320
    graphics_height: int = 256
    display_caption: str = 'mini_basic'
    display_fps_limit: int = 60
    """Pygame present() rate cap; 0 = unlimited (benchmark / fast machines)."""
    hold_display_open: bool = False
    tee_terminal: bool = False
    """Mirror pygame PRINT/INPUT to the terminal when True."""
    run_slow_ms: float = 0.0
    """If > 0, sleep this many milliseconds after each BASIC line (CLI --slow).

    Forces a display present first so graphics (e.g. welcome invert zaps) are
    visible between lines. 0 = full speed.
    """
    input_exit_words: bool = False
    """If True, INPUT treats bye/quit/exit/q as ProgramExit (mini dialect extension)."""
    bigint_enabled: bool = True
    """If True, % integer variables use arbitrary-precision ints; else IEEE float."""
    DEBUG: bool = False
    DEBUG_FILTER: str = ""
    errors_dual_stdout: bool = False
    """If True, diagnostics (? errors / warnings) also go to stdout.

    Always written to stderr so shells can redirect with ``2>err.txt``.
    Tests enable dual so ``redirect_stdout`` / ``_program_stdout`` still see
    the same messages without capturing stderr separately.
    """

    def __post_init__(self) -> None:
        if self.optimization_level < 0:
            self.optimization_level = 0
        elif self.optimization_level > 2:
            self.optimization_level = 2
        if self.dialect not in ('mini', 'mits', 'bbc', 'commodore', 'tiny'):
            self.dialect = 'mini'

    @property
    def use_run_caches(self) -> bool:
        """Level >= 1: cache parsed statements and loop match tables per RUN."""
        return self.optimization_level >= 1

    @property
    def use_compiled_exprs(self) -> bool:
        """Level >= 2: compile pure arithmetic via Python compile()."""
        return self.optimization_level >= 2


DEFAULT_CONFIG = InterpreterConfig()

SYSTEM_VAR_SPEC: Dict[str, Dict[str, object]] = {
    '_print_line_buffering': {
        'target': 'config',
        'attr': 'print_line_buffering',
        'kind': 'bool',
        'min': 0,
        'max': 1,
    },
    '_print_file_echo': {
        'target': 'config',
        'attr': 'print_file_echo',
        'kind': 'bool',
        'min': 0,
        'max': 1,
    },
    '_tee_terminal': {
        'target': 'config',
        'attr': 'tee_terminal',
        'kind': 'bool',
        'min': 0,
        'max': 1,
    },
    '_slow': {
        'target': 'config',
        'attr': 'run_slow_ms',
        'kind': 'float',
        'min': 0,
        'max': 60000,
    },
    '_optimization_level': {
        'target': 'config',
        'attr': 'optimization_level',
        'kind': 'int',
        'min': 0,
        'max': 2,
    },
    '_print_field_width': {
        'target': 'interpreter',
        'attr': 'print_field_width',
        'kind': 'int',
        'min': 1,
        'max': 255,
    },
    '_cols': {
        'target': 'config',
        'attr': 'display_cols',
        'kind': 'int',
        'min': 1,
        'max': 255,
        'readonly': True,
    },
    '_rows': {
        'target': 'config',
        'attr': 'display_rows',
        'kind': 'int',
        'min': 1,
        'max': 255,
        'readonly': True,
    },
    '_argc': {
        'target': 'interpreter',
        'attr': 'program_arg_count',
        'kind': 'int',
        'min': 0,
        'max': 9999,
        'readonly': True,
    },
    '_erl': {
        'target': 'interpreter',
        'attr': 'error_line_num',
        'kind': 'int',
        'min': 0,
        'max': 999999,
        'readonly': True,
    },
    '_epsilon': {
        'target': 'interpreter',
        'attr': 'machine_epsilon',
        'kind': 'float',
        'min': 0,
        'max': 1,
        'readonly': True,
    },
    '_float_digits': {
        'target': 'interpreter',
        'attr': 'float_decimal_digits',
        'kind': 'int',
        'min': 0,
        'max': 99,
        'readonly': True,
    },
    '_float_mantissa': {
        'target': 'interpreter',
        'attr': 'float_mantissa_digits',
        'kind': 'int',
        'min': 0,
        'max': 256,
        'readonly': True,
    },
    '_float_radix': {
        'target': 'interpreter',
        'attr': 'float_radix',
        'kind': 'int',
        'min': 0,
        'max': 16,
        'readonly': True,
    },
    '_ieee754': {
        'target': 'interpreter',
        'attr': 'ieee754_binary64',
        'kind': 'int',
        'min': 0,
        'max': 1,
        'readonly': True,
    },
    '_save_case': {
        'target': 'interpreter',
        'attr': 'save_case',
        'kind': 'int',
        'min': 0,
        'max': 1,
        'readonly': False,
    },
    '_bigint': {
        'target': 'config',
        'attr': 'bigint_enabled',
        'kind': 'bool',
        'min': 0,
        'max': 1,
    },
    '_case_sensitive': {
        'target': 'config',
        'attr': 'identifiers_case_sensitive',
        'kind': 'int',
        'min': 0,
        'max': 2,
    },
}
