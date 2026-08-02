"""Small shared utilities with no BASIC semantics."""
from .debug import (
    announce_debug,
    dprint,
    debug_enabled,
    debug_log_path,
    reset_announce_for_tests,
)
from .float_info import (
    FloatPlatformInfo,
    basic_truth,
    discover_machine_epsilon,
    machine_epsilon,
    near_equal,
    near_equal_sig,
    probe_float_platform,
)
from .process import hard_exit
from .session import session_supports_gui, terminal_interrupt_pending

__all__ = [
    'FloatPlatformInfo',
    'announce_debug',
    'basic_truth',
    'debug_enabled',
    'debug_log_path',
    'discover_machine_epsilon',
    'dprint',
    'hard_exit',
    'machine_epsilon',
    'near_equal',
    'near_equal_sig',
    'probe_float_platform',
    'reset_announce_for_tests',
    'session_supports_gui',
    'terminal_interrupt_pending',
]
