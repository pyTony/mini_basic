"""Compositional, generative tests for complex BBC BASIC programs.

Emphasizes deep nesting (4+ levels of FOR/IF + DEF FN/PROC + arrays +
expressions + calls) and property-based invariants rather than exact
output matching. Designed to be non-stuck (short bounded loops, no
infinite REPEATs, use of display='none' where appropriate).
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

# Phase 1 non-graphics foundation tests (deep nesting + PROC + file I/O composition).
# Preferred filter: pytest -m phase1
pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig
from mini_basic.constants import EXPR_RESERVED_WORDS, NUMERIC_BUILTIN_FUNCS


# --- Strategies for BBC BASIC fragments ---

# Combine runtime reserved words + builtins that can appear as bare names or calls
# (case-insensitive in practice, but we generate lowercase)
_BUILTIN_EXCLUSIONS = {
    w.lower() for w in EXPR_RESERVED_WORDS
} | {
    w.lower() for w in NUMERIC_BUILTIN_FUNCS
}
# Also exclude common BBC keywords and file funcs that can cause parser issues when used as vars
_ADDITIONAL_EXCLUSIONS = {
    "for", "to", "step", "if", "then", "else", "next", "endif",
    "def", "proc", "fn", "end", "dim", "local", "print", "data", "read",
    "while", "wend", "repeat", "until", "exit",
    "tab", "spc", "using", "bget", "bput",
}

safe_var = st.from_regex(r"[a-z][a-z0-9_]*", fullmatch=True).filter(
    lambda s: s not in _BUILTIN_EXCLUSIONS | _ADDITIONAL_EXCLUSIONS
    and not any(s.startswith(b) for b in ("pi", "sin", "cos", "tan", "atn", "sqr", "log", "exp", "int", "abs", "sgn", "rnd", "val", "str", "chr", "asc", "len", "pos", "vpos", "sum", "tab", "spc", "eof", "lof", "ptr", "ext", "err", "erl"))
)

small_int = st.integers(min_value=1, max_value=3)  # Phase 1: keep very small to stay non-stuck and fast
small_depth = st.integers(min_value=1, max_value=2)


@st.composite
def nested_control_expr_array(draw):
    """Generate a program with 4-5 levels of nesting (FOR + IF), DEF FN,
    array access/substitution, simple DATA/READ mix, and PRINT. Bounded.
    Produces valid-ish BBC that exercises core non-graphics paths.
    """
    depth = draw(small_depth) + 1  # small for phase 1 speed/non-stuck (2-3 levels)
    v = draw(safe_var)
    a = draw(safe_var)
    base = draw(small_int)

    lines = [
        "DEF FNdbl(n%)=2*n%",
        f"DIM {a}(20)",
        f"{a}(0)={base}",
        "DATA 10,20,30",
        "READ d1%,d2%",
    ]

    indent = ""
    for d in range(depth):
        lines.append(f"{indent}FOR i{d}% = 1 TO 2")  # hard bound for non-stuck
        indent += "  "
        lines.append(f"{indent}IF i{d}% > 1 THEN")
        indent += "  "
        lines.append(f"{indent}{a}(i{d}%) = FNdbl({a}(i{d}%-1)) + d1%")
        lines.append(f"{indent}ENDIF")

    for d in range(depth - 1, -1, -1):
        indent = "  " * d
        lines.append(f"{indent}NEXT")

    lines.append(f"PRINT {a}(2); d2%")

    return "\n".join(lines)


class TestCompositionalNesting(unittest.TestCase):
    @given(prog=nested_control_expr_array())
    @settings(
        max_examples=5,  # Phase 1 dev: keep small for speed/non-stuck; raise for full runs
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_nested_for_if_fn_array_runs_without_runtime_error(self, prog: str):
        interp = BASICInterpreter(
            InterpreterConfig(dialect="mini", display="none", optimization_level=2)
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            # Fresh interpreter; no need for NEW (NEW is primarily a REPL command)
            for i, line in enumerate(prog.splitlines(), start=10):
                interp.set_program_line(i * 10, line)
            interp.run()

        out = buf.getvalue()
        # Strong invariant for generative test: no "?" error lines
        self.assertNotIn("?", out, f"Runtime error in generated program:\n{prog}\n\nOutput:\n{out}")

        # Additional invariant: the program should have produced some numeric output
        # (the PRINT of the array element)
        self.assertRegex(out.strip(), r'\d+', "Expected numeric output from PRINT")


@st.composite
def proc_with_local_array(draw):
    """PROC with LOCAL array, called from nested loop, with string too for composition."""
    n = draw(small_depth)
    p = draw(safe_var)
    lines = [
        f"DEF PROC{p}()",
        "  LOCAL b%()",
        "  DIM b%(5)",
        "  b%(1)=42",
        "  PRINT b%(1)",
        "ENDPROC",
    ]
    indent = ""
    for d in range(2):
        lines.append(f"{indent}FOR k{d}% = 1 TO 2")  # hard bound non-stuck
        indent += "  "
    lines.append(f"{indent}PROC{p}")
    for d in range(1, -1, -1):
        lines.append("  " * d + "NEXT")
    return "\n".join(lines)


class TestPROCComposition(unittest.TestCase):
    @given(prog=proc_with_local_array())
    @settings(max_examples=5, deadline=5000)  # Phase 1: small for fast iteration
    def test_proc_local_array_called_from_nest(self, prog: str):
        interp = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, ln in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, ln)
            interp.run()
        out = buf.getvalue()
        self.assertNotIn("?", out)
        self.assertIn("42", out)  # the value from inside the PROC


@st.composite
def control_plus_file_io(draw):
    """Non-graphics: nested control (FOR) with file I/O (PRINT#/INPUT# inside/after loops).
    Writes numbers, reads back first numeric, prints it. Predictable output for invariant.
    Uses working_dir + tempdir. Hard bounds.
    """
    depth = draw(small_depth)
    v = draw(safe_var)
    lines = [
        f"{v} = 42",
        "f = OPENOUT \"data.txt\"",
        f"PRINT #f, {v}",
    ]
    indent = ""
    for d in range(depth):
        lines.append(f"{indent}FOR i{d}% = 1 TO 2")
        indent += "  "
        lines.append(f"{indent}PRINT #f, {v} + i{d}%")
    for d in range(depth - 1, -1, -1):
        indent = "  " * d
        lines.append(f"{indent}NEXT")
    lines.append("CLOSE #f")
    lines.append("g = OPENIN \"data.txt\"")
    lines.append("INPUT #g, x%")
    lines.append("PRINT x%")
    lines.append("CLOSE #g")
    return "\n".join(lines)


class TestControlFileIO(unittest.TestCase):
    @given(prog=control_plus_file_io())
    @settings(max_examples=5, deadline=5000)  # Phase 1: small for fast iteration
    def test_nested_control_with_file_io(self, prog: str):
        with tempfile.TemporaryDirectory() as tmp:
            interp = BASICInterpreter(InterpreterConfig(dialect="mini", display="none"))
            interp.working_dir = tmp
            buf = io.StringIO()
            with redirect_stdout(buf):
                for i, line in enumerate(prog.splitlines(), 10):
                    interp.set_program_line(i * 10, line)
                interp.run()
            out = buf.getvalue()
            self.assertNotIn("?", out, f"Error in:\n{prog}\nout:\n{out}")
            # Invariant: we printed a number we wrote/read (42 or close)
            self.assertRegex(out.strip(), r'^\d+$', f"Expected single numeric from file readback, got: {out!r}")


@st.composite
def while_repeat_control_file_fn(draw):
    """Deeper non-graphics composition: WHILE + bounded REPEAT/UNTIL + FOR inner,
    DEF FN + PROC with LOCAL array+string, file PRINT#/INPUT# , complex expr in conditions/prints.
    Always terminates quickly. Exercises more _eval_*, control execute, DEF, file channels.
    """
    v = draw(safe_var)
    arr = draw(safe_var.filter(lambda x: x != v))
    p = draw(safe_var.filter(lambda x: x not in (v, arr)))
    # draw distinct channel vars to avoid collision with user vars/arrays
    chf = draw(safe_var.filter(lambda x: x not in (v, arr, p)))
    chg = draw(safe_var.filter(lambda x: x not in (v, arr, p, chf)))
    loopv = draw(safe_var.filter(lambda x: x not in (v, arr, p, chf, chg)))
    inv = draw(safe_var.filter(lambda x: x not in (v, arr, p, chf, chg, loopv)))
    # small fixed bounds
    lines = [
        "DEF FNsq(n%)=n%*n%",
        f"DEF PROC{p}(a%)",
        "  LOCAL t%()",
        "  LOCAL s$",
        "  DIM t%(3)",
        "  t%(1)=a%+10",
        "  s$=\"s\"+STR$(a%)",
        "  PRINT t%(1); \" \"; s$",
        "ENDPROC",
        f"DIM {arr}(5)",
        f"{arr}(0)=3",
        f"{v}=1",
        f"{chf}=OPENOUT \"wr.txt\"",
        f"PRINT #{chf}, {v}",
    ]
    # outer WHILE bounded by counter
    lines.append(f"WHILE {v} <= 2")
    lines.append(f"  {arr}(1) = FNsq({v})")
    lines.append(f"  PROC{p}({v})")
    lines.append(f"  PRINT #{chf}, {arr}(1) + 100")
    # inner repeat-until with for, small
    lines.append(f"  {loopv}%=0")
    lines.append("  REPEAT")
    lines.append(f"    {loopv}%={loopv}%+1")
    lines.append(f"    PRINT {arr}(1) + {loopv}%")
    lines.append(f"  UNTIL {loopv}%>=2")
    lines.append(f"  {v}={v}+1")
    lines.append("WEND")
    lines.append(f"CLOSE #{chf}")
    lines.append(f"{chg}=OPENIN \"wr.txt\"")
    lines.append(f"INPUT #{chg}, {inv}%")
    lines.append(f"PRINT {inv}%")
    lines.append(f"CLOSE #{chg}")
    return "\n".join(lines)


class TestWhileRepeatFileProcFn(unittest.TestCase):
    @given(prog=while_repeat_control_file_fn())
    @settings(max_examples=4, deadline=8000)
    def test_while_repeat_fn_proc_file_nesting(self, prog: str):
        with tempfile.TemporaryDirectory() as tmp:
            # test both dialects for differential-ish behavior (non-gfx)
            for dialect in ("mini", "bbc"):
                interp = BASICInterpreter(InterpreterConfig(dialect=dialect, display="none"))
                interp.working_dir = tmp
                buf = io.StringIO()
                with redirect_stdout(buf):
                    for i, line in enumerate(prog.splitlines(), 10):
                        interp.set_program_line(i * 10, line)
                    interp.run()
                out = buf.getvalue()
                self.assertNotIn("?", out, f"Error in dialect={dialect}:\n{prog}\nOUT:\n{out}")
                # Invariants: produced output (numbers from print inside repeat/proc), no crash
                self.assertTrue(len(out.strip()) > 0)
                # At least some numeric printed
                self.assertRegex(out, r'\d')


class TestArrayBulkInit(unittest.TestCase):
    """Focused test isolated from bbcsdl/general/calendar.txt corpus failure.
    Tests whole-array initializer syntax: DIM a$(n): a$() = "v1", "v2", ...
    Non-graphics array feature, in scope for phase 1.
    """

    def test_string_array_bulk_assign(self):
        for dialect in ("bbc", "mini"):
            interp = BASICInterpreter(InterpreterConfig(dialect=dialect, display="none"))
            interp.working_dir = tempfile.gettempdir()
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.set_program_line(10, 'DIM Month$(12)')
                interp.set_program_line(20, 'Month$() = "", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"')
                interp.set_program_line(30, 'PRINT Month$(1)')
                interp.run()
            out = buf.getvalue()
            self.assertNotIn("?", out, f"bulk assign failed in {dialect}: {out}")
            self.assertIn("January", out)


if __name__ == "__main__":
    unittest.main()
