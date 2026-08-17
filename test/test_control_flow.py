"""Focused non-graphics tests for control flow (FOR, WHILE, REPEAT, IF, EXIT, etc.)
and composition with expressions/DEFs.

Phase 1 priority: solid foundation before graphics. Non-stuck by design.

Generative loop exit verification (revised):
All hypothesis-generated loops use small fixed bounds (e.g. FOR ... TO 2,
WHILE counter < 3 with counter +=1 inside) + explicit exit conditions.
Tests now assert not only "no ?" but that the program reached the
statements *after* the loops (proving the exit paths were taken and
the interpreter did not hang in an infinite loop).
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest
from hypothesis import given, example, strategies as st, settings, HealthCheck

# Phase 1 non-graphics foundation tests.
# Run with: pytest -m "phase1 and not slow" or via run_regression.py
pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig
from mini_basic.constants import EXPR_RESERVED_WORDS, NUMERIC_BUILTIN_FUNCS


# Combine runtime reserved words + builtins
_BUILTIN_EXCLUSIONS = {
    w.lower() for w in EXPR_RESERVED_WORDS
} | {
    w.lower() for w in NUMERIC_BUILTIN_FUNCS
}
_ADDITIONAL_EXCLUSIONS = {
    "for", "to", "step", "if", "then", "else", "next", "endif",
    "def", "proc", "fn", "end", "dim", "local", "print", "data", "read",
    "while", "wend", "repeat", "until", "exit",
    "tab", "spc", "using", "bget", "bput",
}

# Builtin / keyword stems that glue with digits into bad tokens under FOR normalize
# (fold mode) or statement keywords (for1, next0). Case-sensitive dialects allow
# lowercase ``to`` / ``to0`` as identifiers; hypothesis still avoids keyword stems.
_KEYWORD_STEMS = tuple(sorted(
    _ADDITIONAL_EXCLUSIONS
    | {w.lower() for w in EXPR_RESERVED_WORDS}
    | {
        "pi", "sin", "cos", "tan", "atn", "sqr", "log", "exp", "int", "abs", "sgn",
        "rnd", "val", "str", "chr", "asc", "len", "pos", "vpos", "sum", "tab", "spc",
        "eof", "lof", "ptr", "ext", "err", "erl", "mod", "div", "and", "or", "not",
        "for", "to", "step", "next", "goto", "gosub", "return", "case", "when",
    },
    key=len,
    reverse=True,
))


# Stems that still glue in case-sensitive mini/bbc when written in *lowercase*
# (fold-only glue, or statement keywords always rewritten case-insensitively).
_FOLD_OR_STMT_PREFIX_STEMS = frozenset(_ADDITIONAL_EXCLUSIONS) | {
    "for", "to", "step", "next", "goto", "gosub", "return", "case", "when",
    "and", "or", "not", "mod", "div", "if", "then", "else", "end", "dim",
}


def _is_safe_hypothesis_var(name: str) -> bool:
    """Reject names unsafe under mini (case-sensitive) generative tests.

    Lowercase ``tana`` is a valid identifier when case-sensitive (trig unglue
    only matches uppercase SIN/COS/TAN). Still reject statement prefixes
    (``forx``) and digit-glued keyword tails (``to0``).
    """
    if name in _BUILTIN_EXCLUSIONS | _ADDITIONAL_EXCLUSIONS:
        return False
    for stem in _KEYWORD_STEMS:
        if name == stem:
            return False
        if not name.startswith(stem) or len(name) <= len(stem):
            continue
        rest0 = name[len(stem)]
        # to0 / for1 — stem + non-letter
        if not rest0.isalpha():
            return False
        # forx / nextx / andx — statement / operator keywords as prefixes
        if stem in _FOLD_OR_STMT_PREFIX_STEMS:
            return False
    return True


safe_var = st.from_regex(r"[a-z][a-z0-9_]*", fullmatch=True).filter(_is_safe_hypothesis_var)
small = st.integers(min_value=1, max_value=2)


def distinct_vars(draw, count=2):
    vars_ = []
    for _ in range(count):
        cand = draw(safe_var)
        while cand in vars_:
            cand = draw(safe_var)
        vars_.append(cand)
    return vars_ if count > 1 else vars_[0]


@st.composite
def nested_while_for_if(draw):
    """Bounded WHILE + FOR + IF composition + FN call in condition/assign.
    Exercises _execute for while/for/if, _eval_condition, array/FN expr.

    Revised for loop exit verification: always uses explicit progress counter 'v'
    that is incremented inside the WHILE. The loop condition and final PRINT
    of 'v' allow the test to assert that the loop *did* exit (v reached bound)
    rather than hanging or skipping the exit path. Small hard bounds guarantee
    termination; no UNTIL FALSE or non-progressing loops are generated.
    """
    v, a = distinct_vars(draw, 2)
    lines = [
        "DEF FNodd(x%)=x% MOD 2",
        f"DIM {a}(10)",
        f"{v}=0",
        f"WHILE {v} < 3",
        f"  FOR j% = 0 TO 1",
        f"    IF FNodd({v}+j%) THEN",
        f"      {a}(j%) = {v}*10 + j%",
        "    ENDIF",
        "  NEXT",
        f"  {v}={v}+1",
        "WEND",
        f"PRINT {a}(0); {a}(1); \"EXIT_V=\"; {v}",
    ]
    return "\n".join(lines)


class TestControlFlowComposition(unittest.TestCase):
    @given(prog=nested_while_for_if())
    @settings(
        max_examples=6,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example],
    )
    def test_while_for_if_fn_array(self, prog: str):
        interp = BASICInterpreter(InterpreterConfig(dialect="mini", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue()
        self.assertNotIn("?", out, f"prog:\n{prog}\nout:\n{out}")
        self.assertRegex(out.strip(), r'\d')
        # Revised: explicitly verify the WHILE loop had an exit (counter reached bound)
        # The generator always produces v<3 with v+=1 inside, so final v must be 3.
        self.assertIn("EXIT_V=3", out, f"WHILE loop did not reach exit condition:\n{prog}\nout:\n{out}")


@st.composite
def repeat_until_with_exit(draw):
    """REPEAT/UNTIL + inner FOR + EXIT FOR inside the FOR, small. DATA/READ mix.
    Targets repeat handling, FOR/EXIT and no 'outside loop' errors.
    """
    v = draw(safe_var)
    lines = [
        f"{v}=0",
        "DATA 7,99",
        "READ d1,d2",
        "REPEAT",
        f"  {v}={v}+1",
        "  FOR k% = 1 TO 2",
        "    IF " + v + " > 1 THEN EXIT FOR",
        "  NEXT",
        "UNTIL " + v + " >=2",
        "PRINT d1; d2; " + v,
    ]
    return "\n".join(lines)


class TestRepeatExit(unittest.TestCase):
    @given(prog=repeat_until_with_exit())
    @settings(max_examples=4, deadline=3000)
    def test_repeat_until_exit_data(self, prog: str):
        interp = BASICInterpreter(InterpreterConfig(dialect="mini", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue()
        self.assertNotIn("?", out)
        self.assertTrue(len(out.strip()) > 0)
        # The generator always produces a REPEAT that exits via the UNTIL after increment;
        # verify we reached the final PRINT (normal loop exit path exercised).
        self.assertRegex(out.strip(), r'\d')
        # Stronger exit verification: counter v starts 0, +1 inside REPEAT, UNTIL v>=2
        # so after normal exit the printed v must be >=2 (and data printed).
        # Note: ; in PRINT concatenates, so output like '7992' for 7;99;2
        self.assertRegex(out, r'7.*99.*[2-9]')  # data values + final counter >=2 after exit


class TestRepeatSameLineAndInkey(unittest.TestCase):
    """Same-line REPEAT: body: UNTIL (user-facing BBC style) + INKEY$(n).

    Regression: REPEAT: A$=INKEY$(10): PRINT A$ : UNTIL FALSE previously never
    ran the body (re-entered REPEAT forever, printed nothing).
    """

    def _run(self, lines, dialect="bbc"):
        interp = BASICInterpreter(InterpreterConfig(dialect=dialect, display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(lines, 1):
                interp.set_program_line(i * 10, line)
            interp.run()
        return buf.getvalue()

    def test_repeat_colon_same_line_body_runs(self):
        out = self._run([
            "C%=0",
            "REPEAT: C%=C%+1: PRINT C%: UNTIL C%>=3",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines(), ["1", "2", "3"])

    def test_repeat_glued_body_same_line(self):
        out = self._run([
            "C%=0",
            "REPEAT C%=C%+1: PRINT C%: UNTIL C%>=3",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines(), ["1", "2", "3"])

    def test_inkey_dollar_timeout_returns_empty(self):
        """INKEY$(n) waits ~n centiseconds then returns \"\" if no key."""
        import time
        t0 = time.perf_counter()
        out = self._run([
            "A$=INKEY$(10)",
            'PRINT "GOT|";LEN(A$)',
            "END",
        ])
        elapsed = time.perf_counter() - t0
        self.assertNotIn("?", out)
        self.assertIn("GOT|0", out)
        # 10 cs = 0.10s; allow some slack but require a real wait
        self.assertGreaterEqual(elapsed, 0.05)
        self.assertLess(elapsed, 1.5)

    def test_user_inkey_repeat_prints_newlines(self):
        """User pattern limited to 2 iters: empty keys still PRINT a line each time."""
        out = self._run([
            "C%=0",
            "REPEAT: A$=INKEY$(5): PRINT A$: C%=C%+1: UNTIL C%>=2",
        ])
        self.assertNotIn("?", out)
        # Two empty PRINTs → two newlines
        self.assertGreaterEqual(out.count("\n"), 2)

    def test_user_tab_inkey_until_q(self):
        """Exact user style: REPEAT: A$=INKEY$(n): PRINT TAB(0,0);A$;: UNTIL A$=\"Q\"OR A$=\"q\"."""
        interp = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        n = {"c": 0}

        def wait(timeout_cs: float) -> float:
            n["c"] += 1
            if n["c"] >= 3:
                return float(ord("Q"))
            return -1.0

        interp._inkey_code_wait = wait  # type: ignore[method-assign]
        buf = io.StringIO()
        line = 'REPEAT: A$ = INKEY$(10): PRINT TAB(0,0);A$;: UNTIL A$ = "Q"OR A$ = "q"'
        with redirect_stdout(buf):
            interp.set_program_line(10, line)
            interp.run()
        out = buf.getvalue()
        self.assertNotIn("?", out)
        self.assertIn("Q", out)
        self.assertGreaterEqual(n["c"], 3)

    def test_same_line_repeat_presents_terminal_each_iter(self):
        """Terminal display must present during same-line REPEAT (not only after exit)."""
        interp = BASICInterpreter(InterpreterConfig(dialect="bbc", display="terminal"))
        presents = {"n": 0}
        orig_ensure = interp._ensure_display

        def ensure() -> None:
            orig_ensure()
            disp = interp._display
            if disp is not None and not getattr(disp, "_test_present_hooked", False):
                orig_present = disp.present

                def present(*args, **kwargs):
                    presents["n"] += 1
                    return orig_present(*args, **kwargs)

                disp.present = present  # type: ignore[method-assign]
                disp._test_present_hooked = True  # type: ignore[attr-defined]

        interp._ensure_display = ensure  # type: ignore[method-assign]
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.set_program_line(10, "C%=0")
            interp.set_program_line(
                20, 'REPEAT: C%=C%+1: PRINT TAB(0,0);C%;: UNTIL C%>=3'
            )
            interp.run()
        # At least one present per iteration (and final) — must be > 1
        self.assertGreaterEqual(presents["n"], 3, f"presents={presents['n']} out={buf.getvalue()[:80]!r}")

    def test_timed_inkey_frame_paces_held_key(self):
        """Held/autorepeat keys must not make short INKEY$(n) return in 0ms."""
        import time

        interp = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        # Always-ready key simulates Windows hold/autorepeat.
        interp._inkey_value = lambda: "x"  # type: ignore[method-assign]
        t0 = time.perf_counter()
        # Three frame waits of 5cs → ~0.15s with frame padding (n<=50).
        for _ in range(3):
            code = interp._inkey_code_wait(5.0)
            self.assertEqual(code, float(ord("x")))
        elapsed = time.perf_counter() - t0
        self.assertGreaterEqual(elapsed, 0.10, f"loop not paced: {elapsed:.3f}s")
        self.assertLess(elapsed, 1.0)

    def test_long_inkey_returns_early_on_key(self):
        """Long INKEY$(n) (prompt style) still returns as soon as a key arrives."""
        import time

        interp = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        interp._inkey_value = lambda: "Q"  # type: ignore[method-assign]
        t0 = time.perf_counter()
        code = interp._inkey_code_wait(200.0)  # 2 seconds max, but key ready
        elapsed = time.perf_counter() - t0
        self.assertEqual(code, float(ord("Q")))
        self.assertLess(elapsed, 0.2, f"long INKEY$ did not return early: {elapsed:.3f}s")

    def test_inkey_zero_is_nonblocking(self):
        """INKEY$(0) must poll (not hang) so game loops like RACE.BBC can run."""
        import time

        out = self._run([
            'A$=INKEY$(0)',
            'PRINT "L";LEN(A$)',
            'END',
        ])
        self.assertNotIn("?", out)
        self.assertIn("L0", out)

    def test_bbc_if_then_goto_allowed(self):
        """RACE.BBC uses IF cond THEN GOTO n — must work in bbc dialect."""
        out = self._run([
            "A=1",
            "IF A=1 THEN GOTO 50",
            'PRINT "no"',
            "END",
            'PRINT "yes"',
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertIn("yes", out)
        self.assertNotIn("no", out)


@st.composite
def exit_in_while_and_repeat(draw):
    """Test EXIT in WHILE and REPEAT (not just FOR), with nested control.
    Covers more control structure corners for Phase-1.
    """
    v = draw(safe_var)
    lines = [
        f"{v}=0",
        "REPEAT",
        f"  {v}={v}+1",
        f"  WHILE {v} < 3",
        "    IF " + v + " = 1 THEN EXIT REPEAT",  # jump out of hierarchy: exit outer REPEAT from inside inner WHILE
        "    IF " + v + " = 2 THEN EXIT WHILE",
        "  WEND",
        "UNTIL " + v + " >=3",
        f"PRINT {v}",
    ]
    return "\n".join(lines)


class TestControlExitCorners(unittest.TestCase):
    @given(prog=exit_in_while_and_repeat())
    @settings(max_examples=5, deadline=5000)
    def test_exit_while_repeat(self, prog: str):
        interp = BASICInterpreter(InterpreterConfig(dialect="mini", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue()
        self.assertNotIn("?", out)
        self.assertTrue(len(out.strip()) > 0)
        # Should have printed a number >=3 or handled exit
        self.assertRegex(out.strip(), r'\d+')


@st.composite
def exit_for_from_deep_nesting(draw):
    """EXIT FOR from deep inside WHILE/REPEAT to test jumping outer FOR hierarchy."""
    v = draw(safe_var.filter(lambda n: n != 'i'))
    lines = [
        f"FOR i=1 TO 5",
        f"  {v}=0",
        "  REPEAT",
        f"    {v}={v}+1",
        f"    WHILE {v} < 3",
        "      i+=1",
        "      IF i=3 THEN EXIT FOR",
        "    WEND",
        "  UNTIL " + v + " >=2",
        "NEXT",
        "PRINT i",
    ]
    return "\n".join(lines)

class TestControlExitHierarchy(unittest.TestCase):
    @given(prog=exit_for_from_deep_nesting())
    @settings(max_examples=4, deadline=None)
    def test_exit_for_deep(self, prog: str):
        interp = BASICInterpreter(InterpreterConfig(dialect="mini", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue()
        self.assertNotIn("?", out)
        self.assertTrue(len(out.strip()) > 0)


@st.composite
def nested_fors_correct_matching(draw):
    """Multiple nested FORs with distinct vars and correct NEXT matching.
    Tests that NEXT binds to the correct FOR variable in hierarchy.
    Small bounds.
    """
    outer = draw(safe_var)
    inner = draw(safe_var.filter(lambda x: x != outer))
    lines = [
        f"FOR {outer}=1 TO 2",
        f"  FOR {inner}=1 TO 2",
        f"    PRINT {outer}; {inner}",
        f"  NEXT {inner}",
        f"NEXT {outer}",
    ]
    return "\n".join(lines)


class TestNestedForMatching(unittest.TestCase):
    @given(prog=nested_fors_correct_matching())
    @settings(max_examples=8, deadline=3000)
    def test_nested_fors_correct_next_vars(self, prog: str):
        """Nested FOR/NEXT matching; vars from safe_var (no to0/for1 stems)."""
        interp = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue()
        self.assertNotIn("?", out, f"prog:\n{prog}\nout:\n{out}")
        # Expect 4 lines of output like "1 1\n1 2\n2 1\n2 2\n" or similar
        self.assertEqual(len(out.strip().splitlines()), 4, f"prog:\n{prog}\nout:\n{out}")


class TestCaseSensitiveTrigIdents(unittest.TestCase):
    """Case-sensitive: lowercase tana/sina are vars; uppercase SINa still glues."""

    def _run(self, lines, *, case_sensitive: bool):
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect="mini",
                display="none",
                identifiers_case_sensitive=case_sensitive,
            )
        )
        buf = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(err):
            for i, line in enumerate(lines, 1):
                interp.set_program_line(i * 10, line)
            interp.run()
        return buf.getvalue(), err.getvalue()

    def test_lowercase_tana_is_variable_when_case_sensitive(self):
        out, err = self._run(
            ["tana=5", "PRINT tana", "END"],
            case_sensitive=True,
        )
        self.assertNotIn("?", err + out)
        self.assertEqual(out.strip(), "5")

    def test_uppercase_SINa_still_glues_when_case_sensitive(self):
        out, err = self._run(
            ["a=0", "PRINT SINa", "END"],
            case_sensitive=True,
        )
        self.assertNotIn("?", err + out)
        self.assertTrue(out.strip().endswith("0") or out.strip() == "0")

    def test_uppercase_TAN10_glues_digit_arg_when_case_sensitive(self):
        """BBC keyword+number: TAN10 → TAN(10); tan10 LHS stays a variable."""
        out, err = self._run(
            ["tan10=TAN10", "PRINT tan10", "END"],
            case_sensitive=True,
        )
        self.assertNotIn("?", err + out)
        import math
        self.assertAlmostEqual(float(out.strip()), math.tan(10.0), places=5)

    def test_monadic_digit_and_letter_glue_when_case_sensitive(self):
        """ABS3/SQR4/NOT0 and ABSx match BBC keyword glue (not only SIN/COS/TAN)."""
        out, err = self._run(
            [
                "x=4",
                'PRINT ABS3; ","; SQR4; ","; INT3.7; ","; NOT0; ","; ABSx',
                "END",
            ],
            case_sensitive=True,
        )
        self.assertNotIn("?", err + out)
        parts = [p.strip() for p in out.strip().split(",")]
        self.assertEqual(parts, ["3", "2", "3", "-1", "4"])

    def test_lowercase_tan10_is_variable_when_case_sensitive(self):
        out, err = self._run(
            ["tan10=5", "PRINT tan10", "END"],
            case_sensitive=True,
        )
        self.assertNotIn("?", err + out)
        self.assertEqual(out.strip(), "5")

    def test_lowercase_abs3_is_variable_when_case_sensitive(self):
        out, err = self._run(
            ["abs3=9", "PRINT abs3", "END"],
            case_sensitive=True,
        )
        self.assertNotIn("?", err + out)
        self.assertEqual(out.strip(), "9")

    def test_fold_mode_still_unglues_lowercase_sina(self):
        out, err = self._run(
            ["a=0", "PRINT sina", "END"],
            case_sensitive=False,
        )
        self.assertNotIn("?", err + out)


class TestForCaseSensitiveToVar(unittest.TestCase):
    """Case-sensitive dialect: lowercase ``to`` / ``to0`` are identifiers, not TO."""

    def _run(self, lines, *, case_sensitive: bool):
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect="bbc",
                display="none",
                identifiers_case_sensitive=case_sensitive,
            )
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(lines, 1):
                interp.set_program_line(i * 10, line)
            interp.run()
        return buf.getvalue()

    def test_for_to_var_case_sensitive(self):
        out = self._run(
            ["FOR to=1 TO 2", 'PRINT to', "NEXT", "END"],
            case_sensitive=True,
        )
        self.assertNotIn("?", out)
        self.assertEqual(
            [ln.strip() for ln in out.strip().splitlines() if ln.strip()],
            ["1", "2"],
        )

    def test_for_to0_var_case_sensitive(self):
        """Regression: normalize must not turn to0= into 'to 0='."""
        out = self._run(
            ["FOR to0=1 TO 2", 'PRINT to0', "NEXT", "END"],
            case_sensitive=True,
        )
        self.assertNotIn("?", out)
        self.assertEqual(
            [ln.strip() for ln in out.strip().splitlines() if ln.strip()],
            ["1", "2"],
        )

    def test_for_to0_var_case_insensitive_head_protected(self):
        """Fold mode: loop var head before = is not split (to0=1 TO 2)."""
        out = self._run(
            ["FOR to0=1 TO 2", 'PRINT to0', "NEXT", "END"],
            case_sensitive=False,
        )
        self.assertNotIn("?", out)
        self.assertEqual(
            [ln.strip() for ln in out.strip().splitlines() if ln.strip()],
            ["1", "2"],
        )

    def test_glued_1to10_still_works_case_sensitive(self):
        out = self._run(
            ["FOR I=1TO3", 'PRINT I', "NEXT", "END"],
            case_sensitive=True,
        )
        self.assertNotIn("?", out)
        self.assertEqual(
            [ln.strip() for ln in out.strip().splitlines() if ln.strip()],
            ["1", "2", "3"],
        )

    def test_nested_for_to0_case_sensitive(self):
        out = self._run(
            [
                "FOR to0=1 TO 2",
                "  FOR j=1 TO 2",
                '    PRINT to0;j',
                "  NEXT j",
                "NEXT to0",
                "END",
            ],
            case_sensitive=True,
        )
        self.assertNotIn("?", out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(lines, ["11", "12", "21", "22"])


class TestForSameLineBody(unittest.TestCase):
    """FOR with trailing same-line body when NEXT is on a later line.

    Regression (saucer.bbc): ``FOR X=…:S=X*X:P=SQR(B-S)`` then multi-line
    inner loop and ``NEXT`` on a later line must re-run S/P each outer
    iteration. Jumping only to the next *line* left P stuck at A and drew
    vertical columns instead of the disc silhouette.
    """

    def _run(self, lines, dialect="bbc"):
        interp = BASICInterpreter(InterpreterConfig(dialect=dialect, display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(lines, 1):
                interp.set_program_line(i * 10, line)
            interp.run()
        return buf.getvalue()

    def test_for_trailing_body_reruns_each_iteration(self):
        """Same-line assignments after FOR re-execute when NEXT is later."""
        out = self._run([
            'FOR X=0 TO 2:S=X*X:PRINT X;"|";S',
            "NEXT",
            "END",
        ])
        self.assertNotIn("?", out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(lines, ["0|0", "1|1", "2|4"])

    def test_saucer_style_nested_for_rebinds_p_and_ni(self):
        """Outer FOR header binds S/P; nested FOR I=-P TO P must shrink with X."""
        out = self._run([
            "A=160:B=A*A:XS=40:YS=2",
            "FOR X=0 TO A STEP XS:S=X*X:P=SQR(B-S):NI=0",
            "FOR I=-P TO P STEP 6*YS:NI=NI+1:NEXT",
            # Use | separators — BBC zone PRINT glues adjacent numbers
            'PRINT X;"|";P;"|";NI',
            "NEXT",
            "END",
        ])
        self.assertNotIn("?", out)
        rows = []
        for ln in out.strip().splitlines():
            parts = [p.strip() for p in ln.split("|")]
            if len(parts) >= 3:
                rows.append((float(parts[0]), float(parts[1]), float(parts[2])))
        self.assertEqual(len(rows), 5)  # X=0,40,80,120,160
        # P must fall as |X| rises (ellipse), not stay locked at A
        ps = [r[1] for r in rows]
        self.assertAlmostEqual(ps[0], 160.0, places=3)
        self.assertLess(ps[1], ps[0])
        self.assertLess(ps[2], ps[1])
        self.assertLess(ps[3], ps[2])
        self.assertAlmostEqual(ps[-1], 0.0, places=3)
        # NI resets each outer iter and shrinks with P (not accumulates 27,54,81…)
        nis = [r[2] for r in rows]
        self.assertEqual(nis[0], 27.0)
        self.assertLess(nis[1], nis[0] * 1.5)  # not doubled
        self.assertLess(nis[-1], nis[0])
        for i in range(1, len(nis)):
            self.assertLessEqual(nis[i], nis[i - 1] + 1)

    def test_multiline_for_body_still_runs(self):
        """FOR alone on its line: body on following lines (pre-existing path)."""
        out = self._run([
            "FOR X=0 TO 2",
            "P=10-X*3:N=0",
            "FOR I=-P TO P STEP 2:N=N+1:NEXT",
            'PRINT X;"|";P;"|";N',
            "NEXT",
            "END",
        ])
        self.assertNotIn("?", out)
        rows = []
        for ln in out.strip().splitlines():
            parts = [p.strip() for p in ln.split("|")]
            if len(parts) >= 3:
                rows.append((float(parts[0]), float(parts[1]), float(parts[2])))
        self.assertEqual(rows, [
            (0.0, 10.0, 11.0),
            (1.0, 7.0, 8.0),
            (2.0, 4.0, 5.0),
        ])

    def test_inline_for_next_unchanged(self):
        """Fully inline FOR…:body:NEXT still works after same-line body fix."""
        out = self._run([
            "N=0:FOR I=1 TO 3:N=N+I:NEXT:PRINT N",
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertIn("6", out.strip().splitlines()[-1])

    def test_double_for_headers_one_line(self):
        """Nested FOR…:FOR…:body:NEXT:NEXT all on one line."""
        out = self._run([
            'FOR X=1 TO 2:FOR I=1 TO 2:PRINT X;"|";I:NEXT:NEXT',
            "END",
        ])
        self.assertNotIn("?", out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(lines, ["1|1", "1|2", "2|1", "2|2"])

    def test_next_double_comma_closes_three_loops(self):
        """BBC NEXT ,, is NEXT:NEXT:NEXT (unnamed)."""
        out = self._run([
            'FOR I%=1 TO 2:FOR J%=1 TO 2:FOR K%=1 TO 2:'
            'PRINT I%;J%;K%:NEXT ,,',
            'END',
        ])
        self.assertNotIn('?', out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(
            lines,
            ['111', '112', '121', '122', '211', '212', '221', '222'],
        )

    def test_next_named_list_closes_inner_then_outer(self):
        out = self._run([
            'FOR I=1 TO 2:FOR J=1 TO 2:PRINT I;J:NEXT J,I',
            'END',
        ])
        self.assertNotIn('?', out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(lines, ['11', '12', '21', '22'])

    def test_next_named_list_for_order(self):
        """NEXT I%,J%,K% (FOR order) is the same as NEXT K%,J%,I%."""
        expected = [
            '111', '112', '121', '122', '211', '212', '221', '222',
        ]
        for next_list in ('K%,J%,I%', 'I%,J%,K%'):
            out = self._run([
                'FOR I%=1 TO 2:FOR J%=1 TO 2:FOR K%=1 TO 2:'
                f'PRINT I%;J%;K%:NEXT {next_list}',
                'END',
            ])
            self.assertNotIn('?', out, next_list)
            lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
            self.assertEqual(lines, expected, next_list)
        out = self._run([
            'FOR I%=1 TO 2',
            'FOR J%=1 TO 2',
            'FOR K%=1 TO 2',
            'PRINT I%;J%;K%',
            'NEXT I%,J%,K%',
            'END',
        ])
        self.assertNotIn('?', out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(lines, expected)


class TestIfColonTail(unittest.TestCase):
    """BBC single-line IF: rest of line (including colon-split stmts) is conditional.

    Compact form without THEN is colon-split into separate statements:
      IF I=-P M=Y:N=Y  →  [IF I=-P M=Y] [N=Y]
    True path already appended trailing via _if_branch_inline_code; false path
    must skip the tail (saucer hidden-line: only plot when M=Y OR N=Y).
    """

    def _run(self, lines, dialect="bbc"):
        interp = BASICInterpreter(InterpreterConfig(dialect=dialect, display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(lines, 1):
                interp.set_program_line(i * 10, line)
            interp.run()
        return buf.getvalue()

    def test_compact_if_false_skips_colon_tail(self):
        out = self._run([
            "M=0:N=0",
            "IF 0 M=1:N=1",
            'PRINT M;"|";N',
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), "0|0")

    def test_compact_if_true_runs_colon_tail(self):
        out = self._run([
            "M=0:N=0",
            "IF 1 M=1:N=1",
            'PRINT M;"|";N',
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), "1|1")

    def test_saucer_init_if_i_eq_neg_p(self):
        """IF I=-P M=Y:N=Y — only first I of each column re-inits envelope."""
        out = self._run([
            "P=5:M=0:N=0",
            "FOR I=-P TO P STEP 5",
            "Y=I",
            "IF I=-P M=Y:N=Y",
            "IF Y>M M=Y",
            "IF Y<N N=Y",
            'PRINT I;"|";M;"|";N',
            "NEXT",
            "END",
        ])
        self.assertNotIn("?", out)
        rows = []
        for ln in out.strip().splitlines():
            parts = [p.strip() for p in ln.split("|")]
            if len(parts) >= 3:
                rows.append((float(parts[0]), float(parts[1]), float(parts[2])))
        # I=-5: init M=N=-5; I=0: M=0 N=-5; I=5: M=5 N=-5
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], (-5.0, -5.0, -5.0))
        self.assertEqual(rows[1][1], 0.0)   # M grew
        self.assertEqual(rows[1][2], -5.0)  # N stayed (not reset to 0)
        self.assertEqual(rows[2][1], 5.0)
        self.assertEqual(rows[2][2], -5.0)

    def test_saucer_plot_if_false_skips_second_plot(self):
        """IF M=Y OR N=Y stmt1:stmt2 — false skips both colon parts."""
        out = self._run([
            "M=5:N=1:Y=3:F=0",
            "IF M=Y OR N=Y F=F+1:F=F+10",
            "PRINT F",
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), "0")

    def test_saucer_plot_if_true_runs_both_plot_parts(self):
        out = self._run([
            "M=5:N=1:Y=5:F=0",
            "IF M=Y OR N=Y F=F+1:F=F+10",
            "PRINT F",
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), "11")

    def test_then_if_false_skips_whole_line(self):
        out = self._run([
            "N=0",
            "IF 0 THEN N=1:N=2",
            "PRINT N",
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), "0")

    def test_then_if_true_runs_colon_body(self):
        out = self._run([
            "N=0",
            "IF 1 THEN N=1:N=2",
            "PRINT N",
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), "2")

    def test_then_else_true_skips_else(self):
        out = self._run([
            "N=0",
            "IF 1 THEN N=1:N=9 ELSE N=2",
            "PRINT N",
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), "9")

    def test_then_else_false_runs_else_colon_tail(self):
        out = self._run([
            "N=0",
            "IF 0 THEN N=1 ELSE N=2:N=3",
            "PRINT N",
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), "3")

    def test_silhouette_not_all_points_plotted(self):
        """Saucer envelope: some I samples must be hidden (not every point plots).

        Use HIT (not PLOTTED) — compact IF can mis-split names starting with PLOT.
        """
        out = self._run([
            "A=80:B=A*A:C=64:XS=40:YS=8:HIT=0:TOTAL=0",
            "FOR X=0 TO A STEP XS:S=X*X:P=SQR(B-S)",
            "FOR I=-P TO P STEP 6*YS",
            "R=SQR(S+I*I)/A",
            "Q=(R-1)*SIN(24*R)",
            "Y=INT(I/3+Q*C)",
            "IF I=-P M=Y:N=Y",
            "IF Y>M M=Y",
            "IF Y<N N=Y",
            "TOTAL=TOTAL+1",
            "IF M=Y OR N=Y THEN HIT=HIT+1",
            "NEXT:NEXT",
            'PRINT TOTAL;"|";HIT',
            "END",
        ])
        self.assertNotIn("?", out)
        parts = out.strip().splitlines()[-1].strip().split("|")
        total, plotted = float(parts[0]), float(parts[1])
        self.assertGreater(total, 5)
        self.assertGreater(plotted, 0)
        self.assertLess(plotted, total)  # some hidden


class TestWhileAndRepeatForms(unittest.TestCase):
    """WHILE/REPEAT multi-line and same-line forms (BBC demos)."""

    def _run(self, lines, dialect="bbc"):
        interp = BASICInterpreter(InterpreterConfig(dialect=dialect, display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(lines, 1):
                interp.set_program_line(i * 10, line)
            interp.run()
        return buf.getvalue()

    def test_while_wend_multiline(self):
        out = self._run([
            "I=0",
            "WHILE I<3",
            "I=I+1",
            "PRINT I",
            "WEND",
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(
            [ln.strip() for ln in out.strip().splitlines() if ln.strip()],
            ["1", "2", "3"],
        )

    def test_while_endwhile_multiline(self):
        out = self._run([
            "I=0",
            "WHILE I<2",
            "I=I+1",
            'PRINT I',
            "ENDWHILE",
            "END",
        ])
        self.assertNotIn("?", out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(lines, ["1", "2"])

    def test_while_same_line_body_wend(self):
        """WHILE cond: body: WEND on one line (if supported)."""
        out = self._run([
            "I=0",
            "WHILE I<3:I=I+1:PRINT I:WEND",
            "END",
        ])
        self.assertNotIn("?", out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(lines, ["1", "2", "3"])

    def test_repeat_trailing_body_until_later(self):
        """REPEAT body on header line; UNTIL on later line."""
        out = self._run([
            "C=0",
            "REPEAT C=C+1",
            "PRINT C",
            "UNTIL C>=3",
            "END",
        ])
        self.assertNotIn("?", out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(lines, ["1", "2", "3"])

    def test_repeat_fully_inline(self):
        out = self._run([
            "C=0:REPEAT:C=C+1:PRINT C:UNTIL C>=2",
            "END",
        ])
        self.assertNotIn("?", out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(lines, ["1", "2"])


class TestCaseWhenColon(unittest.TestCase):
    """CASE/WHEN multi-statement WHEN arms."""

    def _run(self, lines, dialect="bbc"):
        interp = BASICInterpreter(InterpreterConfig(dialect=dialect, display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(lines, 1):
                interp.set_program_line(i * 10, line)
            interp.run()
        return buf.getvalue()

    def test_case_when_single_print(self):
        out = self._run([
            "X=2",
            "CASE X OF",
            'WHEN 1: PRINT "A"',
            'WHEN 2: PRINT "B"',
            'WHEN 3: PRINT "C"',
            "ENDCASE",
            'PRINT "Z"',
            "END",
        ])
        self.assertNotIn("?", out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(lines, ["B", "Z"])

    def test_case_when_colon_tail_on_match(self):
        out = self._run([
            "X=2:F=0",
            "CASE X OF",
            "WHEN 1: F=1",
            "WHEN 2: F=F+1:F=F+10",
            "WHEN 3: F=99",
            "ENDCASE",
            "PRINT F",
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), "11")

    def test_case_when_nonmatch_does_not_run(self):
        out = self._run([
            "X=1:F=0",
            "CASE X OF",
            "WHEN 1: F=5",
            "WHEN 2: F=F+100",
            "ENDCASE",
            "PRINT F",
            "END",
        ])
        self.assertNotIn("?", out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), "5")


class TestOnErrorColonTail(unittest.TestCase):
    """ON ERROR handler may include colon-separated statements."""

    def _run(self, lines, dialect="bbc"):
        interp = BASICInterpreter(InterpreterConfig(dialect=dialect, display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(lines, 1):
                interp.set_program_line(i * 10, line)
            interp.run()
        return buf.getvalue()

    def test_on_error_print_and_assign(self):
        out = self._run([
            'ON ERROR PRINT "E": N=9: END',
            "PRINT 1/0",
            "PRINT N",
            "END",
        ])
        self.assertIn("E", out)
        # Handler END should stop before falling through wrongly
        self.assertNotIn("?", out.split("E")[0] if "E" in out else out)

    def test_on_error_if_err_compiled_condition(self):
        """piechart: ON ERROR … : IF ERR=17 … ELSE … — ERR must bind in compiled IF."""
        out = self._run([
            'ON ERROR IF ERR=17 PRINT "E17" ELSE PRINT "E";ERR: END',
            "A=1/0",
            "END",
        ])
        self.assertNotIn("NameError", out)
        self.assertRegex(out, r"E17|E\s*\d+")


@st.composite
def nested_fors_mismatch(draw):
    """Nested FORs with mismatched NEXT to trigger error.
    For error coverage.
    """
    outer = draw(safe_var)
    inner = draw(safe_var.filter(lambda x: x != outer))
    lines = [
        f"FOR {outer}=1 TO 2",
        f"  FOR {inner}=1 TO 2",
        f"  NEXT {outer}",  # mismatch
        f"NEXT {inner}",
    ]
    return "\n".join(lines)


class TestNestedForMismatch(unittest.TestCase):
    @given(prog=nested_fors_mismatch())
    @settings(max_examples=3, deadline=3000)
    def test_nested_fors_mismatch_next(self, prog: str):
        interp = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue()
        self.assertIn("?", out)  # should have mismatch or next without error


@st.composite
def nested_ifs_else_matching(draw):
    """Nested IF with ELSE to test correct binding of ELSE to innermost IF.
    Uses structured IF/ENDIF for clarity, with inline ELSE.
    """
    a = draw(safe_var)
    b = draw(safe_var.filter(lambda x: x != a))
    lines = [
        f"{a}=1",
        f"{b}=0",
        f"IF {a} > 0 THEN",
        f"  IF {b} > 0 THEN",
        f"    PRINT 1",
        f"  ELSE",
        f"    PRINT 2",  # this ELSE should bind to inner IF
        f"  ENDIF",
        f"ELSE",
        f"  PRINT 3",
        f"ENDIF",
    ]
    return "\n".join(lines)


class TestNestedIfElse(unittest.TestCase):
    @given(prog=nested_ifs_else_matching())
    @settings(max_examples=5, deadline=3000)
    def test_nested_if_else_binds_correctly(self, prog: str):
        interp = BASICInterpreter(InterpreterConfig(dialect="mini", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue().strip()
        self.assertNotIn("?", out)
        # With a=1, b=0, should hit inner ELSE, print 2
        self.assertEqual(out, "2")


@st.composite
def mini_continue_in_loop(draw):
    """CONTINUE in WHILE (mini dialect only). Small bound.
    Covers the CONTINUE implementation path and dialect guard.
    """
    v = draw(safe_var)
    lines = [
        f"{v}=0",
        f"WHILE {v} < 4",
        f"  {v}={v}+1",
        "  IF " + v + " = 2 THEN CONTINUE",
        f"  PRINT {v};",
        "WEND",
    ]
    return "\n".join(lines)


class TestMiniContinue(unittest.TestCase):
    @given(prog=mini_continue_in_loop())
    @settings(max_examples=3, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
    def test_continue_skips_in_while(self, prog: str):
        interp = BASICInterpreter(InterpreterConfig(dialect="mini", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue().strip()
        self.assertNotIn("?", out)
        # Should have printed 1 3 4 (skipped 2)
        self.assertIn("1", out)
        self.assertIn("3", out)
        self.assertNotIn("2", out)  # the continue skipped the print for 2


def mits_numbered_goto_next():
    """Mits-style numbered with GOTO to NEXT inside FOR (like 1DLIFE).
    Covers the legacy jump to NEXT without popping frame.
    The returned text mimics a real .BAS file (leading line numbers).
    (No longer a @composite because it doesn't use draw().)
    """
    lines = [
        "10 M=5",
        "20 FOR I=0 TO M",
        "30   IF I=3 THEN GOTO 50",
        "40   PRINT I;",
        "50 NEXT I",
        "60 PRINT",
    ]
    return "\n".join(lines)


@pytest.mark.mits
class TestMitsLegacyControl(unittest.TestCase):
    def test_goto_to_next_in_for(self):
        """Mits-style numbered with GOTO to NEXT inside FOR (like 1DLIFE).
        Uses real numbered load path.
        """
        prog = mits_numbered_goto_next()
        interp = BASICInterpreter(InterpreterConfig(dialect="mits", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            # Real numbered load path (exactly like loading 1DLIFE.BAS etc.)
            import re
            for raw in prog.splitlines():
                m = re.match(r'^\s*(\d+)\s+(.*)$', raw.strip())
                if m:
                    interp.set_program_line(int(m.group(1)), m.group(2))
            interp.run()
        out = buf.getvalue().strip()
        self.assertNotIn("?", out)
        # Should print 01245 or similar, skipping 3 via goto to NEXT
        self.assertIn("0", out)
        self.assertIn("1", out)
        self.assertIn("2", out)
        self.assertNotIn("3", out)
        self.assertIn("4", out)


@st.composite
def mini_continue_in_for(draw):
    """CONTINUE in FOR (mini). Tests skip in counted loop."""
    v = draw(safe_var)
    lines = [
        f"FOR {v}=1 TO 5",
        f"  IF {v} = 3 THEN CONTINUE",
        f"  PRINT {v};",
        "NEXT",
    ]
    return "\n".join(lines)


class TestMiniContinueFor(unittest.TestCase):
    @given(prog=mini_continue_in_for())
    @settings(max_examples=2, deadline=2000)
    def test_continue_skips_in_for(self, prog: str):
        interp = BASICInterpreter(InterpreterConfig(dialect="mini", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue().strip()
        self.assertNotIn("?", out)
        self.assertIn("1", out)
        self.assertIn("2", out)
        self.assertNotIn("3", out)  # skipped
        self.assertIn("4", out)
        self.assertIn("5", out)


@st.composite
def on_error_inside_nested_loops(draw):
    """ON ERROR inside FOR + WHILE, with RESUME, plus EXIT after error recovery.
    Exercises error handler + control stack interaction. Bounded, mini (EXIT FOR).
    """
    v = draw(safe_var.filter(lambda n: n != 'i'))
    lines = [
        "ON ERROR PRINT \"E\"; : RESUME NEXT",
        f"{v}=0",
        "FOR i=1 TO 3",
        f"  {v}={v}+1",
        "  WHILE " + v + " < 5",
        f"    IF i=2 THEN PRINT 1/0",  # force error inside
        f"    {v}={v}+1",
        "  WEND",
        "  IF i=3 THEN EXIT FOR",
        "NEXT",
        f"PRINT {v}",
    ]
    return "\n".join(lines)


class TestOnErrorInControl(unittest.TestCase):
    @given(prog=on_error_inside_nested_loops())
    @settings(max_examples=3, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_on_error_recovery_in_loops(self, prog: str):
        interp = BASICInterpreter(InterpreterConfig(dialect="mini", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue()
        self.assertNotIn("?", out)  # no unhandled crash (trap was active, recovered)
        self.assertTrue(len(out.strip()) > 0)
        # Note: full inline handler stmt exec is still basic in runtime;
        # this exercises the trap set + BasicRuntimeError catch + resume path.


@st.composite
def on_error_inside_proc(draw):
    """ON ERROR + RESUME set inside PROC, error inside it.
    Verifies RESUME works in PROC/DEF context (Phase 1 TODO).
    """
    lines = [
        "DEF PROCbad",
        "ON ERROR PRINT \"E\"; : RESUME NEXT",
        "PRINT 1/0",
        "PRINT \"AI\"",
        "ENDPROC",
        "PROCbad",
        "PRINT \"done\"",
    ]
    return "\n".join(lines)


class TestOnErrorInProc(unittest.TestCase):
    @given(prog=on_error_inside_proc())
    @settings(max_examples=2, deadline=3000)
    def test_on_error_resume_in_proc(self, prog: str):
        interp = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            for i, line in enumerate(prog.splitlines(), 10):
                interp.set_program_line(i * 10, line)
            interp.run()
        out = buf.getvalue()
        self.assertNotIn("?", out)
        self.assertIn("E", out)
        self.assertIn("AI", out)  # RESUME NEXT continued inside proc
        self.assertIn("done", out)


if __name__ == "__main__":
    unittest.main()
