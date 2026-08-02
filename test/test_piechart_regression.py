"""Simple regression tests for piechart-related BBCSDL support.

Keeps the suite small and fast (display=none). Covers:
- ON ERROR + IF ERR= (compiled condition; was NameError)
- @tmp$ path string
- OSCLI GSAVE / DISPLAY (piechart bitmap squash path)
- COSa / SINa glue used by PROCsector
"""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

try:
    import pytest
    pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]
except ImportError:  # allow unittest without pytest installed
    pytest = None  # type: ignore
    pytestmark = []

from mini_basic import BASICInterpreter, InterpreterConfig


def _run(lines, *, dialect: str = "bbc") -> str:
    interp = BASICInterpreter(
        InterpreterConfig(dialect=dialect, display="none", display_locked=True)
    )
    buf = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(err), patch("time.sleep"):
        for i, line in enumerate(lines, 1):
            interp.set_program_line(i * 10, line)
        interp.run()
    return buf.getvalue() + err.getvalue()


class TestOnErrorErrErl(unittest.TestCase):
    def test_on_error_if_err_else_branch(self):
        """Division error is not 17 → ELSE branch prints E + code (no NameError)."""
        out = _run([
            'ON ERROR IF ERR=17 PRINT "E17" ELSE PRINT "E";ERR: END',
            "A=1/0",
            "END",
        ])
        self.assertNotIn("NameError", out)
        self.assertNotIn("? OSCLI error", out)
        # ERR for 1/0 is typically 11 (or similar); must print E + digits
        self.assertRegex(out.replace(" ", ""), r"E\d+")

    def test_on_error_oscli_refresh_then_if_err(self):
        """piechart-style ON ERROR header must register and run IF ERR=."""
        out = _run([
            'ON ERROR OSCLI "REFRESH ON" : IF ERR=17 PRINT "CHAIN" ELSE PRINT "R";ERR : END',
            "A=1/0",
            "END",
        ])
        self.assertNotIn("NameError", out)
        self.assertRegex(out.replace(" ", ""), r"R\d+|CHAIN")


class TestBbcAtTmp(unittest.TestCase):
    def test_tmp_dollar_prints_path(self):
        out = _run(['PRINT @tmp$', "END"])
        self.assertNotIn("?", out)
        text = out.strip()
        self.assertTrue(len(text) > 2, msg=repr(out))
        # Trailing separator (BBCSDL convention)
        self.assertTrue(
            text.endswith("\\") or text.endswith("/"),
            msg=f"@tmp$ should end with path sep: {text!r}",
        )


class TestOscliGsaveDisplay(unittest.TestCase):
    def test_gsave_writes_bmp(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "pie.tmp.bmp").replace("\\", "\\\\")
            out = _run([
                "MODE 8",
                "GCOL 1",
                "MOVE 100,100",
                "PLOT 69,200,200",
                f'OSCLI "GSAVE ""{path}"" 0,0,100,100"',
                "END",
            ])
            self.assertNotIn("? OSCLI error", out)
            self.assertNotIn("NameError", out)
            # Path may use single backslashes in actual file system
            real = path.replace("\\\\", "\\")
            self.assertTrue(os.path.isfile(real), msg=f"missing {real}; out={out!r}")
            self.assertGreater(os.path.getsize(real), 54)

    def test_gsave_display_roundtrip_no_oscli_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "pie2.bmp").replace("\\", "\\\\")
            out = _run([
                "MODE 8",
                f'OSCLI "GSAVE ""{path}"" 0,0,40,40"',
                "CLS",
                f'OSCLI "DISPLAY ""{path}"" 0,0,40,20"',
                "END",
            ])
            self.assertNotIn("? OSCLI error", out)
            self.assertNotIn("NameError", out)

    def test_gsave_under_refresh_off_does_not_present(self):
        """piechart: GSAVE must not flip the upright render before DISPLAY squash."""
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect="bbc",
                display="pygame",
                display_locked=True,
                hold_display_open=False,
            )
        )
        presents = {"n": 0}
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "silent.bmp").replace("\\", "\\\\")
            lines = [
                "MODE 8",
                "*REFRESH OFF",
                "GCOL 1",
                "MOVE 0,0",
                "PLOT 69,100,100",
                f'OSCLI "GSAVE ""{path}"" 0,0,200,200"',
                "END",
            ]
            for i, line in enumerate(lines, 1):
                interp.set_program_line(i * 10, line)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), patch(
                "time.sleep"
            ):
                # Hook present after display exists (MODE opens it).
                real_run = interp.run

                def run_and_hook():
                    # Ensure display first via partial run? Patch after load by wrapping.
                    return real_run()

                orig_ensure = interp._ensure_display

                def ensure_and_hook():
                    orig_ensure()
                    disp = interp._display
                    if disp is not None and not getattr(disp, "_gsave_hooked", False):
                        real_present = disp.present

                        def counting_present(*, force=False):
                            presents["n"] += 1
                            return real_present(force=force)

                        disp.present = counting_present  # type: ignore[method-assign]
                        disp._gsave_hooked = True  # type: ignore[attr-defined]
                    return None

                interp._ensure_display = ensure_and_hook  # type: ignore[method-assign]
                # MODE and plot will call ensure; count presents from GSAVE only after baseline
                interp.run()
            # MODE may present once; GSAVE must not add a force-present of the plot.
            # Allow MODE open presents but require GSAVE path left a file without needing
            # more than a couple of early presents.
            real = path.replace("\\\\", "\\")
            self.assertTrue(os.path.isfile(real))
            self.assertGreater(os.path.getsize(real), 54)
            # With *REFRESH OFF, present count should stay very low (MODE setup only).
            self.assertLessEqual(presents["n"], 3, f"unexpected presents: {presents['n']}")


