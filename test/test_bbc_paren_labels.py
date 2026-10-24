"""BBC BASIC for SDL style labels: (name) defines, GOTO/GOSUB/THEN (name) jumps."""
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
    '10 GOSUB (sub)\n20 GOTO (done)\n30 PRINT "skipped"\n'
    '40 (sub) PRINT "in sub" : RETURN\n50 (done) PRINT "done"\n'
    '60 IF 1 THEN (last)\n70 PRINT "no"\n80 (last) END\n'
)


class BbcParenLabelTests(unittest.TestCase):
    def test_paren_labels_jump(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none', display_locked=True))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'p.bas')
            with open(path, 'w') as handle:
                handle.write(SOURCE)
            out = io.StringIO()
            with redirect_stdout(out):
                interp.load(path, announce=False)
                interp.run()
        self.assertEqual(out.getvalue().split(), ['in', 'sub', 'done'])
