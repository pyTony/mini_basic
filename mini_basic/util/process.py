"""Process-level helpers for the CLI and interpreter."""
from __future__ import annotations

import os
import sys


def hard_exit(code: int = 0) -> None:
    """Exit immediately without Python shutdown hooks.

    Used after Ctrl+C in the REPL so Windows ``cmd.exe`` does not prompt
    "Terminate batch job (Y/N)?".
    """
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)


__all__ = ['hard_exit']
