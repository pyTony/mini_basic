"""(name) labels are no longer BBC-only.

Tony (2026-10-26): prefer (name) over "name:" everywhere, since ":" is
also the statement separator -- a label spelled "name:" can collide with
it (see _split_colon_statements' heuristic for keeping that colon from
being read as a separator, which only covers the common case). (name) has
no such ambiguity, so _extract_label_prefix now accepts it in every
dialect, and _labelize_numeric_jump_targets (used by the editor's Strip
Line Numbers / SAVE PRETTY) always emits it, not just for dialect='bbc'.
"""
from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]

SOURCE = (
    '10 GOSUB sub\n20 GOTO done\n30 PRINT "skipped"\n'
    '40 (sub) PRINT "in sub" : RETURN\n50 (done) PRINT "done"\n'
)


class ParenLabelsAllDialectsTests(unittest.TestCase):
    def test_paren_labels_jump_in_mini_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', dialect_locked=True, display='none', display_locked=True))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'p.bas')
            with open(path, 'w') as handle:
                handle.write(SOURCE)
            out = io.StringIO()
            with redirect_stdout(out):
                interp.load(path, announce=False)
                interp.run()
        self.assertEqual(out.getvalue().split(), ['in', 'sub', 'done'])

    def test_labelize_numeric_jump_targets_emits_parens_in_mini_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', dialect_locked=True, display='none', display_locked=True))
        interp.program = {
            10: 'PRINT "a"',
            20: 'GOTO 40',
            30: 'PRINT "skip"',
            40: 'PRINT "b"',
        }
        interp._rebuild_labels()
        interp._labelize_numeric_jump_targets()
        self.assertEqual(interp.program[20], 'GOTO L40')
        self.assertEqual(interp.program[40], '(L40) PRINT "b"')
        self.assertNotIn('L40:', interp.program[40])
