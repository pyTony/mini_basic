"""Pytest hooks for mini_basic tests.

- Dual error output for captured tests
- Phase regression is cumulative: phase N includes phase 0..N-1
  when the mark expression is the documented form
  ``phaseN`` or ``phaseN and not slow``.
"""
from __future__ import annotations

import os
import re

import pytest

from mini_basic.runtime_parts.core import RuntimeCoreMixin

# CLI helpers without an Interpreter also dual-write when this is set.
os.environ.setdefault('MINI_BASIC_ERRORS_DUAL_STDOUT', '1')
# Dummy SDL driver: pygame can still auto-enable for tests without a real window.
# Do NOT set MINIBASIC_NO_GRAPHICS here — that blocks terminal→pygame auto-upgrade
# (see test_dialect_hint, MODE/GCOL enable paths).
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

_PHASE_REGRESSION = re.compile(
    r'^phase(?P<n>[0-2])(?P<slow>\s+and\s+not\s+slow)?$',
    re.IGNORECASE,
)


def pytest_configure(config: pytest.Config) -> None:
    """Expand ``phaseN`` so regression includes all lower phases.

    Examples (after expansion):
      phase0              -> phase0
      phase1              -> (phase0 or phase1)
      phase1 and not slow -> (phase0 or phase1) and not slow
      phase2 and not slow -> (phase0 or phase1 or phase2) and not slow
    """
    expr = (getattr(config.option, 'markexpr', None) or '').strip()
    if not expr:
        return
    match = _PHASE_REGRESSION.fullmatch(expr)
    if not match:
        return
    n = int(match.group('n'))
    parts = ' or '.join(f'phase{i}' for i in range(n + 1))
    expanded = f'({parts})'
    if match.group('slow'):
        expanded = f'{expanded} and not slow'
    config.option.markexpr = expanded


@pytest.fixture(autouse=True)
def _errors_dual_stdout_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """Turn on ``errors_dual_stdout`` for every BASICInterpreter created in tests."""
    monkeypatch.setenv('MINI_BASIC_ERRORS_DUAL_STDOUT', '1')
    original_init = RuntimeCoreMixin.__init__

    def _init(self, config=None):  # type: ignore[no-untyped-def]
        from mini_basic.config import InterpreterConfig

        if config is None:
            config = InterpreterConfig()
        config.errors_dual_stdout = True
        original_init(self, config)

    monkeypatch.setattr(RuntimeCoreMixin, '__init__', _init)