class TestCosaGlue(unittest.TestCase):
    def test_cosa_sina_match_cos_sin(self):
        out = _run([
            "a=0",
            'PRINT COS(a);"|";COSa;"|";SIN(a);"|";SINa',
            "END",
        ])
        self.assertNotIn("?", out)
        parts = [p.strip() for p in out.strip().split("|")]
        self.assertEqual(len(parts), 4)
        # COS(0)=1, SIN(0)=0 (allow BBC spacing / float noise)
        self.assertTrue(parts[0].strip().endswith("1") or "1" in parts[0])
        self.assertEqual(parts[0].replace(" ", ""), parts[1].replace(" ", ""))


class TestPiechartLoadSmoke(unittest.TestCase):
    def test_piechart_runs_past_oscli_without_nameerror(self):
        """Load corpus piechart; stop before infinite REPEAT; no OSCLI/ERR crash."""
        interp = BASICInterpreter(
            InterpreterConfig(dialect="bbc", display="none", display_locked=True)
        )
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "test", "corpus", "bbcsdl", "graphics", "piechart.txt")
        if not os.path.isfile(path):
            self.skipTest("piechart.txt missing")
        interp.load(path, announce=False)
        for ln, s in list(interp.program.items()):
            u = s.strip().upper()
            if "UNTIL FALSE" in u or u.startswith("REPEAT"):
                interp.program[ln] = "END"
            if "Depth = 128" in s or s.strip() == "Depth = 128":
                interp.program[ln] = "Depth = 4"
        buf = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(err), patch("time.sleep"):
            interp.run()
        out = buf.getvalue() + err.getvalue()
        self.assertNotIn("NameError", out)
        self.assertNotIn("? OSCLI error", out)


class TestPiechartSkyBackground(unittest.TestCase):
    def test_color_15_plus_128_keeps_palette_index(self):
        """COLOR 15,&r,&g,&b then COLOR 15+128 must CLS to sky, not gray (7)."""
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect="bbc",
                display="pygame",
                display_locked=True,
                hold_display_open=False,
            )
        )
        interp._shutdown_display = lambda **k: None  # type: ignore[method-assign]
        for i, line in enumerate(
            [
                "MODE 8",
                "COLOR 15,&87,&CE,&FF",
                "COLOR 15+128",
                "CLS",
                "END",
            ],
            1,
        ):
            interp.set_program_line(i * 10, line)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), patch(
            "time.sleep"
        ):
            interp.run()
        disp = interp._display
        self.assertIsNotNone(disp)
        self.assertEqual(disp._bg_colour, 15)
        disp.present(force=True)
        surf = disp._canvas
        # Sample a corner — should be sky blue, not palette gray/white.
        r, g, b = surf.get_at((8, 8))[:3]
        self.assertGreater(b, r + 20, msg=f"expected sky-ish blue, got {(r, g, b)}")
        self.assertGreater(b, 150)


class TestVduIndirection(unittest.TestCase):
    def test_vdu_bang_with_spaces_around_percent(self):
        """piechart label MOVE: tolerate ``@VDU %!220`` after case/spacing noise."""
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect="bbc",
                display="none",
                display_locked=True,
                graphics_width=640,
                graphics_height=512,
            )
        )
        v220 = int(interp._eval_numeric("@vdu%!220"))
        self.assertGreater(v220, 0)
        self.assertEqual(int(interp._eval_numeric("@VDU %!220")), v220)
        self.assertEqual(int(interp._eval_numeric("@vdu% !208")), 640)


class TestPiechartLabelXor(unittest.TestCase):
    def test_gcol3_vdu5_xors_slice_colours(self):
        """piechart ``GCOL 3,15`` + VDU 5 must XOR (not solid sky/15) for legibility."""
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        import numpy as np

        interp = BASICInterpreter(
            InterpreterConfig(
                dialect="bbc",
                display="pygame",
                display_locked=True,
                hold_display_open=False,
            )
        )
        interp._shutdown_display = lambda **k: None  # type: ignore[method-assign]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), patch(
            "time.sleep"
        ):
            for n, s in [
                (10, "MODE 8"),
                (20, "GCOL 0,1:RECTANGLE FILL 100,100,120,80"),
                (30, "VDU 5"),
                (40, "GCOL 3,15"),
                (50, 'MOVE 120,140:PRINT "One";'),
                (60, "END"),
            ]:
                interp.program[n] = s
            interp.run()
        px = np.asarray(interp._display._gfx.pixels)
        # 1 XOR 15 = 14 (cyan-ish index); solid mode-0 would leave only 1 and 15.
        self.assertGreater(int((px == 14).sum()), 20)


if __name__ == "__main__":
    unittest.main()
