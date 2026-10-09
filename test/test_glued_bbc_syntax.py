"""Regression: glued BBC NOTX / A%AND1 / MODE5-style normalize."""
import unittest
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]


class GluedBbcSyntaxTests(unittest.TestCase):
    def test_underscore_array_dim(self):
        """BBCSDL flier uses DIM _BOX / _LINE (leading underscore)."""
        i = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        i.program[10] = "DIM _BOX(4,2):_BOX(1,1)=700:PRINT _BOX(1,1):END"
        buf = StringIO()
        with redirect_stdout(buf), redirect_stderr(StringIO()):
            i.run()
        self.assertIn("700", buf.getvalue())

    def test_notx_unary(self):
        i = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        i.variables["X"] = 5.0
        self.assertEqual(i._eval_numeric("NOTX"), -6.0)

    def test_percent_and_div(self):
        i = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        i.program[10] = "A%=5:PRINT A%AND1;A%DIV2:END"
        buf = StringIO()
        with redirect_stdout(buf), redirect_stderr(StringIO()):
            i.run()
        out = buf.getvalue().replace(" ", "")
        self.assertIn("1", out)
        self.assertIn("2", out)

    def test_percent_mod_space_rhs_clock_style(self):
        """Clock.bas: HOUR24%MOD 12 after int sub → 18MOD 12 must become 18 % 12."""
        i = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        self.assertEqual(i._normalize_operators("18MOD 12").replace(" ", ""), "18%12")
        i.int_variables["HOUR24"] = 18
        self.assertEqual(int(i._eval_numeric("HOUR24%MOD 12")), 6)
        i.program[10] = "HOUR24%=14:HOUR%=HOUR24%MOD 12:PRINT HOUR%:END"
        buf = StringIO()
        with redirect_stdout(buf), redirect_stderr(StringIO()):
            i.run()
        self.assertEqual(buf.getvalue().strip(), "2")

    def test_mode5_normalize(self):
        i = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        self.assertEqual(i._normalize_bbc_dialect_line("MODE5"), "MODE 5")
        self.assertEqual(i._normalize_bbc_dialect_line("GCOL0,135"), "GCOL 0,135")
        self.assertIn("INKEY(1)", i._normalize_bbc_dialect_line("D%=INKEY1"))

    def test_saucer_notx_smoke(self):
        i = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        i.load("test/corpus/bbcsdl/graphics/saucer.txt", announce=False)
        for ln, s in list(i.program.items()):
            if "640" in s:
                i.program[ln] = s.replace("640", "16").replace("512", "16")
            u = s.strip().upper()
            if u.startswith("REPEAT") or u.startswith("UNTIL") or u.startswith("WAIT"):
                i.program[ln] = "END"
        errors = []

        def track(msg, *a, **k):
            t = str(msg)
            if t.startswith("?"):
                errors.append(t)

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch.object(
            i, "_runtime_error", track
        ), patch("time.sleep"):
            i.run()
        self.assertEqual(errors, [], errors)


if __name__ == "__main__":
    unittest.main()
