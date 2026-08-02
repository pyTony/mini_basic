"""Regression: --debug / dprint is usable across modular mixins."""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from mini_basic import BASICInterpreter, InterpreterConfig
from mini_basic.util.debug import (
    announce_debug,
    dprint,
    reset_announce_for_tests,
)


class TestDprintCore(unittest.TestCase):
    def setUp(self) -> None:
        reset_announce_for_tests()

    def test_dprint_on_core_mixin_not_io_only(self):
        cfg = InterpreterConfig(DEBUG=True, display='none', display_locked=True)
        interp = BASICInterpreter(cfg)
        self.assertTrue(callable(getattr(interp, 'dprint', None)))
        # Method resolution should use Core (works even if IoMixin lacks dprint)
        self.assertEqual(interp.dprint.__func__.__qualname__, 'RuntimeCoreMixin.dprint')

    def test_dprint_writes_stderr_when_debug(self):
        cfg = InterpreterConfig(DEBUG=True, display='none')
        err = io.StringIO()
        with patch('sys.stderr', err):
            dprint(cfg, 'HELLO', 42)
        text = err.getvalue()
        self.assertIn('HELLO', text)
        self.assertIn('42', text)
        self.assertIn('[DEBUG] enabled', text)

    def test_dprint_silent_when_debug_off(self):
        cfg = InterpreterConfig(DEBUG=False, display='none')
        err = io.StringIO()
        with patch('sys.stderr', err):
            dprint(cfg, 'NOPE')
        self.assertEqual(err.getvalue(), '')

    def test_debug_filter(self):
        cfg = InterpreterConfig(DEBUG=True, DEBUG_FILTER='MOVE', display='none')
        err = io.StringIO()
        with patch('sys.stderr', err):
            dprint(cfg, 'EXEC skip')
            dprint(cfg, 'MOVE args')
        text = err.getvalue()
        self.assertNotIn('EXEC skip', text)
        self.assertIn('MOVE args', text)

    def test_cli_debug_flag_sets_config(self):
        from mini_basic.runtime import _parse_main_args

        _t, _a, _i, _q, _tr, _lm, config = _parse_main_args(
            ['--debug', '--dialect', 'bbc', 'x.bas']
        )
        self.assertTrue(config.DEBUG)


class TestVduBangNotEatenByIntVar(unittest.TestCase):
    """@vdu%!220 must not become @0!220 via int-var ``vdu%`` match."""

    def test_move_with_vdu_offset_and_width(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        buf = io.StringIO()
        err = io.StringIO()
        lines = [
            'MODE 8',
            'Cx%=640:Cy%=512:Rad=300:Depth=128:prev=0:this=1.5',
            'MOVE Cx%+Rad/2*COS(prev+this/2)-WIDTH("One")/2, '
            'Cy%+Rad/4*SIN(prev+this/2)+@vdu%!220+Depth/2',
            'PRINT "ok"',
            'END',
        ]
        with redirect_stdout(buf), redirect_stderr(err):
            for i, line in enumerate(lines, 1):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue() + err.getvalue()
        self.assertNotIn('MOVE error', out)
        self.assertIn('ok', out)


if __name__ == '__main__':
    unittest.main()
