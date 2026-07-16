import concurrent.futures
import io
import os
import re
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

# =============================================================================
# LEGACY BROAD TEST FILE (test_mini_basic.py)
# =============================================================================
# Policy (Phase 1 priority per test/README.txt):
# - NO NEW TESTS should be added here.
# - This file provides historical broad coverage.
# - All new non-graphics foundation work goes in focused files:
#     test_control_flow.py, test_compositional.py, (future) test_error_recovery.py etc.
# - Graphics, pygame, interactive, long corpus, and display-dependent tests
#   have been removed from here (or quarantined) and are listed in stuck_tests.txt.
# - Use: python -m pytest -m "phase1" ... or python test/run_regression.py
# =============================================================================



def _run_with_timeout(func, timeout_seconds: float = 15.0, *args, **kwargs):
    """Run a callable in a separate thread with a hard timeout.

    Useful for tests that execute BASIC programs containing infinite
    display loops (REPEAT ... UNTIL FALSE + WAIT) or long-running
    graphics.

    Returns the function result on success.
    Raises TimeoutError if it does not complete in time.

    Note: The worker thread is not killed on timeout (Windows does not
    support reliable thread termination). The test can still continue.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError as e:
            raise TimeoutError(
                f"Test operation timed out after {timeout_seconds}s"
            ) from e

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import (
    BASICInterpreter,
    EXIT_HOLD_CONSOLE,
    InterpreterConfig,
    ListCommand,
    _execute_repl_line,
    _script_file_kind,
    main,
    _expand_repl_abbrev,
    _get_readline_module,
    _parse_list_command,
    _parse_renumber_command,
    _print_dialect_compatibility_matrix,
    _prompt_editing_input,
    _resolve_save_filename,
    _windows_apply_arrow,
    _windows_arrow_action,
    _windows_editing_input,
)
from mini_basic.dialect_hint import parse_shebang_line, split_dialect_hints
from mini_basic.repl.completion import (
    accept_unique_completion,
    advance_tab_completion,
    compute_matches,
    configure_readline,
    file_command_context,
)
from mini_basic.repl.windows_input import windows_repl_input

_CORPUS_ROOT = _ROOT


class MiniBASICTests(unittest.TestCase):
    def run_program(self, lines, inputs=None):
        interp = BASICInterpreter()
        for line_num, statement in lines:
            interp.program[line_num] = statement

        inputs = inputs or []
        with patch('builtins.input', side_effect=inputs):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.run()
        return buf.getvalue().rstrip('\n')

    def test_factorial(self):
        lines = [
            (10, "INPUT n"),
            (20, "LET fact = 1"),
            (30, "FOR i = 1 TO n"),
            (40, "LET fact = fact * i"),
            (50, "NEXT i"),
            (60, "PRINT fact"),
            (70, "END"),
        ]
        self.assertEqual(self.run_program(lines, inputs=["5"]), "120")
        self.assertEqual(self.run_program(lines, inputs=["0"]), "1")

    def test_input_with_string_prompt(self):
        lines = [
            (10, 'INPUT "Name? ", N$'),
            (20, 'PRINT "["; N$; "]"'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines, inputs=['Alice']), 'Name? [Alice]')

    def test_input_multi_numeric_vars(self):
        lines = [
            (10, 'INPUT A, B'),
            (20, 'PRINT A + B'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines, inputs=['3,4']), '7')

    def test_input_multi_string_vars(self):
        lines = [
            (10, 'INPUT A$, B$'),
            (20, 'PRINT A$; B$'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines, inputs=['hi,there']), 'hithere')

    def test_input_spc_prompt(self):
        lines = [
            (10, 'INPUT SPC(2); "x", N$'),
            (20, 'PRINT N$'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines, inputs=['ok']), '  xok')

    def test_input_bare_uses_question_prompt(self):
        lines = [
            (10, 'INPUT n'),
            (20, 'PRINT n'),
            (30, 'END'),
        ]
        prompts: list[str] = []

        def fake_input(prompt=''):
            prompts.append(prompt)
            return '42'

        interp = BASICInterpreter()
        for line_num, statement in lines:
            interp.program[line_num] = statement
        with patch('builtins.input', side_effect=fake_input):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.run()
        self.assertEqual(prompts, ['? '])
        self.assertEqual(buf.getvalue().rstrip('\n'), '42')

    def test_input_string_var_prompt_then_var(self):
        lines = [
            (10, 'LET PROMPT$ = "Enter"'),
            (20, 'INPUT PROMPT$; ": ", N$'),
            (30, 'END'),
        ]
        interp = BASICInterpreter()
        for line_num, statement in lines:
            interp.program[line_num] = statement
        with patch('builtins.input', return_value='yes'):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.run()
        self.assertEqual(interp.str_variables['N'], 'yes')
        self.assertEqual(buf.getvalue(), 'Enter: ')

    def test_for_loop_counts(self):
        lines = [
            (10, "FOR i = 1 TO 3"),
            (20, "PRINT i"),
            (30, "NEXT i"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "1\n2\n3")

    def test_for_lowercase_to(self):
        lines = [
            (10, "for i = 1 to 2"),
            (20, "PRINT i"),
            (30, "next i"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "1\n2")

    def test_immediate_for_colon_chain(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('FOR I = 1 TO 3: PRINT I: NEXT')
        self.assertEqual(buf.getvalue().strip(), '1\n2\n3')

    def test_immediate_for_colon_chain_lowercase(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            _execute_repl_line(interp, 'for i = 1 to 3: print i : next i')
        self.assertEqual(buf.getvalue().strip(), '1\n2\n3')

    def test_immediate_for_compact_bbc_spacing(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('for i=1to3:?i: next i')
        self.assertEqual(buf.getvalue().strip(), '1\n2\n3')

    def test_immediate_time_for_next_print_chain(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate(
                'TIME=0:for I%=1 TO 3:?I%:NEXT:PRINT TIME/100'
            )
        lines = buf.getvalue().strip().split('\n')
        self.assertEqual(lines[:3], ['1', '2', '3'])
        self.assertEqual(len(lines), 4)
        self.assertGreaterEqual(float(lines[3]), 0.0)

    def test_immediate_for_next_case_mismatch_mini(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('for i = 1 to 3: print i : next I')
        self.assertEqual(buf.getvalue(), '? FOR error (NEXT I does not match i)\n')

    def test_immediate_for_float_step(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('FOR I = 1 TO 2 STEP 0.5: PRINT I: NEXT')
        self.assertEqual(buf.getvalue().strip(), '1\n1.5\n2')

    def test_program_line_for_colon_chain_with_step(self):
        lines = [
            (10, 'FOR I = 1 TO 3 STEP 0.5: PRINT I: NEXT'),
            (20, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '1\n1.5\n2\n2.5\n3')

    def test_implicit_let(self):
        lines = [
            (10, "x = 7"),
            (20, "PRINT x"),
            (30, "END"),
        ]
        self.assertEqual(self.run_program(lines), "7")

    def test_print_comma_tabs(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT 1,2,3')
        self.assertEqual(buf.getvalue(), '         1         2         3\n')

    def test_print_trailing_comma_tabs(self):
        lines = [
            (10, "FOR I = 1 TO 3"),
            (20, "PRINT I,"),
            (30, "NEXT I"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "         1         2         3")

    def test_multiplication_table_row(self):
        lines = [
            (10, "FOR col = 1 TO 5"),
            (20, "PRINT col * 2,"),
            (30, "NEXT col"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "         2         4         6         8        10")

    def test_print_comma_string_tabs(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT "a","b"')
        self.assertEqual(buf.getvalue(), 'a         b\n')

    def test_print_trailing_semicolon(self):
        lines = [
            (10, "FOR i = 1 TO 5"),
            (20, "PRINT i;"),
            (30, "NEXT i"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "12345")

    def test_cols_rows_system_vars(self):
        interp = BASICInterpreter(
            config=InterpreterConfig(display_cols=40, display_rows=24)
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT _cols, _rows')
        self.assertEqual(buf.getvalue(), '        40        24\n')

    def test_pos_vpos_after_print(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT "Hi"; POS; VPOS')
        self.assertEqual(buf.getvalue(), 'Hi20\n')
        interp2 = BASICInterpreter()
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            interp2.execute_immediate('PRINT "Hi", POS, VPOS')
        self.assertEqual(buf2.getvalue(), 'Hi        10        0\n')

    def test_mode_sets_text_dimensions(self):
        interp = BASICInterpreter()
        interp.execute_immediate('MODE 7')
        self.assertEqual(interp.config.display_cols, 40)
        self.assertEqual(interp.config.display_rows, 25)

    def test_print_comma_wraps_at_screen_width(self):
        interp = BASICInterpreter(
            config=InterpreterConfig(display_cols=20, display_rows=24)
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT 1,2,3')
        self.assertEqual(buf.getvalue(), '         1         2\n         3\n')

    def test_next_without_variable(self):
        lines = [
            (10, "FOR i = 1 TO 3"),
            (20, "PRINT i"),
            (30, "NEXT"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "1\n2\n3")

    def test_chr_print(self):
        lines = [
            (10, "PRINT CHR$(65)"),
            (20, "END"),
        ]
        self.assertEqual(self.run_program(lines), "A")

    def test_asc_print(self):
        lines = [
            (10, 'PRINT ASC("A")'),
            (20, "END"),
        ]
        self.assertEqual(self.run_program(lines), "65")

    def test_chr_asc_roundtrip(self):
        lines = [
            (10, 'PRINT CHR$(ASC("Z"))'),
            (20, "END"),
        ]
        self.assertEqual(self.run_program(lines), "Z")

    def test_asc_in_let(self):
        lines = [
            (10, 'LET x = ASC("A")'),
            (20, "PRINT x"),
            (30, "END"),
        ]
        self.assertEqual(self.run_program(lines), "65")

    def test_chr_in_loop(self):
        lines = [
            (10, "FOR i = 65 TO 67"),
            (20, "PRINT CHR$(i);"),
            (30, "NEXT"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "ABC")

    def test_mid_string_var(self):
        lines = [
            (10, 'Z$="ABC"'),
            (20, "PRINT MID$(Z$,2,1)"),
            (30, "END"),
        ]
        self.assertEqual(self.run_program(lines), "B")

    def test_mandelbrot2_palette(self):
        interp = BASICInterpreter()
        with open("mandelbrot2.bas", encoding="utf-8") as f:
            for line in f:
                parsed = interp._parse_line_number(line)
                if parsed:
                    interp.program[parsed[0]] = parsed[1]
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        out = buf.getvalue()
        self.assertIn("Finished", out)
        rows = [r for r in out.splitlines() if r and not r.startswith(("Mandelbrot", "Start", "Finished", "Time:"))]
        self.assertEqual(len(rows), 25)
        self.assertIn("O", "".join(rows))

    def test_integer_variable_print(self):
        lines = [
            (10, "N% = 42"),
            (20, "X = 42"),
            (30, "PRINT N%"),
            (40, "PRINT X"),
            (50, "END"),
        ]
        self.assertEqual(self.run_program(lines), "42\n42")

    def test_integer_separate_from_float_and_string(self):
        lines = [
            (10, "A% = 7"),
            (20, "A = 1.5"),
            (30, 'A$ = "hi"'),
            (40, "PRINT A%"),
            (50, "PRINT A"),
            (60, "PRINT A$"),
            (70, "END"),
        ]
        self.assertEqual(self.run_program(lines), "7\n1.5\nhi")

    def test_for_integer_loop(self):
        lines = [
            (10, "FOR I% = 1 TO 3"),
            (20, "PRINT I%;"),
            (30, "NEXT I%"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "123")

    def test_time_set_and_read(self):
        interp = BASICInterpreter()
        interp.execute_immediate('TIME = 500')
        self.assertGreaterEqual(interp._get_time(), 500)
        self.assertLess(interp._get_time(), 510)

    def test_time_counts_centiseconds(self):
        interp = BASICInterpreter()
        interp.execute_immediate('TIME = 0')
        time.sleep(0.08)
        self.assertGreaterEqual(interp._get_time(), 6)
        self.assertLess(interp._get_time(), 20)

    def test_time_assignment_uses_expression(self):
        interp = BASICInterpreter()
        interp.execute_immediate('TIME = 100')
        interp.execute_immediate('TIME = TIME + 25')
        self.assertGreaterEqual(interp._get_time(), 125)
        self.assertLess(interp._get_time(), 135)

    def test_repeat_until_loop(self):
        lines = [
            (10, 'N = 0'),
            (20, 'REPEAT'),
            (30, 'N = N + 1'),
            (40, 'UNTIL N >= 3'),
            (50, 'PRINT N'),
            (60, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '3')

    def test_repeat_inline_until_before_outer_until(self):
        """wheel.txt: REPEAT WAIT 0 : UNTIL T%<>TIME must not pair with outer UNTIL FALSE."""
        lines = [
            (10, 'T% = 0'),
            (20, 'REPEAT'),
            (30, 'T% = T% + 1'),
            (40, 'REPEAT WAIT 0 : UNTIL T% <> TIME'),
            (50, 'T% = TIME'),
            (60, 'UNTIL T% > 2'),
            (70, 'PRINT "done"'),
            (80, 'END'),
        ]
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp._prepare_run()
        self.assertEqual(interp._run_repeat_until.get(40), (40, 'T% <> TIME'))
        self.assertEqual(interp._run_repeat_until.get(20), (60, 'T% > 2'))
        with patch('time.sleep'):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.run()
        self.assertEqual(buf.getvalue().strip(), 'done')

    def test_exit_repeat(self):
        lines = [
            (10, 'N = 0'),
            (20, 'REPEAT'),
            (30, 'N = N + 1'),
            (40, 'IF N = 2 THEN EXIT REPEAT'),
            (50, 'UNTIL N >= 5'),
            (60, 'PRINT N'),
            (70, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '2')

    def test_exit_while(self):
        lines = [
            (10, 'N = 0'),
            (20, 'WHILE N < 10'),
            (30, 'N = N + 1'),
            (40, 'IF N = 4 THEN EXIT WHILE'),
            (50, 'PRINT N'),
            (60, 'WEND'),
            (70, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '1\n2\n3')

    def test_proc_endproc(self):
        lines = [
            (10, 'DEF PROCshow(X)'),
            (20, 'PRINT "val="; X'),
            (30, 'ENDPROC'),
            (40, 'PROCshow(7)'),
            (50, 'END'),
        ]
        self.assertEqual(self.run_program(lines), 'val=7')

    def test_break_blocked_in_bbc_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        for line_num, statement in [
            (10, 'FOR I = 1 TO 3'),
            (20, 'BREAK'),
            (30, 'NEXT I'),
            (40, 'END'),
        ]:
            interp.program[line_num] = statement
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertIn('? BREAK error', buf.getvalue())

    def test_time_persists_across_run(self):
        interp = BASICInterpreter()
        interp.execute_immediate('TIME = 9000')
        for line_num, statement in [(10, 'PRINT TIME'), (20, 'END')]:
            interp.program[line_num] = statement
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertGreaterEqual(int(buf.getvalue().strip()), 9000)

    def test_format_list_line(self):
        interp = BASICInterpreter()
        self.assertEqual(
            interp.format_list_line('print"hello";'),
            'PRINT "hello";',
        )
        self.assertEqual(
            interp.format_list_line('TIME=0:rem init'),
            'TIME = 0: REM init',
        )
        self.assertEqual(
            interp.format_list_line('C=X*229/100'),
            'C = X * 229 / 100',
        )
        self.assertEqual(
            interp.format_list_line('IF ((P*P)+(Q*Q))>=5 GOTO 280'),
            'IF ((P * P) + (Q * Q)) >= 5 GOTO 280',
        )
        self.assertEqual(
            interp.format_list_line('FOR Y = -12 TO 12'),
            'FOR Y = -12 TO 12',
        )
        self.assertEqual(
            interp.format_list_line('Z$=".,\'~=+:;*%&$OXB#@ "'),
            'Z$ = ".,\'~=+:;*%&$OXB#@ "',
        )

    def test_list_output_formatted(self):
        interp = BASICInterpreter()
        interp.set_program_line(100, 'print"hi"')
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program()
        self.assertIn('100 PRINT "hi"', buf.getvalue())

    def test_indent_preserved_on_list(self):
        interp = BASICInterpreter()
        interp.set_program_line(20, 'PRINT "in loop"', indent=4)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program()
        line = buf.getvalue().splitlines()[0]
        match = re.match(r'^\s*20\s(\s*)PRINT "in loop"', line)
        self.assertIsNotNone(match)
        self.assertEqual(len(match.group(1)), 4)

    def test_parse_line_number_indent_after_number(self):
        interp = BASICInterpreter()
        self.assertEqual(
            interp._parse_line_number('    20   PRINT "x"'),
            (20, 'PRINT "x"', 2),
        )
        self.assertEqual(
            interp._parse_line_number('  10 FOR I=1 TO 2'),
            (10, 'FOR I=1 TO 2', 0),
        )

    def test_list_risc_os_style_indent_after_line_number(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        for text in [
            '    10 FOR N%=1 TO 10',
            '    20   PRINT "vol";FNvolume(N%)',
            '    30   NEXT N%',
            '    40 END',
        ]:
            interp.set_program_line(*interp._parse_line_number(text))
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program()
        lines = buf.getvalue().splitlines()

        def stmt_indent(line: str) -> int:
            match = re.match(r'^\s*\d+\s(\s*)', line)
            return len(match.group(1)) if match else 0

        for_line = next(line for line in lines if 'FOR N' in line)
        print_line = next(line for line in lines if 'PRINT "vol"' in line)
        next_line = next(line for line in lines if 'NEXT N' in line)
        self.assertEqual(stmt_indent(for_line), 0)
        self.assertGreater(stmt_indent(print_line), stmt_indent(for_line))
        self.assertEqual(stmt_indent(print_line), stmt_indent(next_line))

    def test_parse_list_command_range(self):
        cmd = _parse_list_command('LIST 270-330')
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.start_line, 270)
        self.assertEqual(cmd.end_line, 330)
        self.assertEqual(cmd.mode, 'standard')

    def test_parse_list_command_pretty_range(self):
        cmd = _parse_list_command('LIST PRETTY 270-330')
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.mode, 'pretty')
        self.assertEqual(cmd.start_line, 270)
        self.assertEqual(cmd.end_line, 330)

    def test_parse_list_command_from_line(self):
        cmd = _parse_list_command('LIST 330')
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.start_line, 330)
        self.assertIsNone(cmd.end_line)

    def test_parse_list_command_invalid_range(self):
        self.assertIsNone(_parse_list_command('LIST FOO'))

    def test_list_line_range(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, 'PRINT 1')
        interp.set_program_line(20, 'PRINT 2')
        interp.set_program_line(30, 'PRINT 3')
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program(ListCommand(start_line=20, end_line=30))
        output = buf.getvalue()
        self.assertNotIn('    10 ', output)
        self.assertIn('    20 ', output)
        self.assertIn('    30 ', output)

    def test_goto_label(self):
        lines = [
            (10, "GOTO DONE"),
            (20, 'PRINT "skip"'),
            (30, "DONE: PRINT \"ok\""),
            (40, "END"),
        ]
        interp = BASICInterpreter()
        for line_num, statement in lines:
            interp.set_program_line(line_num, statement)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertEqual(buf.getvalue().strip(), "ok")

    def test_list_pretty_splits_colons(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, "A=1:B=2")
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program('pretty')
        out = buf.getvalue()
        self.assertIn("A = 1", out)
        self.assertIn("B = 2", out)
        self.assertGreaterEqual(out.count("\n"), 1)

    def test_list_pretty_closer_aligns_with_opener(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, "FOR I = 1 TO 2")
        interp.set_program_line(20, "WHILE I < 3")
        interp.set_program_line(30, "IF I = 1 THEN")
        interp.set_program_line(40, 'PRINT "hi"')
        interp.set_program_line(50, "ELSE")
        interp.set_program_line(60, 'PRINT "bye"')
        interp.set_program_line(70, "ENDIF")
        interp.set_program_line(80, "WEND")
        interp.set_program_line(90, "NEXT I")
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program('pretty')
        lines = buf.getvalue().splitlines()

        def leading_spaces(text):
            return len(text) - len(text.lstrip())

        def find_line(substring):
            return next(line for line in lines if substring in line)

        self.assertEqual(leading_spaces(find_line('FOR I')), leading_spaces(find_line('NEXT I')))
        self.assertEqual(leading_spaces(find_line('WHILE')), leading_spaces(find_line('WEND')))
        self.assertEqual(leading_spaces(find_line('IF I = 1')), leading_spaces(find_line('ENDIF')))
        self.assertEqual(leading_spaces(find_line('IF I = 1')), leading_spaces(find_line('ELSE')))

    def test_list_refs_structured_without_goto_has_no_numbers(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, "FOR I = 1 TO 2")
        interp.set_program_line(20, "WHILE I < 3")
        interp.set_program_line(30, "IF I = 1 THEN")
        interp.set_program_line(40, 'PRINT "hi"')
        interp.set_program_line(50, "ENDIF")
        interp.set_program_line(60, "WEND")
        interp.set_program_line(70, "NEXT I")
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program('refs')
        text = buf.getvalue()
        self.assertIn('PRINT "hi"', text)
        self.assertNotIn("    10 ", text)
        self.assertNotIn("    40 ", text)

    def test_list_refs_preserves_existing_indent(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, 'PRINT "a"')
        interp.set_program_line(20, 'FOR I = 1 TO 2', indent=4)
        interp.set_program_line(30, 'PRINT I', indent=8)
        interp.set_program_line(40, 'NEXT I', indent=4)

        def stmt_indent_after_marker(line: str) -> int:
            numbered = re.match(r'^\s*\d+\s(\s*)', line)
            if numbered:
                return len(numbered.group(1))
            refs = re.match(r'^    (\s*)', line)
            return len(refs.group(1)) if refs else 0

        def find_line(lines, substring):
            return next(line for line in lines if substring in line)

        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program('standard')
        standard_lines = buf.getvalue().splitlines()

        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program('refs')
        refs_lines = buf.getvalue().splitlines()

        self.assertEqual(
            stmt_indent_after_marker(find_line(standard_lines, 'PRINT I')),
            stmt_indent_after_marker(find_line(refs_lines, 'PRINT I')),
        )
        self.assertEqual(
            stmt_indent_after_marker(find_line(standard_lines, 'FOR I = 1 TO 2')),
            stmt_indent_after_marker(find_line(refs_lines, 'FOR I = 1 TO 2')),
        )

    def test_list_refs_blank_line_before_def(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.set_program_line(10, 'PRINT "main"')
        interp.set_program_line(20, 'END')
        interp.set_program_line(100, 'DEF FNfact(n)')
        interp.set_program_line(110, 'IF n<2 THEN')
        interp.set_program_line(120, '=1')
        interp.set_program_line(130, 'ELSE')
        interp.set_program_line(140, '=n*FNfact(n-1)')
        interp.set_program_line(150, 'END IF')
        interp.set_program_line(160, 'END DEF')
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program('refs')
        lines = buf.getvalue().splitlines()
        end_idx = next(i for i, line in enumerate(lines) if line.strip() == 'END')
        def_idx = next(i for i, line in enumerate(lines) if 'DEF FNFACT' in line)
        self.assertGreater(def_idx, end_idx)
        self.assertEqual(lines[def_idx - 1], '')

    def test_list_refs_shows_goto_targets_only(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, "PRINT 1")
        interp.set_program_line(20, "GOTO 40")
        interp.set_program_line(30, "PRINT 2")
        interp.set_program_line(40, "END")
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program('refs')
        text = buf.getvalue()
        self.assertIn("    40 ", text)
        self.assertNotIn("    20 ", text)
        self.assertNotIn("    10 ", text)
        self.assertNotIn("    30 ", text)

    def test_list_refs_shows_label_gosub_target(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, "GOSUB SUB")
        interp.set_program_line(20, "END")
        interp.set_program_line(100, "SUB: PRINT 1")
        interp.set_program_line(110, "RETURN")
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program('refs')
        text = buf.getvalue()
        self.assertIn("   100 ", text)
        self.assertNotIn("    10 ", text)

    def test_for_break(self):
        lines = [
            (10, "FOR I = 1 TO 5"),
            (20, "IF I = 3 THEN BREAK"),
            (30, "PRINT I"),
            (40, "NEXT I"),
            (50, 'PRINT "done"'),
            (60, "END"),
        ]
        self.assertEqual(self.run_program(lines), "1\n2\ndone")

    def test_for_continue(self):
        lines = [
            (10, "FOR I = 1 TO 4"),
            (20, "IF I = 2 THEN CONTINUE"),
            (30, "PRINT I"),
            (40, "NEXT I"),
            (50, "END"),
        ]
        self.assertEqual(self.run_program(lines), "1\n3\n4")

    def test_instr(self):
        lines = [
            (10, 'LET A$ = "HELLO WORLD"'),
            (20, 'PRINT INSTR(A$, "WORLD")'),
            (30, 'PRINT INSTR(A$, "X")'),
            (40, 'PRINT INSTR(A$, "L", 3)'),
            (50, "END"),
        ]
        self.assertEqual(self.run_program(lines), "7\n0\n3")

    def test_while_loop(self):
        lines = [
            (10, "LET N = 1"),
            (20, "WHILE N <= 3"),
            (30, "PRINT N"),
            (40, "LET N = N + 1"),
            (50, "WEND"),
            (60, "END"),
        ]
        self.assertEqual(self.run_program(lines), "1\n2\n3")

    def test_while_break_continue(self):
        lines = [
            (10, "LET N = 0"),
            (20, "WHILE N < 5"),
            (30, "LET N = N + 1"),
            (40, "IF N = 2 THEN CONTINUE"),
            (50, "IF N = 4 THEN BREAK"),
            (60, "PRINT N"),
            (70, "WEND"),
            (80, "END"),
        ]
        self.assertEqual(self.run_program(lines), "1\n3")

    def test_break_labeled_for(self):
        lines = [
            (10, "OUTER: FOR I = 1 TO 3"),
            (20, "FOR J = 1 TO 5"),
            (30, "IF J = 3 THEN BREAK OUTER"),
            (40, "PRINT I; J;"),
            (50, "NEXT J"),
            (60, "NEXT I"),
            (70, 'PRINT "done"'),
            (80, "END"),
        ]
        self.assertEqual(self.run_program(lines), "1112done")

    def test_continue_labeled_for(self):
        lines = [
            (10, "OUTER: FOR I = 1 TO 3"),
            (20, "FOR J = 1 TO 3"),
            (30, "IF J = 2 THEN CONTINUE OUTER"),
            (40, "PRINT I; J;"),
            (50, "NEXT J"),
            (60, "PRINT I;"),
            (70, "NEXT I"),
            (80, "END"),
        ]
        self.assertEqual(self.run_program(lines), "112131")

    def test_break_labeled_while(self):
        lines = [
            (10, "LET I = 0"),
            (20, "OUTER: WHILE I < 3"),
            (30, "LET I = I + 1"),
            (40, "LET J = 0"),
            (50, "WHILE J < 5"),
            (60, "LET J = J + 1"),
            (70, "IF J = 2 THEN BREAK OUTER"),
            (80, "PRINT I; J;"),
            (90, "WEND"),
            (100, "WEND"),
            (110, 'PRINT "done"'),
            (120, "END"),
        ]
        self.assertEqual(self.run_program(lines), "11done")

    def test_break_unknown_label(self):
        lines = [
            (10, "FOR I = 1 TO 2"),
            (20, "BREAK MISSING"),
            (30, "NEXT I"),
            (40, "END"),
        ]
        out = self.run_program(lines)
        self.assertIn("? BREAK label not found", out)

    def test_system_variables_set_and_print(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('_optimization_level = 1')
            interp.execute_immediate('_print_line_buffering = 1')
            interp.execute_immediate('PRINT _optimization_level')
            interp.execute_immediate('PRINT _print_line_buffering')
        self.assertEqual(buf.getvalue().strip(), '1\n1')
        self.assertEqual(interp.config.optimization_level, 1)
        self.assertTrue(interp.config.print_line_buffering)

    def test_bigint_system_variable_default_on(self):
        interp = BASICInterpreter()
        self.assertTrue(interp.config.bigint_enabled)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT _bigint')
        self.assertEqual(buf.getvalue().strip(), '1')

    def test_bigint_off_stores_percent_var_as_float(self):
        interp = BASICInterpreter()
        interp.execute_immediate('LET _bigint = 0')
        interp.execute_immediate('LET x% = 9007199254740993')
        self.assertIsInstance(interp.int_variables['x'], float)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT x%')
        printed = buf.getvalue().strip()
        self.assertNotEqual(printed, '9007199254740993')

    def test_bigint_on_keeps_large_percent_int(self):
        interp = BASICInterpreter()
        value = '123456789012345'
        interp.execute_immediate(f'LET x% = {value}')
        self.assertIsInstance(interp.int_variables['x'], int)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT x%')
        self.assertEqual(buf.getvalue().strip(), value)

    def test_bigint_off_factorial_uses_float_precision(self):
        lines = [
            (10, 'LET _bigint = 0'),
            (20, 'DEF FNfact%(n%)'),
            (30, 'IF n%<1 THEN'),
            (40, '=1'),
            (50, 'ELSE'),
            (60, '=FNfact%(n%-1)*n%'),
            (70, 'ENDIF'),
            (80, 'END DEF'),
            (90, 'PRINT FNfact%(69)'),
            (100, 'END'),
        ]
        buf = io.StringIO()
        interp = BASICInterpreter()
        interp._program_stdout = buf
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp.run()
        out = buf.getvalue().strip()
        self.assertEqual(
            out,
            '171122452428141297375735434272073448876652721480628511030304905066123383956194496253690059725733888',
        )

    def test_epsilon_system_variable(self):
        import sys

        from mini_basic.util.float_info import discover_machine_epsilon, machine_epsilon

        interp = BASICInterpreter()
        self.assertEqual(interp.machine_epsilon, machine_epsilon())
        self.assertEqual(interp.machine_epsilon, discover_machine_epsilon())
        self.assertEqual(interp.machine_epsilon, sys.float_info.epsilon)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT _epsilon')
        self.assertEqual(float(buf.getvalue().strip()), interp.machine_epsilon)

    def test_epsilon_readonly(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('_epsilon = 1')
        self.assertIn('System variable error', buf.getvalue())

    def test_find_epsilon_example_matches_interpreter(self):
        import os

        path = os.path.join(_ROOT, 'examples', 'mini', 'find_epsilon.bas')
        interp = BASICInterpreter()
        interp.load(path, announce=False)
        buf = io.StringIO()
        interp._program_stdout = buf
        interp.run()
        out = buf.getvalue()
        self.assertIn('Match!', out)
        self.assertIn('Found by loop:', out)
        self.assertIn('Interpreter  :', out)

    def test_float_platform_system_variables(self):
        import sys

        from mini_basic.util.float_info import probe_float_platform

        platform = probe_float_platform()
        interp = BASICInterpreter()
        self.assertEqual(interp.float_decimal_digits, platform.decimal_digits)
        self.assertEqual(interp.float_mantissa_digits, platform.mantissa_digits)
        self.assertEqual(interp.float_radix, platform.radix)
        self.assertEqual(interp.ieee754_binary64, 1 if platform.is_ieee754_binary64 else 0)
        self.assertEqual(interp.float_decimal_digits, sys.float_info.dig)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT _float_digits, _float_mantissa, _float_radix, _ieee754')
        parts = buf.getvalue().strip().split()
        self.assertEqual(int(parts[0]), platform.decimal_digits)
        self.assertEqual(int(parts[1]), platform.mantissa_digits)
        self.assertEqual(int(parts[2]), platform.radix)
        self.assertEqual(int(parts[3]), 1 if platform.is_ieee754_binary64 else 0)

    def test_float_platform_system_variables_readonly(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('_float_digits = 1')
        self.assertIn('System variable error', buf.getvalue())

    def test_near_function(self):
        from mini_basic.util.float_info import machine_epsilon, near_equal

        interp = BASICInterpreter()
        eps = machine_epsilon()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT NEAR(1, 1 + _epsilon / 2)')
        self.assertEqual(buf.getvalue().strip(), '-1')
        self.assertTrue(near_equal(1.0, 1.0 + eps / 2))
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT NEAR(1, 1 + _epsilon * 2)')
        self.assertEqual(buf.getvalue().strip(), '0')
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT NEAR(0, 1E-10, 1E-9)')
        self.assertEqual(buf.getvalue().strip(), '-1')

    def test_nearsig_function(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT NEARSIG(3.14159265, 3.14159, 6)')
        self.assertEqual(buf.getvalue().strip(), '-1')
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT NEARSIG(3.14159265, 3.14159, 7)')
        self.assertEqual(buf.getvalue().strip(), '0')

    def test_near_float_example_runs(self):
        import os

        path = os.path.join(_ROOT, 'examples', 'mini', 'near_float.bas')
        interp = BASICInterpreter()
        interp.load(path, announce=False)
        buf = io.StringIO()
        interp._program_stdout = buf
        interp.run()
        out = buf.getvalue()
        self.assertIn('Decimal digits', out)
        self.assertIn('NEAR(1, 1+eps/2)', out)
        self.assertIn('NEAR(1, 1+2*eps)', out)
        self.assertIn('NEARSIG(pi, 3.14159, 6)', out)

    def test_user_variables_cannot_start_with_underscore(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('_user = 1')
        self.assertIn('System variable error', buf.getvalue())

    def test_unknown_system_variable_rejected(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('_not_a_real_setting = 1')
        self.assertIn('System variable error', buf.getvalue())

    def test_print_line_buffering_matches_direct_print(self):
        lines = [
            (10, 'FOR I = 1 TO 3'),
            (20, 'PRINT I;",";'),
            (30, 'NEXT I'),
            (40, 'PRINT "done"'),
            (50, 'END'),
        ]

        direct = BASICInterpreter(InterpreterConfig(print_line_buffering=False))
        buffered = BASICInterpreter(InterpreterConfig(print_line_buffering=True))
        for line_num, statement in lines:
            direct.set_program_line(line_num, statement)
            buffered.set_program_line(line_num, statement)

        buf_direct = io.StringIO()
        buf_buffered = io.StringIO()
        direct._program_stdout = buf_direct
        buffered._program_stdout = buf_buffered
        direct.run()
        buffered.run()

        self.assertEqual(buf_direct.getvalue(), buf_buffered.getvalue())

    def test_optimization_level_zero_runs_program(self):
        lines = [
            (10, 'LET n = 5'),
            (20, 'LET fact = 1'),
            (30, 'FOR i = 1 TO n'),
            (40, 'LET fact = fact * i'),
            (50, 'NEXT i'),
            (60, 'PRINT fact'),
            (70, 'END'),
        ]
        interp = BASICInterpreter(InterpreterConfig(optimization_level=0))
        for line_num, statement in lines:
            interp.set_program_line(line_num, statement)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertEqual(buf.getvalue().strip(), '120')

    def test_compiled_expr_matches_slow_path(self):
        interp = BASICInterpreter()
        interp.int_variables['A'] = 10
        interp.int_variables['B'] = 3
        interp.variables['X'] = 2.5
        interp.variables['Y'] = 4.0
        cases = [
            '10 MOD 3',
            'A% MOD B%',
            'X * Y + 1',
            '(X * X) + (Y * Y) >= 5',
        ]
        for expr in cases:
            slow = interp._eval_numeric_slow(expr) if '%' in expr or 'MOD' in expr else None
            if slow is None and '>=' not in expr:
                slow = interp._eval_numeric_slow(expr)
            if '>=' in expr:
                self.assertEqual(
                    interp._get_compiled_expr(expr, is_condition=True).eval_condition(interp),
                    interp._eval_condition(expr),
                )
            else:
                self.assertEqual(
                    interp._get_compiled_expr(expr, is_condition=False).eval_numeric(interp),
                    interp._eval_numeric_slow(expr),
                )

    def test_mod_and_division(self):
        interp = BASICInterpreter()
        self.assertEqual(interp.eval_expr("10 MOD 3"), 1.0)
        self.assertEqual(interp.eval_expr("10 % 3"), 1.0)
        self.assertAlmostEqual(interp.eval_expr("10 / 3"), 10 / 3)
        self.assertEqual(interp.eval_expr("10 // 3"), 3.0)
        self.assertEqual(interp.eval_expr("10 \\ 3"), 3.0)
        interp.int_variables["A"] = 10
        interp.int_variables["B"] = 3
        self.assertEqual(interp.eval_expr("A% MOD B%"), 1.0)
        self.assertAlmostEqual(interp.eval_expr("A% / B%"), 10 / 3)
        self.assertEqual(interp.eval_expr("A% \\ B%"), 3.0)

    def test_integer_truncates_on_assign(self):
        lines = [
            (10, "N% = 9.9"),
            (20, "PRINT N%"),
            (30, "END"),
        ]
        self.assertEqual(self.run_program(lines), "9")

    def test_auto_entry(self):
        interp = BASICInterpreter()
        with patch('mini_basic.runtime._prompt_editing_input', side_effect=['PRINT "a"', 'PRINT "b"', '']):
            interp.auto_entry(10, 10)
        self.assertEqual(interp.program[10], 'PRINT "a"')
        self.assertEqual(interp.program[20], 'PRINT "b"')

    def test_def_proc_block_entry_at_prompt(self):
        interp = BASICInterpreter()
        with patch('mini_basic.runtime._prompt_editing_input', side_effect=[
            '  IF N <= 1 THEN PRINT ACC : ENDPROC',
            '  PROCfact(N - 1, N * ACC)',
            'ENDPROC',
            '',
        ]):
            interp.def_block_entry('DEF PROCfact(N, ACC)')
        self.assertEqual(interp.program[10], 'DEF PROCfact(N, ACC)')
        self.assertEqual(interp.program[20], 'IF N <= 1 THEN PRINT ACC : ENDPROC')
        self.assertEqual(interp.program[30], 'PROCfact(N - 1, N * ACC)')
        self.assertEqual(interp.program[40], 'ENDPROC')
        self.assertIn('fact', interp.user_procedures)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PROCfact(5, 1)')
        self.assertEqual(buf.getvalue().strip(), '120')

    def test_proc_immediate_without_run(self):
        interp = BASICInterpreter()
        for line_num, statement in [
            (10, 'DEF PROCshow(X)'),
            (20, 'PRINT "val="; X'),
            (30, 'ENDPROC'),
        ]:
            interp.set_program_line(line_num, statement)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PROCshow(7)')
        self.assertEqual(buf.getvalue().strip(), 'val=7')

    def test_def_proc_block_entry_via_repl_line(self):
        interp = BASICInterpreter()
        with patch('mini_basic.runtime._prompt_editing_input', side_effect=[
            'PRINT "hi"',
            'ENDPROC',
            '',
        ]):
            _execute_repl_line(interp, 'DEF PROChello')
        self.assertEqual(interp.program[10], 'DEF PROChello')
        self.assertEqual(interp.program[20], 'PRINT "hi"')
        self.assertEqual(interp.program[30], 'ENDPROC')

    def test_def_fn_block_entry_at_prompt(self):
        interp = BASICInterpreter()
        with patch('mini_basic.runtime._prompt_editing_input', side_effect=[
            'IF n <= 1 THEN',
            '  = 1',
            'ELSE',
            '  = n * FNfact(n - 1)',
            'ENDIF',
            'END DEF',
            '',
        ]):
            interp.def_block_entry('DEF FNfact(n)')
        self.assertEqual(interp.program[10], 'DEF FNfact(n)')
        self.assertIn('fact', interp.user_functions)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT FNfact(5)')
        self.assertEqual(buf.getvalue().strip(), '120')

    def test_def_block_entry_preserves_indent_on_list(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        with patch('mini_basic.runtime._prompt_editing_input', side_effect=[
            '    IF n<2 THEN',
            '        = 1',
            '    ELSE',
            '        = n * FNfact(n - 1)',
            '    END IF',
            'END DEF',
            '',
        ]):
            interp.def_block_entry('DEF FNfact(n)')
        self.assertEqual(interp.line_indent.get(20), 4)
        self.assertEqual(interp.line_indent.get(30), 8)

        def stmt_indent(line: str) -> int:
            match = re.match(r'^\s*\d+\s(\s*)', line)
            return len(match.group(1)) if match else 0

        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program()
        standard = buf.getvalue().splitlines()
        if_line = next(line for line in standard if 'IF N<2' in line)
        eq_line = next(line for line in standard if '= 1' in line)
        self.assertEqual(stmt_indent(if_line), 4)
        self.assertEqual(stmt_indent(eq_line), 8)

        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program('pretty')
        pretty = buf.getvalue().splitlines()
        def_line = next(line for line in pretty if 'DEF FNFACT' in line)
        pretty_if = next(line for line in pretty if 'IF N<2' in line)
        self.assertEqual(stmt_indent(def_line), 0)
        self.assertGreaterEqual(stmt_indent(pretty_if), 4)

    def _define_recursive_fact_fn(self, interp: BASICInterpreter) -> None:
        with patch('mini_basic.runtime._prompt_editing_input', side_effect=[
            'IF n <= 1 THEN',
            '  = 1',
            'ELSE',
            '  = n * FNfact(n - 1)',
            'ENDIF',
            'END DEF',
            '',
        ]):
            interp.def_block_entry('DEF FNfact(n)')

    def test_def_fn_deep_recursion_does_not_echo(self):
        interp = BASICInterpreter()
        self._define_recursive_fact_fn(interp)
        value = interp.eval_print_value('FNfact(100)')
        self.assertFalse(value.startswith('FNfact'))
        import math
        self.assertEqual(value, str(math.factorial(100)))
        self.assertEqual(interp.eval_print_value('FNfact(10)'), '3628800')

    def test_float_wraps_expanded_fn_call(self):
        interp = BASICInterpreter()
        self._define_recursive_fact_fn(interp)
        value = interp.eval_print_value('float(FNfact(10))')
        self.assertEqual(value, '3628800')
        sng = interp.eval_print_value('SNG(FNfact(10))')
        self.assertEqual(sng, '3628800')
        deep = interp.eval_print_value('float(FNfact(100))')
        self.assertFalse(deep.startswith('float'))
        self.assertTrue(deep.startswith('933262154439441'))

    def _patch_noninteractive_repl(self, side_effect):
        return patch(
            'mini_basic.repl.windows_input.windows_repl_input',
            side_effect=side_effect,
        )

    def test_one_line_def_fn_still_immediate_not_block_entry(self):
        interp = BASICInterpreter()
        with patch('mini_basic.runtime._prompt_editing_input') as prompt:
            buf = io.StringIO()
            with redirect_stdout(buf):
                _execute_repl_line(interp, 'DEF FNdouble(x) = x * 2')
            prompt.assert_not_called()
        self.assertNotIn(10, interp.program)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT FNdouble(5)')
        self.assertEqual(buf.getvalue().strip(), '10')

    def test_def_proc_block_entry_rejected_in_mits(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mits', strict_dialect=True))
        with patch('mini_basic.runtime._prompt_editing_input') as prompt:
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.def_block_entry('DEF PROChello')
            prompt.assert_not_called()
        self.assertNotIn(10, interp.program)
        self.assertIn('not allowed in mits', buf.getvalue())

    def test_edit_line_delete(self):
        interp = BASICInterpreter()
        interp.program[50] = 'PRINT "old"'
        with patch('mini_basic.runtime._prompt_editing_input', return_value=''):
            interp.edit_line(50)
        self.assertNotIn(50, interp.program)

    def test_repl_bare_line_number_deletes_program_line(self):
        interp = BASICInterpreter()
        interp.program[30] = 'PRINT "gone"'
        interp.program[40] = 'PRINT "stay"'
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertTrue(_execute_repl_line(interp, '30'))
        self.assertNotIn(30, interp.program)
        self.assertIn(40, interp.program)
        self.assertEqual(buf.getvalue(), '')

    def test_repl_bare_line_number_missing_line_is_silent(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertTrue(_execute_repl_line(interp, '30'))
        self.assertEqual(buf.getvalue(), '')

    def test_prompt_editing_input_prefills_program_line(self):
        fake_readline = MagicMock()
        fake_readline.get_current_history_length.return_value = 1
        fake_readline.get_history_item.return_value = 'RUN'
        with patch('mini_basic.runtime.sys.platform', 'linux'):
            with patch('mini_basic.runtime._get_readline_module', return_value=fake_readline):
                with patch('builtins.input', return_value='PRINT "new"'):
                    result = _prompt_editing_input('50 ', 'PRINT "old"')
        self.assertEqual(result, 'PRINT "new"')
        fake_readline.clear_history.assert_called()
        fake_readline.add_history.assert_any_call('PRINT "old"')
        prefill_hook = fake_readline.set_startup_hook.call_args_list[0][0][0]
        prefill_hook()
        fake_readline.insert_text.assert_called_with('PRINT "old"')

    def test_edit_line_uses_program_line_as_default(self):
        interp = BASICInterpreter()
        interp.program[50] = 'PRINT "old"'
        with patch('mini_basic.runtime._prompt_editing_input', return_value='PRINT "new"') as prompt:
            interp.edit_line(50)
        prompt.assert_called_once_with('50 ', 'PRINT "old"')
        self.assertEqual(interp.program[50], 'PRINT "new"')

    def test_edit_line_preserves_indent(self):
        interp = BASICInterpreter()
        interp.set_program_line(330, 'PRINT "Done!"', indent=6)
        with patch('mini_basic.runtime._prompt_editing_input', return_value='PRINT "Done!"'):
            interp.edit_line(330)
        self.assertEqual(interp.line_indent.get(330), 6)
        self.assertEqual(interp.program[330], 'PRINT "Done!"')

    def test_edit_line_prefill_includes_indent(self):
        interp = BASICInterpreter()
        interp.set_program_line(330, 'PRINT "Done!"', indent=6)
        with patch('mini_basic.runtime._prompt_editing_input', return_value='PRINT "Done!"') as prompt:
            interp.edit_line(330)
        prompt.assert_called_once_with('330 ', '      PRINT "Done!"')

    def test_windows_arrow_action_parses_vt100_right(self):
        keys = iter(['[', 'C'])
        self.assertEqual(_windows_arrow_action(lambda: next(keys), '\x1b'), 'right')

    def test_windows_editing_input_vt100_right_fills_default(self):
        keys = list('\x1b[C\n')
        result = _windows_editing_input(
            '330 ',
            'PRINT "Finished"',
            getwch=lambda: keys.pop(0),
        )
        self.assertEqual(result, 'PRINT "Finished"')

    def test_windows_editing_input_keeps_quoted_line_on_enter(self):
        keys = list('\n')
        result = _windows_editing_input(
            '330 ',
            'PRINT "Finished"',
            getwch=lambda: keys.pop(0),
        )
        self.assertEqual(result, 'PRINT "Finished"')

    def test_windows_editing_input_backspace_after_left_arrow(self):
        keys = list('\x1b[D\x1b[D\x1b[D\x7f\n')
        result = _windows_editing_input(
            '330 ',
            'PRINT "Finished"',
            getwch=lambda: keys.pop(0),
        )
        self.assertEqual(result, 'PRINT "Finised"')

    def test_windows_editing_input_backspace_from_end(self):
        keys = list('\x7f\x7f\n')
        result = _windows_editing_input(
            '330 ',
            'PRINT "Finished"',
            getwch=lambda: keys.pop(0),
        )
        self.assertEqual(result, 'PRINT "Finishe')

    def test_prompt_editing_input_prefers_windows_editor(self):
        with patch('mini_basic.runtime.sys.platform', 'win32'):
            with patch('mini_basic.runtime.sys.stdin.isatty', return_value=True):
                with patch('mini_basic.runtime._windows_editing_input', return_value='PRINT 1') as win_edit:
                    result = _prompt_editing_input('10 ', 'PRINT 0')
        self.assertEqual(result, 'PRINT 1')
        win_edit.assert_called_once_with('10 ', 'PRINT 0')

    def test_edit_program(self):
        interp = BASICInterpreter()
        with patch('builtins.input', side_effect=['10 PRINT 1', '20 PRINT 2', '']):
            interp.edit_program()
        self.assertEqual(interp.program[10], 'PRINT 1')
        self.assertEqual(interp.program[20], 'PRINT 2')

    def test_gosub_return(self):
        lines = [
            (10, "GOSUB 100"),
            (20, 'PRINT "done"'),
            (30, "END"),
            (100, 'PRINT "sub"'),
            (110, "RETURN"),
        ]
        self.assertEqual(self.run_program(lines), "sub\ndone")

    def test_gosub_colon_resume(self):
        lines = [
            (10, 'PRINT "a";: GOSUB 100: PRINT "c"'),
            (20, "END"),
            (100, 'PRINT "b";'),
            (110, "RETURN"),
        ]
        self.assertEqual(self.run_program(lines), "abc")

    def test_fg_reset_contains_escape(self):
        lines = [
            (10, 'PRINT FG$(1);"X";RESET$()'),
            (20, "END"),
        ]
        out = self.run_program(lines)
        self.assertIn("X", out)
        self.assertIn("\033[", out)

    def test_rgb_function(self):
        interp = BASICInterpreter()
        value = interp.eval_print_value('RGB$(10,20,30)')
        self.assertEqual(value, "\033[38;2;10;20;30m")

    def test_mandelbrot_color_only_perf_not_regressed(self):
        """WHILE comparisons must stay near snapshot speed (compiled arith path)."""
        interp = BASICInterpreter(InterpreterConfig(optimization_level=2))
        interp.load('examples/graphics/mandelbrot/mandelbrot_color_only.bas')
        started = time.perf_counter()
        buf = io.StringIO()
        interp._program_stdout = buf
        interp.run()
        elapsed = time.perf_counter() - started
        self.assertIn('Finished', buf.getvalue())
        self.assertLess(elapsed, 12.0, f'mandelbrot_color_only took {elapsed:.2f}s')

    def test_mandelbrot_fp_variants_have_consistent_timing(self):
        """mandelbrot2, color ANSI, and color-only share the same core loop."""
        scripts = (
            'examples/graphics/mandelbrot/mandelbrot2.bas',
            'examples/graphics/mandelbrot/mandelbrot_color.bas',
            'examples/graphics/mandelbrot/mandelbrot_color_only.bas',
        )
        elapsed: list[float] = []
        for path in scripts:
            interp = BASICInterpreter(InterpreterConfig(optimization_level=2))
            interp.load(path)
            buf = io.StringIO()
            interp._program_stdout = buf
            started = time.perf_counter()
            interp.run()
            elapsed.append(time.perf_counter() - started)
            self.assertIn('Finished', buf.getvalue())
        fastest = min(elapsed)
        slowest = max(elapsed)
        self.assertLessEqual(
            slowest,
            fastest * 1.15,
            f'timing spread too wide: {list(zip(scripts, elapsed))}',
        )

    def test_mandelbrot_color_only_single_glyph(self):
        interp = BASICInterpreter()
        with open("examples/graphics/mandelbrot/mandelbrot_color_only.bas", encoding="utf-8") as f:
            for line in f:
                parsed = interp._parse_line_number(line)
                if parsed:
                    interp.program[parsed[0]] = parsed[1]
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        out = buf.getvalue()
        self.assertIn("Finished", out)
        def plain(line: str) -> str:
            return re.sub(r'\033\[[0-9;]*m', '', line)

        rows = [
            r for r in out.splitlines()
            if r and not plain(r).startswith(("Mandelbrot", "Start", "Finished", "Time:"))
        ]
        self.assertEqual(len(rows), 25)
        joined = ''.join(rows)
        visible = re.sub(r'\033\[[0-9;]*m', '', joined)
        self.assertEqual(set(visible), {' '})
        self.assertIn('\x1b[48;5;', joined)
        self.assertIn('\x1b[48;5;232m', joined)
        self.assertGreater(len(visible), 1000)

    def test_mandelbrot_small(self):
        interp = BASICInterpreter()
        with open("mandelbrot_small.bas", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    m = re.match(r'^(\d+)\s+(.*)', line)
                    if m:
                        interp.program[int(m.group(1))] = m.group(2)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        rows = [row for row in buf.getvalue().splitlines() if row]
        self.assertEqual(len(rows), 12)
        self.assertEqual(len(rows[0]), 40)
        joined = "".join(rows)
        self.assertGreater(len(set(joined)), 4)
        self.assertGreater(joined.count(","), 50)

    def test_run_resets_state(self):
        lines = [
            (10, "LET x = 1"),
            (20, "PRINT x"),
            (30, "END"),
        ]
        interp = BASICInterpreter()
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp.variables["x"] = 99
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertEqual(buf.getvalue().strip(), "1")

    def test_structured_if_else(self):
        lines = [
            (10, "LET X = 1"),
            (20, "IF X = 1 THEN"),
            (30, 'PRINT "one"'),
            (40, "ELSE"),
            (50, 'PRINT "other"'),
            (60, "ENDIF"),
            (70, "END"),
        ]
        self.assertEqual(self.run_program(lines), "one")

    def test_structured_if_elseif_else(self):
        lines = [
            (10, "LET X = 2"),
            (20, "IF X = 1 THEN"),
            (30, 'PRINT "one"'),
            (40, "ELSEIF X = 2 THEN"),
            (50, 'PRINT "two"'),
            (60, "ELSE"),
            (70, 'PRINT "other"'),
            (80, "ENDIF"),
            (90, "END"),
        ]
        self.assertEqual(self.run_program(lines), "two")

    def test_nested_structured_if(self):
        lines = [
            (10, "LET A = 5"),
            (20, "IF A >= 0 THEN"),
            (30, "IF A < 10 THEN"),
            (40, 'PRINT "small"'),
            (50, "ELSE"),
            (60, 'PRINT "big"'),
            (70, "ENDIF"),
            (80, "ELSE"),
            (90, 'PRINT "negative"'),
            (100, "ENDIF"),
            (110, "END"),
        ]
        self.assertEqual(self.run_program(lines), "small")

    def test_single_line_if_then_else(self):
        lines = [
            (10, "LET X = 3"),
            (20, 'IF X = 2 THEN PRINT "no" ELSE PRINT "yes"'),
            (30, "END"),
        ]
        self.assertEqual(self.run_program(lines), "yes")

    def test_resolve_path_relative_and_absolute(self):
        interp = BASICInterpreter()
        interp.working_dir = r'C:\Projects\basic'
        self.assertEqual(interp.resolve_path('game.bas'), r'C:\Projects\basic\game.bas')
        self.assertEqual(interp.resolve_path(r'D:\temp\game.bas'), r'D:\temp\game.bas')

    def test_load_save_quoted_paths_with_spaces(self):
        import os
        import tempfile

        interp = BASICInterpreter()
        with tempfile.TemporaryDirectory() as tmp:
            spaced = os.path.join(tmp, 'my table.bas')
            with open(spaced, 'w', encoding='utf-8') as f:
                f.write('10 PRINT "ok"\n20 END\n')
            interp.working_dir = tmp
            interp.load('"my table.bas"')
            self.assertEqual(interp.program[10], 'PRINT "ok"')

            interp.new()
            interp.set_program_line(10, 'PRINT "saved"')
            interp.save("'my table.bas'")
            with open(spaced, encoding='utf-8') as f:
                self.assertIn('PRINT "saved"', f.read())

    def test_dim_and_array_access(self):
        lines = [
            (10, "DIM A(3)"),
            (20, "A(0) = 10"),
            (30, "A(3) = 40"),
            (40, "PRINT A(0), A(3)"),
            (50, "END"),
        ]
        self.assertEqual(self.run_program(lines), "        10        40")

    def test_dim_string_and_int_arrays(self):
        lines = [
            (10, "DIM N%(2)"),
            (20, 'DIM S$(1)'),
            (30, "N%(1) = 7"),
            (40, 'S$(1) = "ok"'),
            (50, "PRINT N%(1); S$(1)"),
            (60, "END"),
        ]
        self.assertEqual(self.run_program(lines), "7ok")

    def test_data_read_restore(self):
        lines = [
            (10, "READ A, B"),
            (20, 'PRINT A; ","; B'),
            (30, "RESTORE 100"),
            (40, "READ A, B"),
            (50, 'PRINT A; ","; B'),
            (60, "END"),
            (100, 'DATA 1, 2, "skip"'),
        ]
        self.assertEqual(self.run_program(lines), '1,2\n1,2')

    def test_restore_relative_plus_one(self):
        lines = [
            (10, 'RESTORE +1'),
            (20, 'READ A$'),
            (30, 'PRINT A$'),
            (40, 'END'),
            (50, 'DATA first'),
            (60, 'DATA second'),
        ]
        self.assertEqual(self.run_program(lines), 'first')

    def test_data_empty_items_between_commas(self):
        lines = [
            (10, 'READ A$, B$, C$'),
            (20, 'PRINT "["; A$; "]["; B$; "]["; C$; "]"'),
            (30, 'END'),
            (100, 'DATA one,,three'),
        ]
        self.assertEqual(self.run_program(lines), '[one][][three]')

    def test_print_comma_number_then_string(self):
        lines = [
            (10, 'MSG$ = "hi"'),
            (20, "READ A"),
            (30, "DATA 1"),
            (40, "PRINT A, MSG$"),
            (50, "END"),
        ]
        self.assertEqual(self.run_program(lines), '1         hi')

    def test_read_into_array_element(self):
        lines = [
            (10, "DIM A(1)"),
            (20, "DATA 9, 8"),
            (30, "READ A(0), A(1)"),
            (40, "PRINT A(0), A(1)"),
            (50, "END"),
        ]
        self.assertEqual(self.run_program(lines), "         9         8")

    def test_print_file_echo_tee(self):
        with tempfile.TemporaryDirectory() as tmp:
            lines = [
                (10, '_print_file_echo = 1'),
                (20, 'LET CH = OPENOUT("data.txt")'),
                (30, 'PRINT# CH, "tee"'),
                (40, 'CLOSE# CH'),
                (50, 'END'),
            ]
            interp = BASICInterpreter()
            interp.working_dir = tmp
            out = self.run_program_lines(interp, lines)
            self.assertEqual(out, 'tee')
            with open(os.path.join(tmp, 'data.txt'), encoding='utf-8') as f:
                self.assertEqual(f.read(), 'tee\n')

    # [REMOVED for Phase 1] pygame / auto-display tests moved to dedicated graphics tests
    # (test_bbc_graphics.py, test_graphics_confirm.py, test_display.py, test/manual/).
    # Kept out of god file and broad non-gfx regression. See stuck_tests.txt + phase markers.

    # [REMOVED for Phase 1] tee_terminal + pygame interactive tests quarantined.
    # Full versions live in dedicated test files under graphics / manual when needed.

            def poll(self) -> bool:
                return True

            def pump_events(self) -> None:
                return None

            def present(self) -> None:
                return None

        interp._display = _TerminalOnlyDisplay()
        interp._display_live = True

        with patch.object(interp, '_ensure_display'), patch.object(
            interp, '_flush_display',
        ), patch.object(
            interp, '_read_combined_tee_input_line', return_value='YN',
        ):
            line = interp._read_program_input('? ')
        self.assertEqual(line, 'YN')

    def test_print_file_echo_off_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            lines = [
                (10, 'LET CH = OPENOUT("data.txt")'),
                (20, 'PRINT# CH, "silent"'),
                (30, 'CLOSE# CH'),
                (40, 'END'),
            ]
            interp = BASICInterpreter()
            interp.working_dir = tmp
            out = self.run_program_lines(interp, lines)
            self.assertEqual(out, '')

    def test_bbc_openout_string_and_print_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            lines = [
                (10, 'f = OPENOUT "data.txt"'),
                (20, 'PRINT #f, "bbc"'),
                (30, 'CLOSE#f'),
                (40, 'END'),
            ]
            interp = BASICInterpreter()
            interp.working_dir = tmp
            out = self.run_program_lines(interp, lines)
            self.assertEqual(out, '')
            with open(os.path.join(tmp, 'data.txt'), encoding='utf-8') as handle:
                self.assertEqual(handle.read(), 'bbc\n')

    def test_openout_concatenated_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
            interp.working_dir = tmp
            interp.str_variables['BASE'] = tmp + os.sep
            channel = int(interp._eval_numeric('OPENOUT(BASE$+"animal.dat")'))
            self.assertGreater(channel, 0)
            self.assertIn(channel, interp.file_channels)
            interp._assign('X', 'OPENOUT(BASE$+"animal.dat")')
            self.assertEqual(int(interp.variables['X']), channel)

    def test_eof_hash_empty_read_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'empty.dat')
            open(path, 'w', encoding='utf-8').close()
            interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
            interp.working_dir = tmp
            interp._assign('X', f'OPENIN("{path}")')
            channel = int(interp.variables['X'])
            self.assertNotEqual(interp._eval_numeric('EOF#X'), 0.0)
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.execute_line(20, 'INPUT#X,A$', [20, 30])
            self.assertEqual(buf.getvalue(), '')
            self.assertNotEqual(interp._eval_numeric('EOF#X'), 0.0)
            interp._close_file_channels()

    def test_input_hash_eof_repeat_exits_without_error_spam(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'empty.dat')
            open(path, 'w', encoding='utf-8').close()
            lines = [
                (10, f'X=OPENIN("{path}")'),
                (20, 'Z=0'),
                (30, 'REPEAT INPUT#X,A$(Z):Z=Z+1'),
                (40, 'UNTIL EOF#X'),
                (50, 'PRINT "done"'),
                (60, 'END'),
            ]
            interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
            interp.working_dir = tmp
            out = self.run_program_lines(interp, lines)
            self.assertEqual(out, 'done')

    def test_input_hash_channel_error_includes_line(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.variables['X'] = 99.0
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_line(1250, 'INPUT#X,A$', [1250])
        out = buf.getvalue()
        self.assertIn('? INPUT# channel at line 1250', out)
        self.assertIn('`INPUT#X,A$`', out)

    def test_runtime_error_shows_statement_index_on_colon_line(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_line(200, 'A=1:INPUT#X,B$:C=2', [200])
        out = buf.getvalue()
        self.assertIn('at line 200', out)
        self.assertIn('statement 2 of 3', out)
        self.assertIn('`INPUT#X,B$`', out)

    def test_print_input_file_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            lines = [
                (10, 'LET CH = OPENOUT("data.txt")'),
                (20, 'PRINT# CH, 1, 2, 3'),
                (30, 'PRINT# CH, "hi"'),
                (40, 'CLOSE# CH'),
                (50, 'LET CH = OPENIN("data.txt")'),
                (60, 'INPUT# CH, A, B, C'),
                (70, 'INPUT# CH, MSG$'),
                (80, 'CLOSE# CH'),
                (90, 'PRINT A, B, C, MSG$'),
                (100, 'END'),
            ]
            interp = BASICInterpreter()
            interp.working_dir = tmp
            for line_num, statement in lines:
                interp.set_program_line(line_num, statement)
            out = self.run_program_lines(interp, lines)
            self.assertEqual(out, '1         2         3         hi')

    def run_program_lines(self, interp, lines):
        for line_num, statement in lines:
            interp.program[line_num] = statement
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        return buf.getvalue().rstrip('\n')

    def test_load_remembers_filename_for_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'hello.bas')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('PRINT "loaded"\nEND\n')
            interp = BASICInterpreter()
            interp.working_dir = tmp
            interp.load('hello.bas')
            self.assertEqual(interp.loaded_filename, 'hello.bas')
            interp.set_program_line(10, 'PRINT "changed"')
            interp.save(interp.loaded_filename)
            with open(path, encoding='utf-8') as f:
                text = f.read()
            self.assertIn('PRINT "changed"', text)

    def test_new_clears_loaded_filename(self):
        interp = BASICInterpreter()
        interp.loaded_filename = 'keep.bas'
        interp.new()
        self.assertIsNone(interp.loaded_filename)

    def test_save_prompts_when_no_loaded_filename(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, 'PRINT 1')
        with patch('builtins.input', return_value='prompted.bas'):
            with tempfile.TemporaryDirectory() as tmp:
                interp.working_dir = tmp
                filename = _resolve_save_filename(interp, None)
                self.assertEqual(filename, 'prompted.bas')
                interp.save(filename)
                self.assertEqual(interp.loaded_filename, 'prompted.bas')
                self.assertTrue(os.path.exists(os.path.join(tmp, 'prompted.bas')))

    def test_cd_dir_and_save_load(self):
        import os
        import tempfile

        interp = BASICInterpreter()
        with tempfile.TemporaryDirectory() as tmp:
            sub = os.path.join(tmp, 'programs')
            os.mkdir(sub)
            interp.change_dir(sub)
            self.assertEqual(interp.working_dir, os.path.normpath(sub))

            interp.set_program_line(10, 'PRINT "hi"')
            interp.save('hello.bas')
            saved = os.path.join(sub, 'hello.bas')
            self.assertTrue(os.path.exists(saved))

            interp.new()
            interp.load('hello.bas')
            self.assertEqual(interp.program[10], 'PRINT "hi"')

            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.list_dir('*.bas')
            listing = buf.getvalue()
            self.assertIn('hello.bas', listing)
            self.assertTrue(os.path.normpath(sub) in listing.splitlines()[0])

    def test_save_pretty_writes_unnumbered_indented_program(self):
        import os
        import tempfile

        interp = BASICInterpreter()
        interp.set_program_line(10, "FOR I = 1 TO 2")
        interp.set_program_line(20, "WHILE I < 3")
        interp.set_program_line(30, "IF I = 1 THEN")
        interp.set_program_line(40, 'PRINT "hi"')
        interp.set_program_line(50, "ENDIF")
        interp.set_program_line(60, "WEND")
        interp.set_program_line(70, "NEXT I")
        interp.set_program_line(80, "END")

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'pretty.bas')
            interp.working_dir = tmp
            interp.save('pretty.bas', 'pretty')
            with open(path, encoding='utf-8') as f:
                saved = f.read().splitlines()

            self.assertTrue(all(not re.match(r'^\s*\d+\s', line) for line in saved if line.strip()))
            self.assertIn('FOR I = 1 TO 2', saved[0])
            self.assertIn('PRINT "hi"', '\n'.join(saved))

            def leading_spaces(text):
                return len(text) - len(text.lstrip())

            next_line = next(line for line in saved if 'NEXT I' in line)
            for_line = next(line for line in saved if 'FOR I = 1 TO 2' in line)
            self.assertEqual(leading_spaces(next_line), leading_spaces(for_line))

            interp.new()
            interp.load('pretty.bas')
            self.assertEqual(interp.program[10], 'FOR I = 1 TO 2')
            self.assertEqual(interp.program[80], 'END')

    def test_load_autonumbers_unnumbered_program(self):
        import os
        import tempfile

        interp = BASICInterpreter()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'plain.bas')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('PRINT "a"\n    PRINT "b"\nEND\n')
            interp.working_dir = tmp
            interp.load('plain.bas')
            self.assertEqual(interp.program[10], 'PRINT "a"')
            self.assertEqual(interp.program[20], 'PRINT "b"')
            self.assertEqual(interp.program[30], 'END')
            self.assertEqual(interp.line_indent.get(20), 4)

    def test_load_unnumbered_with_goto(self):
        import os
        import tempfile

        interp = BASICInterpreter()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'goto.bas')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('GOTO HIT\nPRINT "skip"\nHIT: PRINT "hit"\nEND\n')
            interp.working_dir = tmp
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.load('goto.bas')
            self.assertIn('Loaded:', buf.getvalue())
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.run()
            self.assertEqual(buf.getvalue().strip(), 'hit')

    def test_load_unnumbered_with_gosub(self):
        import os
        import tempfile

        interp = BASICInterpreter()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'sub.bas')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('GOSUB SUB\nPRINT "back"\nEND\nSUB: PRINT "sub"\nRETURN\n')
            interp.working_dir = tmp
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.load('sub.bas')
            self.assertIn('Loaded:', buf.getvalue())
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.run()
            self.assertEqual(buf.getvalue().strip(), 'sub\nback')

    def test_load_mixed_numbered_unnumbered_fails(self):
        import os
        import tempfile

        interp = BASICInterpreter()
        interp.set_program_line(10, 'PRINT "keep"')
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'mixed.bas')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('10 PRINT "a"\nPRINT "b"\n')
            interp.working_dir = tmp
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.load('mixed.bas')
            out = buf.getvalue()
            self.assertIn('Mixed numbered and unnumbered', out)
            self.assertIn('source line 2', out)
            self.assertEqual(interp.program[10], 'PRINT "keep"')

    def test_load_numbered_with_leading_preamble(self):
        import os
        import tempfile

        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'poem_style.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(
                    'ON ERROR GOTO 900\n'
                    '\n'
                    '10 PRINT "start"\n'
                    '20 END\n',
                )
            interp.working_dir = tmp
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.load('poem_style.bas', announce=False)
            self.assertIn('ON ERROR GOTO 900', interp.program[0])
            self.assertEqual(interp.program[10], 'PRINT "start"')

    def test_immediate_assignment_and_print(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('tony = 100')
            interp.execute_immediate('LET answer_count = 5')
            interp.execute_immediate('PRINT tony')
            interp.execute_immediate('PRINT answer_count')
        self.assertEqual(buf.getvalue().strip(), '100\n5')
        self.assertEqual(interp.variables['tony'], 100.0)
        self.assertEqual(interp.program, {})

    def test_long_variable_names(self):
        lines = [
            (10, "LET factorial = 1"),
            (20, "FOR loop_counter = 1 TO 4"),
            (30, "LET factorial = factorial * loop_counter"),
            (40, "NEXT loop_counter"),
            (50, "PRINT factorial"),
            (60, "END"),
        ]
        self.assertEqual(self.run_program(lines), "24")

    def test_long_integer_and_string_variables(self):
        lines = [
            (10, 'LET message_text$ = "Hello"'),
            (20, "LET answer_count% = 3"),
            (30, "PRINT message_text$"),
            (40, "PRINT answer_count%"),
            (50, "END"),
        ]
        self.assertEqual(self.run_program(lines), "Hello\n3")

    def test_variable_names_are_case_sensitive_in_mini_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
        lines = [
            (10, "LET Count = 10"),
            (20, "LET count = 20"),
            (30, "PRINT Count"),
            (40, "PRINT count"),
            (50, "END"),
        ]
        buf = io.StringIO()
        interp._program_stdout = buf
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp.run()
        self.assertEqual(buf.getvalue(), "10\n20\n")

    def test_variable_names_fold_in_bbc_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        lines = [
            (10, "LET Count = 10"),
            (20, "LET count = 20"),
            (30, "PRINT COUNT"),
            (40, "END"),
        ]
        buf = io.StringIO()
        interp._program_stdout = buf
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp.run()
        self.assertEqual(buf.getvalue(), "20\n")

    def test_variable_names_fold_in_mits_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mits'))
        lines = [
            (10, "LET n = 3"),
            (20, "LET N = 5"),
            (30, "PRINT n"),
            (40, "END"),
        ]
        buf = io.StringIO()
        interp._program_stdout = buf
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp.run()
        self.assertEqual(buf.getvalue(), "5\n")

    def test_shebang_dialect_hint_applies_on_load(self):
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.bas',
            delete=False,
            encoding='utf-8',
        ) as handle:
            handle.write('#!bbc\nPRINT "ok"\nEND\n')
            path = handle.name
        try:
            buf = io.StringIO()
            interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
            interp._program_stdout = buf
            interp.load(path, announce=False)
            self.assertEqual(interp.config.dialect, 'bbc')
            self.assertNotIn('#!bbc', interp.program.values())
            interp.run()
            self.assertEqual(buf.getvalue(), 'ok\n')
        finally:
            os.unlink(path)

    def test_cli_dialect_overrides_shebang_hint(self):
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.bas',
            delete=False,
            encoding='utf-8',
        ) as handle:
            handle.write('#!mits\n10 PRINT "n"\n20 END\n')
            path = handle.name
        try:
            interp = BASICInterpreter(
                InterpreterConfig(dialect='bbc', dialect_locked=True),
            )
            interp.load(path, announce=False)
            self.assertEqual(interp.config.dialect, 'bbc')
        finally:
            os.unlink(path)

    def test_rem_dialect_hint_applies_without_stripping_paren_form(self):
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.bas',
            delete=False,
            encoding='utf-8',
        ) as handle:
            handle.write(
                'REM BETH cousin (bbc dialect)\n'
                'PRINT "beth"\n'
                'END\n'
            )
            path = handle.name
        try:
            interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
            interp.load(path, announce=False)
            self.assertEqual(interp.config.dialect, 'bbc')
            self.assertTrue(
                any('bbc dialect' in stmt for stmt in interp.program.values()),
            )
        finally:
            os.unlink(path)

    def test_repl_dialect_and_case_commands(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertTrue(_execute_repl_line(interp, 'DIALECT bbc'))
            self.assertTrue(_execute_repl_line(interp, 'CASE off'))
            self.assertTrue(_execute_repl_line(interp, 'DIALECT'))
        text = out.getvalue()
        self.assertIn('Dialect: bbc', text)
        self.assertIn('Case: off', text)
        self.assertIn('Dialect: bbc', text)
        self.assertEqual(interp.config.dialect, 'bbc')
        self.assertFalse(interp._identifiers_case_sensitive())

    def test_case_change_clears_runtime_variables(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
        interp.program[10] = 'LET Count = 42'
        interp.program[20] = 'END'
        interp.variables['Count'] = 42.0
        interp.set_case_sensitivity(False, announce=False)
        self.assertNotIn('Count', interp.variables)
        self.assertNotIn('COUNT', interp.variables)

    def test_dialect_change_to_mits_warns_on_bbc_program(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.program[10] = 'WHILE I% < 3'
        interp.program[20] = 'WEND'
        interp.program[30] = 'END'
        interp._program_source_numbered = False
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertTrue(interp.set_dialect('mits'))
        self.assertIn('Warning:', out.getvalue())
        self.assertEqual(interp.config.dialect, 'mits')

    def test_dialect_change_blocked_in_strict_mode(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', strict_dialect=True),
        )
        interp.program[10] = 'WHILE I% < 3'
        interp.program[20] = 'WEND'
        interp.program[30] = 'END'
        interp._program_source_numbered = False
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertFalse(interp.set_dialect('mits'))
        self.assertEqual(interp.config.dialect, 'bbc')
        self.assertIn('? DIALECT error', out.getvalue())

    def test_proc_remove_spaces_recursive(self):
        """RISC OS manual uses RIGHT$ on line 150; BBC semantics need MID$."""
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        lines = [
            (10, 'INPUT A$'),
            (20, 'PROCremove_spaces(A$)'),
            (30, 'END'),
            (100, 'DEF PROCremove_spaces(A$)'),
            (110, 'LOCAL pos_space%'),
            (120, 'PRINT A$'),
            (130, 'pos_space%=INSTR(A$," ")'),
            (140, 'IF pos_space% THEN'),
            (150, '  A$=LEFT$(A$,pos_space%-1)+MID$(A$,pos_space%+1)'),
            (160, '  PROCremove_spaces(A$)'),
            (170, 'ENDIF'),
            (180, 'ENDPROC'),
        ]
        for line_num, statement in lines:
            interp.set_program_line(line_num, statement)
        buf = io.StringIO()
        interp._program_stdout = buf
        with patch('builtins.input', return_value='A quick brown fox'):
            interp.run()
        self.assertEqual(
            buf.getvalue().splitlines(),
            [
                'A quick brown fox',
                'Aquick brown fox',
                'Aquickbrown fox',
                'Aquickbrownfox',
            ],
        )

    def test_proc_reverseprint_for_loop(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        lines = [
            (10, 'PROCreverseprint("Good morning !")'),
            (100, 'DEF PROCreverseprint(A$)'),
            (110, 'FOR i% = LEN A$ TO 1 STEP -1'),
            (120, '  PRINT MID$(A$,i%,1);'),
            (130, 'NEXT'),
            (140, 'ENDPROC'),
        ]
        for line_num, statement in lines:
            interp.set_program_line(line_num, statement)
        buf = io.StringIO()
        interp._program_stdout = buf
        interp.run()
        self.assertEqual(buf.getvalue(), '! gninrom dooG')

    def test_proc_reverseprint_len_bare_in_for(self):
        """BBC allows LEN A$ without parentheses in FOR bounds."""
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        lines = [
            (10, 'DEF PROCreverseprint(A$)'),
            (20, 'FOR i% = LEN A$ TO 1 STEP -1'),
            (30, '  PRINT MID$(A$,i%,1);'),
            (40, 'NEXT'),
            (50, 'ENDPROC'),
            (60, 'PROCreverseprint("Hi")'),
            (70, 'END'),
        ]
        for line_num, statement in lines:
            interp.set_program_line(line_num, statement)
        buf = io.StringIO()
        interp._program_stdout = buf
        interp.run()
        self.assertEqual(buf.getvalue(), 'iH')

    def test_len_without_parentheses(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.str_variables['A'] = 'hello'
        self.assertEqual(interp._eval_numeric('LEN A$'), 5.0)

    def test_right_dollar_two_arg_returns_last_n_characters(self):
        interp = BASICInterpreter()
        out = io.StringIO()
        interp._program_stdout = out
        for line_num, statement in [
            (10, 'PRINT RIGHT$("A quick brown fox",3)'),
            (20, 'END'),
        ]:
            interp.program[line_num] = statement
        interp.run()
        self.assertEqual(out.getvalue(), 'fox\n')

    def test_mid_dollar_two_arg_from_position_to_end(self):
        interp = BASICInterpreter()
        out = io.StringIO()
        interp._program_stdout = out
        for line_num, statement in [
            (10, 'PRINT MID$("hello",3)'),
            (20, 'END'),
        ]:
            interp.program[line_num] = statement
        interp.run()
        self.assertEqual(out.getvalue(), 'llo\n')

    def test_left_and_right_dollar_single_arg_shorthand(self):
        interp = BASICInterpreter()
        out = io.StringIO()
        interp._program_stdout = out
        for line_num, statement in [
            (10, 'PRINT LEFT$("Hello")'),
            (20, 'PRINT RIGHT$("Hello")'),
            (30, 'END'),
        ]:
            interp.program[line_num] = statement
        interp.run()
        self.assertEqual(out.getvalue(), 'Hell\no\n')

    def test_split_dialect_hints_parses_env_shebang(self):
        lines, hint = split_dialect_hints([
            '#!/usr/bin/env mini_basic --dialect mits strict\n',
            '10 PRINT 1\n',
        ])
        self.assertIsNotNone(hint)
        self.assertEqual(hint.dialect, 'mits')
        self.assertTrue(hint.strict)
        self.assertEqual(len(lines), 1)
        shebang = parse_shebang_line('#!mini case')
        self.assertIsNotNone(shebang)
        self.assertTrue(shebang.case_sensitive)

    def test_multiline_def_fn_parameter_case_folds_in_bbc_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        lines = [
            (10, "DEF FNfact(n)"),
            (20, "IF N<1 THEN"),
            (30, "=1"),
            (40, "ELSE"),
            (50, "=FNfact(n-1)*n"),
            (60, "ENDIF"),
            (70, "END DEF"),
            (80, "PRINT FNfact(5)"),
            (90, "END"),
        ]
        buf = io.StringIO()
        interp._program_stdout = buf
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp.run()
        self.assertEqual(buf.getvalue(), "120\n")

    def test_multiline_def_fn_accepts_lowercase_end_if_and_end_def(self):
        interp = BASICInterpreter()
        lines = [
            (10, "DEF FNfact(n)"),
            (20, "IF n<2 THEN"),
            (30, "= 1"),
            (40, "ELSE"),
            (50, "= n * FNfact(n - 1)"),
            (60, "END if"),
            (70, "END def"),
            (80, "PRINT FNfact(5)"),
            (90, "END"),
        ]
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp._ensure_definitions_current()
        self.assertIn('fact', interp.user_functions)
        self.assertTrue(interp.user_functions['fact'].multiline)
        buf = io.StringIO()
        interp._program_stdout = buf
        interp.run()
        self.assertEqual(buf.getvalue(), "120\n")

    def test_multiline_def_fn_accepts_lowercase_end_if_with_rem(self):
        interp = BASICInterpreter()
        lines = [
            (10, "DEF FNfact(n)"),
            (20, "if n<2 then"),
            (30, "= 1"),
            (40, "else"),
            (50, "= n * FNfact(n - 1)"),
            (60, "end if REM close branch"),
            (70, "end def"),
            (80, "PRINT FNfact(4)"),
            (90, "END"),
        ]
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp._ensure_definitions_current()
        self.assertIn('fact', interp.user_functions)
        buf = io.StringIO()
        interp._program_stdout = buf
        interp.run()
        self.assertEqual(buf.getvalue(), "24\n")

    def test_invalid_variable_name_rejected(self):
        lines = [
            (10, "LET 2bad = 1"),
            (20, "END"),
        ]
        buf = io.StringIO()
        interp = BASICInterpreter()
        for line_num, statement in lines:
            interp.program[line_num] = statement
        with redirect_stdout(buf):
            interp.run()
        self.assertIn("? LET error", buf.getvalue())

    def test_structured_if_no_else(self):
        lines = [
            (10, "LET X = 2"),
            (20, "IF X = 1 THEN"),
            (30, 'PRINT "yes"'),
            (40, "ENDIF"),
            (50, 'PRINT "after"'),
            (60, "END"),
        ]
        self.assertEqual(self.run_program(lines), "after")

    def test_def_fn_single_line(self):
        lines = [
            (10, "DEF FNdouble(x) = x * 2"),
            (20, "PRINT FNdouble(21)"),
            (30, "END"),
        ]
        self.assertEqual(self.run_program(lines), "42")

    def test_def_fn_two_params(self):
        lines = [
            (10, "DEF FNadd(a, b) = a + b"),
            (20, "PRINT FNadd(3, 4)"),
            (30, "END"),
        ]
        self.assertEqual(self.run_program(lines), "7")

    def test_def_fn_with_sgn(self):
        lines = [
            (10, "DEF FNsign(x) = SGN(x)"),
            (20, "PRINT FNsign(-5); FNsign(0); FNsign(8)"),
            (30, "END"),
        ]
        self.assertEqual(self.run_program(lines), "-101")

    def test_sgn(self):
        lines = [
            (10, "PRINT SGN(-3); SGN(0); SGN(9)"),
            (20, "END"),
        ]
        self.assertEqual(self.run_program(lines), "-101")

    def test_rnd_one_is_unit_interval(self):
        lines = [
            (10, 'FOR I = 1 TO 30'),
            (20, 'LET X = RND(1)'),
            (30, 'IF X < 0 THEN PRINT "low"'),
            (40, 'IF X >= 1 THEN PRINT "high"'),
            (50, 'NEXT I'),
            (60, 'PRINT "ok"'),
            (70, 'END'),
        ]
        self.assertEqual(self.run_program(lines), 'ok')

    def test_rnd_range(self):
        lines = [
            (10, "LET S = RND(-42)"),
            (20, "FOR I = 1 TO 20"),
            (30, "LET N = RND(6)"),
            (40, 'IF N < 1 THEN PRINT "bad"'),
            (50, "IF N > 6 THEN PRINT \"bad\""),
            (60, "NEXT I"),
            (70, 'PRINT "ok"'),
            (80, "END"),
        ]
        self.assertEqual(self.run_program(lines), "ok")

    def test_rnd_zero_repeats(self):
        lines = [
            (10, "LET S = RND(-99)"),
            (20, "LET A = RND"),
            (30, "IF A = RND(0) THEN PRINT 1 ELSE PRINT 0"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "1")

    def test_print_spc_and_tab(self):
        lines = [
            (10, 'PRINT "A"; SPC(3); "B"'),
            (20, 'PRINT TAB(6); "C"'),
            (30, "END"),
        ]
        self.assertEqual(self.run_program(lines), "A   B\n     C")

    def test_print_spc_implicit_string(self):
        lines = [
            (10, 'PRINT SPC(4)"Hi"'),
            (20, 'PRINT SPC(4);"Hi"'),
            (30, 'PRINT TAB(6)"x"'),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "    Hi\n    Hi\n     x")

    def test_print_comma_empty_field(self):
        lines = [
            (10, 'PRINT SPC(4),"Hi"'),
            (20, 'PRINT SPC(4),,"Hi"'),
            (30, 'PRINT ,,"Hi"'),
            (40, "END"),
        ]
        self.assertEqual(
            self.run_program(lines),
            '          Hi\n                    Hi\n                    Hi',
        )

    def test_def_fn_string(self):
        lines = [
            (10, "DEF FNtag$(text$) = text$"),
            (20, 'PRINT "hi "; FNtag$("Bob")'),
            (30, "END"),
        ]
        self.assertEqual(self.run_program(lines), "hi Bob")

    def test_def_fn_multiline_hypot(self):
        lines = [
            (10, "DEF FNhypot(a, b)"),
            (20, "  LET t = a * a + b * b"),
            (30, "  = SQR(t)"),
            (40, "END DEF"),
            (50, "PRINT FNhypot(3, 4)"),
            (60, "END"),
        ]
        self.assertEqual(self.run_program(lines), "5")

    def test_def_fn_equals_return_without_end_def(self):
        import math

        lines = [
            (10, 'FOR N% = 1 TO 3'),
            (20, 'PRINT "r";N%;" v"; FNvolume(N%)'),
            (30, 'NEXT N%'),
            (40, 'END'),
            (100, 'DEF FNvolume(radius%)'),
            (110, '= 4/3*PI*radius%^3'),
        ]
        out = self.run_program(lines).splitlines()
        self.assertEqual(len(out), 3)
        for n, line in enumerate(out, start=1):
            expected = 4 / 3 * math.pi * (n ** 3)
            self.assertIn(str(n), line)
            printed = float(line.split('v', 1)[1])
            self.assertAlmostEqual(printed, expected, places=5)

    def test_def_fn_shorthand_then_multiline_fn_via_block_entry(self):
        interp = BASICInterpreter()
        for line_num, statement in [
            (10, 'FOR N% = 1 TO 2'),
            (20, 'PRINT FNvolume(N%)'),
            (30, 'NEXT N%'),
            (40, 'END'),
            (100, 'DEF FNvolume(radius%)'),
            (110, '= 4/3*PI*radius%^3'),
        ]:
            interp.program[line_num] = statement
        interp.run()
        with patch('mini_basic.runtime._prompt_editing_input', side_effect=[
            'IF n<2 THEN',
            '  = 1',
            'ELSE',
            '  = n * FNfact(n - 1)',
            'END if',
            'END def',
            '',
        ]):
            interp.def_block_entry('DEF FNfact(n)')
        self.assertIn('volume', interp.user_functions)
        self.assertIn('fact', interp.user_functions)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('PRINT FNfact(10)')
        self.assertEqual(buf.getvalue().strip(), '3628800')

    def test_def_fn_multiline_body_not_run_at_startup(self):
        lines = [
            (10, "LET leaked = 0"),
            (20, "DEF FNfoo(x)"),
            (30, "  LET leaked = 99"),
            (40, "  = x * 2"),
            (50, "END DEF"),
            (60, "PRINT leaked"),
            (70, "END"),
        ]
        self.assertEqual(self.run_program(lines), "0")

    def test_def_fn_multiline_if_return(self):
        lines = [
            (10, "DEF FNabsval(x)"),
            (20, "IF x < 0 THEN"),
            (30, "  = -x"),
            (40, "ELSE"),
            (50, "  = x"),
            (60, "ENDIF"),
            (70, "END DEF"),
            (80, "PRINT FNabsval(-7); FNabsval(4)"),
            (90, "END"),
        ]
        self.assertEqual(self.run_program(lines), "74")

    def test_def_fn_end_fn_and_end_if_two_word_closers(self):
        lines = [
            (10, "DEF FNfact(n)"),
            (20, "IF n<1 THEN"),
            (30, "=1"),
            (40, "ELSE"),
            (50, "=FNfact(n-1)*n"),
            (60, "END IF"),
            (70, "END FN"),
            (80, "PRINT FNfact(5)"),
            (90, "END"),
        ]
        self.assertEqual(self.run_program(lines), "120")

    def test_end_if_two_word_closer(self):
        lines = [
            (10, "IF 1 THEN"),
            (20, 'PRINT "x"'),
            (30, "END IF"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "x")

    def test_end_while_two_word_closer(self):
        lines = [
            (10, "LET I = 0"),
            (20, "WHILE I < 1"),
            (30, "LET I = I + 1"),
            (40, "END WHILE"),
            (50, "END"),
        ]
        self.assertEqual(self.run_program(lines), "")

    def test_end_proc_two_word_closer(self):
        lines = [
            (10, "DEF PROChello"),
            (20, 'PRINT "hi"'),
            (30, "END PROC"),
            (40, "PROChello"),
            (50, "END"),
        ]
        self.assertEqual(self.run_program(lines), "hi")

    def test_def_fn_header_only_hint(self):
        lines = [
            (10, "DEF FNfact(n)"),
            (20, "END"),
        ]
        buf = io.StringIO()
        interp = BASICInterpreter()
        for line_num, statement in lines:
            interp.program[line_num] = statement
        with redirect_stdout(buf):
            interp.run()
        self.assertIn('END DEF', buf.getvalue())

    def test_def_fn_missing_equals_return_warns_at_run(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.program[10] = 'DEF FNFACT(N)'
        interp.program[20] = 'IF N<2 THEN 1 ELSE FNFACT(N - 1) * N'
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        output = buf.getvalue()
        self.assertIn('DEF FN body needs =return', output)
        self.assertNotIn('FNfact(2)', output)

    def test_def_fn_missing_equals_return_errors_on_call(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.program[10] = 'DEF FNFACT(N)'
        interp.program[20] = 'IF N<2 THEN 1 ELSE FNFACT(N - 1) * N'
        interp._prepare_run()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('? FNfact(2)')
        output = buf.getvalue()
        self.assertIn('? FN error', output)
        self.assertNotIn('FNfact(2)', output)

    def test_immediate_compact_if_bare_numbers_error(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('IF 1 THEN 0 ELSE 100')
        self.assertIn('? IF error', buf.getvalue())

    def test_immediate_compact_if_goto_existing_line(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.program[100] = 'PRINT 100'
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('IF 1 THEN 100')
        self.assertEqual(buf.getvalue().strip(), '100')

    def test_program_compact_if_goto_missing_line_errors(self):
        lines = [
            (10, 'IF 1 THEN 999'),
            (20, 'PRINT "ok"'),
            (30, 'END'),
        ]
        output = self.run_program(lines)
        self.assertIn('? IF error', output)
        self.assertIn('ok', output)

    def test_if_goto_allowed_in_numbered_goto_dialects(self):
        for dialect in ('mini', 'mits', 'commodore'):
            with self.subTest(dialect=dialect):
                lines = [
                    (10, 'PRINT "hit"'),
                    (20, 'END'),
                    (30, 'IF 1 GOTO 10'),
                    (40, 'END'),
                ]
                interp = BASICInterpreter(
                    InterpreterConfig(dialect=dialect, display='none'),
                )
                for line_num, stmt in lines:
                    interp.program[line_num] = stmt
                buf = io.StringIO()
                with redirect_stdout(buf):
                    interp.run()
                self.assertEqual(buf.getvalue().strip(), 'hit')

    def test_if_goto_rejected_in_bbc_strict_on_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'bad.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('IF 1 GOTO 20\nPRINT "skip"\nEND\n')
            interp = BASICInterpreter(
                InterpreterConfig(dialect='bbc', strict_dialect=True),
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.load(path)
            self.assertEqual(len(interp.program), 0)
            self.assertIn('if goto not allowed', buf.getvalue().lower())

    def test_if_goto_runtime_error_in_bbc(self):
        lines = [
            (10, 'IF 1 GOTO 30'),
            (20, 'END'),
            (30, 'PRINT "hit"'),
            (40, 'END'),
        ]
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        for line_num, stmt in lines:
            interp.program[line_num] = stmt
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertIn('? IF error', buf.getvalue())
        self.assertNotIn('hit', buf.getvalue())

    def test_if_goto_rejected_in_tiny(self):
        lines = [
            (10, 'IF 1 GOTO 30'),
            (20, 'END'),
            (30, 'PRINT "hit"'),
            (40, 'END'),
        ]
        interp = BASICInterpreter(InterpreterConfig(dialect='tiny', display='none'))
        for line_num, stmt in lines:
            interp.program[line_num] = stmt
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertIn('? IF error', buf.getvalue())
        self.assertNotIn('hit', buf.getvalue())

    def test_if_then_line_rejected_in_tiny(self):
        lines = [
            (10, 'IF 1 THEN 30'),
            (20, 'END'),
            (30, 'PRINT "hit"'),
            (40, 'END'),
        ]
        interp = BASICInterpreter(InterpreterConfig(dialect='tiny', display='none'))
        for line_num, stmt in lines:
            interp.program[line_num] = stmt
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertIn('? IF error', buf.getvalue())
        self.assertNotIn('hit', buf.getvalue())

    def test_if_then_statement_allowed_in_tiny(self):
        lines = [
            (10, 'IF 1 THEN PRINT "ok"'),
            (20, 'END'),
        ]
        interp = BASICInterpreter(InterpreterConfig(dialect='tiny', display='none'))
        for line_num, stmt in lines:
            interp.program[line_num] = stmt
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertEqual(buf.getvalue().strip(), 'ok')

    def test_boolean_comparisons_return_minus_one(self):
        interp = BASICInterpreter()
        interp.variables['A'] = 1
        interp.variables['B'] = 2
        self.assertEqual(interp.eval_expr('A < B'), -1.0)
        self.assertEqual(interp.eval_expr('A = B'), 0.0)
        self.assertEqual(interp.eval_expr('A <> B'), -1.0)

    def test_boolean_and_or_not(self):
        interp = BASICInterpreter()
        interp.variables['A'] = 1
        interp.variables['B'] = 2
        interp.variables['C'] = 3
        self.assertEqual(interp.eval_expr('A < B AND B < C'), -1.0)
        self.assertEqual(interp.eval_expr('A > B OR B < C'), -1.0)
        self.assertEqual(interp.eval_expr('NOT 0'), -1.0)
        self.assertEqual(interp.eval_expr('NOT -1'), 0.0)
        self.assertEqual(interp.eval_expr('NOT 5'), -6.0)
        self.assertEqual(interp.eval_expr('TRUE'), -1.0)
        self.assertEqual(interp.eval_expr('FALSE'), 0.0)
        self.assertTrue(interp._eval_condition('A < B AND B < C'))

    def test_eval_condition_int_percent_suffix(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.int_variables['I%'] = 3
        self.assertTrue(interp._eval_condition('I% < 5'))
        self.assertFalse(interp._eval_condition('I% >= 5'))
        interp.variables['CONT'] = -1.0
        interp.int_variables['I%'] = 0
        self.assertTrue(interp._eval_condition('CONT AND (I% < 16)'))

    def test_while_int_percent_condition(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        lines = [
            (10, 'I% = 0'),
            (20, 'WHILE I% < 3'),
            (30, 'I% = I% + 1'),
            (40, 'ENDWHILE'),
            (50, 'PRINT I%'),
            (60, 'END'),
        ]
        for line_num, statement in lines:
            interp.program[line_num] = statement
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertEqual(buf.getvalue().strip(), '3')

    def test_boolean_true_false(self):
        lines = [
            (10, "PRINT TRUE; FALSE"),
            (20, "LET X = TRUE + 1"),
            (30, "PRINT X"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "-10\n0")

    def test_boolean_in_print_and_let(self):
        lines = [
            (10, "LET A = 1"),
            (20, "LET B = 2"),
            (30, "LET X = A <> B"),
            (40, "PRINT X"),
            (50, "END"),
        ]
        self.assertEqual(self.run_program(lines), "-1")

    def test_cli_run_bas_file(self):
        import os
        import tempfile

        import mini_basic

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'hello.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('PRINT "beth"\nEND\n')
            buf = io.StringIO()
            with redirect_stdout(buf):
                status = mini_basic.main([path, '--quiet'])
            self.assertEqual(status, mini_basic.EXIT_HOLD_CONSOLE)
            self.assertIn('beth', buf.getvalue())

    def test_cli_run_bas_interactive_does_not_hold_console(self):
        import os
        import tempfile

        import mini_basic

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'hello.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('PRINT "beth"\nEND\n')
            with self._patch_noninteractive_repl(['EXIT']):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    status = mini_basic.main(['-i', path, '--quiet'])
            self.assertEqual(status, 0)

    def test_cli_pretty_list_without_run(self):
        import os
        import tempfile

        import mini_basic

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'struct.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('\n'.join([
                    'WHILE 1',
                    '  IF X = 1 THEN',
                    '    PRINT "ran"',
                    '  ENDIF',
                    '  END',
                ]))
            buf = io.StringIO()
            with redirect_stdout(buf):
                status = mini_basic.main(['--pretty', path, '--quiet'])
            self.assertEqual(status, 0)
            out = buf.getvalue()
            self.assertIn('WHILE', out)
            self.assertIn('IF', out)
            self.assertIn('ENDIF', out)
            self.assertIn('PRINT "ran"', out)
            self.assertNotRegex(out, r'(?m)^ran\s*$')
            self.assertNotIn('Loaded:', out)
            self.assertNotIn('Program cleared.', out)
            self.assertNotIn('Note:', out)

    def test_cli_list_mode_requires_bas_file(self):
        import mini_basic

        buf = io.StringIO()
        with redirect_stdout(buf):
            status = mini_basic.main(['--pretty', '--quiet'])
        self.assertEqual(status, 2)
        self.assertIn('listing mode requires', buf.getvalue())

    def test_cli_pretty_list_then_repl(self):
        import os
        import tempfile

        import mini_basic

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'stay.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('PRINT "run_me"\nEND\n')
            buf = io.StringIO()
            with redirect_stdout(buf):
                with self._patch_noninteractive_repl(['RUN', 'EXIT']):
                    status = mini_basic.main(['--pretty', '-i', path, '--quiet'])
            self.assertEqual(status, 0)
            out = buf.getvalue()
            self.assertIn('PRINT "run_me"', out)
            self.assertRegex(out, r'(?m)^run_me\s*$')

    def test_math_trig_and_pi(self):
        lines = [
            (10, "PRINT SIN(0)"),
            (20, "PRINT COS(0)"),
            (30, "PRINT TAN(0)"),
            (40, "PRINT PI"),
            (50, "END"),
        ]
        out = self.run_program(lines)
        rows = out.splitlines()
        self.assertEqual(rows[0], "0")
        self.assertEqual(rows[1], "1")
        self.assertEqual(rows[2], "0")
        self.assertTrue(abs(float(rows[3]) - 3.141592653589793) < 1e-12)

    def test_math_inverse_trig_log_exp_sqr(self):
        lines = [
            (10, "PRINT ATN(1)"),
            (20, "PRINT ASN(0.5)"),
            (30, "PRINT ACS(0)"),
            (40, "PRINT LOG(2.718281828)"),
            (50, "PRINT EXP(1)"),
            (60, "PRINT SQR(9)"),
            (70, "END"),
        ]
        out = self.run_program(lines)
        rows = [float(x) for x in out.splitlines()]
        self.assertTrue(abs(rows[0] - 0.7853981633974483) < 1e-9)
        self.assertTrue(abs(rows[1] - 0.5235987755982989) < 1e-9)
        self.assertTrue(abs(rows[2] - 1.5707963267948966) < 1e-9)
        self.assertTrue(abs(rows[3] - 1.0) < 1e-6)
        self.assertTrue(abs(rows[4] - 2.718281828) < 1e-6)
        self.assertEqual(rows[5], 3.0)

    def test_math_abs_and_int(self):
        lines = [
            (10, "PRINT ABS(-4.2)"),
            (20, "PRINT INT(3.9)"),
            (30, "PRINT INT(-3.1)"),
            (40, "END"),
        ]
        self.assertEqual(self.run_program(lines), "4.2\n3\n-4")

    def test_program_args_arg_and_argc(self):
        lines = [
            (10, 'PRINT "argc="; _argc'),
            (20, 'PRINT "a="; ARG$(1)'),
            (30, 'PRINT "n="; ARG(1)'),
            (40, 'PRINT "n2="; ARG(2)'),
            (50, 'END'),
        ]
        interp = BASICInterpreter()
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp.program_args = ['32', 'hello']
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertEqual(
            buf.getvalue().strip(),
            'argc=2\na=32\nn=32\nn2=0',
        )

    def test_cli_passes_program_args(self):
        import os
        import tempfile

        import mini_basic

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'args.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('PRINT "iter="; ARG(1)\nEND\n')
            buf = io.StringIO()
            with redirect_stdout(buf):
                status = mini_basic.main([path, '48', '--quiet'])
            self.assertEqual(status, mini_basic.EXIT_HOLD_CONSOLE)
            self.assertIn('iter=48', buf.getvalue())

    def test_cli_exit_word_ends_input_loop(self):
        import mini_basic

        interp = BASICInterpreter()
        interp.set_program_line(10, 'INPUT I$')
        interp.set_program_line(20, 'PRINT "again"')
        interp.set_program_line(30, 'END')
        interp.config.input_exit_words = True
        with patch('builtins.input', return_value='quit'):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.run()
        self.assertNotIn('again', buf.getvalue())

    def test_input_reads_exit_word_by_default(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, 'INPUT I$')
        interp.set_program_line(20, 'PRINT "["; I$; "]"')
        interp.set_program_line(30, 'END')
        with patch('builtins.input', return_value='bye'):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.run()
        self.assertIn('[bye]', buf.getvalue())

    def test_on_error_if_line_not_split_on_colon(self):
        line = (
            'ON ERROR IF ERR=17 CHAIN "tool" '
            'ELSE MODE 3 : PRINT REPORT$ : END'
        )
        parts = BASICInterpreter()._split_colon_statements(line)
        self.assertEqual(parts, [line])

    def test_script_file_kind_treats_corpus_txt_as_program(self):
        import os

        path = os.path.join(
            _ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'graphics',
            'fern.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('missing fern.txt')
        self.assertEqual(_script_file_kind(path), 'program')

    def test_cli_runs_corpus_txt_as_program_not_repl(self):
        import os

        path = os.path.join(
            _ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'graphics',
            'fern.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('missing fern.txt')
        buf = io.StringIO()
        with redirect_stdout(buf), patch('time.sleep'), patch(
            'mini_basic.runtime.BASICInterpreter._flush_display',
            lambda *a, **k: None,
        ):
            code = main([
                '--dialect',
                'bbc',
                '--display',
                'null',
                path,
            ])
        self.assertIn(code, (0, EXIT_HOLD_CONSOLE))
        errors = [
            line for line in buf.getvalue().splitlines()
            if line.startswith('?')
        ]
        self.assertEqual(errors, [], f'CLI errors: {errors[:5]}')

    def test_cli_run_command_script(self):
        import os
        import tempfile

        import mini_basic

        with tempfile.TemporaryDirectory() as tmp:
            bas_path = os.path.join(tmp, 'prog.bas')
            mbs_path = os.path.join(tmp, 'run.mbs')
            with open(bas_path, 'w', encoding='utf-8') as handle:
                handle.write('PRINT "from script"\nEND\n')
            with open(mbs_path, 'w', encoding='utf-8') as handle:
                handle.write('LOAD prog.bas\nRUN\n')

            interp = BASICInterpreter()
            interp.working_dir = tmp
            buf = io.StringIO()
            with redirect_stdout(buf):
                status = mini_basic._run_command_script(interp, mbs_path)
            self.assertEqual(status, 0)
            self.assertIn('from script', buf.getvalue())

    def _run_loaded_program(self, interp, inputs=None):
        pending = list(inputs or [])

        def fake_input(prompt=''):
            if pending:
                return pending.pop(0)
            raise EOFError('session complete')

        with patch('builtins.input', side_effect=fake_input):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.run()
            return buf.getvalue()

    def test_eliza_loads_and_greets(self):
        path = os.path.join(_CORPUS_ROOT, 'ELIZA.BAS')
        self.assertTrue(os.path.exists(path), msg=path)
        config = InterpreterConfig(dialect='mits')
        interp = BASICInterpreter(config)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.load(path)
        self.assertGreater(len(interp.program), 50)
        out = self._run_loaded_program(interp, inputs=['Men are all alike'])
        self.assertIn("HI!  I'M ELIZA", out)
        self.assertIn('IN WHAT WAY?', out)

    def test_beth_loads_and_greets(self):
        path = os.path.join(_CORPUS_ROOT, 'BETH.BAS')
        self.assertTrue(os.path.exists(path), msg=path)
        config = InterpreterConfig(dialect='bbc')
        interp = BASICInterpreter(config)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.load(path)
        self.assertGreater(len(interp.program), 50)
        out = self._run_loaded_program(interp, inputs=['Men are all alike'])
        self.assertIn("HI!  I'M BETH", out)
        self.assertIn('IN WHAT WAY?', out)

    def test_on_goto_dispatch(self):
        lines = [
            (10, 'LET C = 2'),
            (20, 'ON C GOTO 100, 200, 300'),
            (30, 'PRINT "skip"'),
            (100, 'PRINT "one"'),
            (110, 'END'),
            (200, 'PRINT "two"'),
            (210, 'END'),
            (300, 'PRINT "three"'),
        ]
        self.assertEqual(self.run_program(lines), 'two')

    def test_on_goto_out_of_range_falls_through(self):
        lines = [
            (10, 'LET C = 9'),
            (20, 'ON C GOTO 100, 200'),
            (30, 'PRINT "ok"'),
            (40, 'END'),
            (100, 'PRINT "one"'),
            (200, 'PRINT "two"'),
        ]
        self.assertEqual(self.run_program(lines), 'ok')

    def test_on_gosub_return(self):
        lines = [
            (10, 'ON 1 GOSUB 100, 200'),
            (20, 'PRINT "back"'),
            (30, 'END'),
            (100, 'PRINT "sub1"'),
            (110, 'RETURN'),
            (200, 'PRINT "sub2"'),
            (210, 'RETURN'),
        ]
        self.assertEqual(self.run_program(lines), 'sub1\nback')

    def test_dialect_mits_rejects_while_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'bad.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('10 WHILE 1\n20 WEND\n30 END\n')
            config = InterpreterConfig(dialect='mits', strict_dialect=True)
            interp = BASICInterpreter(config)
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.load(path)
            self.assertEqual(len(interp.program), 0)
            self.assertIn('WHILE not allowed', buf.getvalue())

    def test_dialect_commodore_rejects_while_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'bad.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('10 WHILE 1\n20 WEND\n30 END\n')
            config = InterpreterConfig(dialect='commodore', strict_dialect=True)
            interp = BASICInterpreter(config)
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.load(path)
            self.assertEqual(len(interp.program), 0)
            self.assertIn('WHILE not allowed', buf.getvalue())

    def test_dialect_tiny_rejects_while_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'bad.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('10 WHILE 1\n20 WEND\n30 END\n')
            config = InterpreterConfig(dialect='tiny', strict_dialect=True)
            interp = BASICInterpreter(config)
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.load(path)
            self.assertEqual(len(interp.program), 0)
            self.assertIn('WHILE not allowed', buf.getvalue())

    def test_dialect_tiny_rejects_if_then_line_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'bad.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('10 IF 1 THEN 20\n20 END\n')
            config = InterpreterConfig(dialect='tiny', strict_dialect=True)
            interp = BASICInterpreter(config)
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.load(path)
            self.assertEqual(len(interp.program), 0)
            self.assertIn('if then line not allowed', buf.getvalue().lower())

    def test_repl_dialect_commodore(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertTrue(_execute_repl_line(interp, 'DIALECT commodore'))
        self.assertEqual(interp.config.dialect, 'commodore')
        self.assertIn('Dialect: commodore', buf.getvalue())

    def test_shebang_commodore_dialect_hint(self):
        lines, hint = split_dialect_hints(['#!commodore\n', '10 END\n'])
        self.assertIsNotNone(hint)
        assert hint is not None
        self.assertEqual(hint.dialect, 'commodore')
        self.assertEqual(lines, ['10 END\n'])

    def test_repl_dialect_tiny(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertTrue(_execute_repl_line(interp, 'DIALECT tiny'))
        self.assertEqual(interp.config.dialect, 'tiny')
        self.assertIn('Dialect: tiny', buf.getvalue())

    def test_shebang_tiny_dialect_hint(self):
        lines, hint = split_dialect_hints(['#!tiny\n', '10 END\n'])
        self.assertIsNotNone(hint)
        assert hint is not None
        self.assertEqual(hint.dialect, 'tiny')
        self.assertEqual(lines, ['10 END\n'])

    def test_dialect_bbc_allows_goto(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'ok.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('GOTO DONE\nPRINT "skip"\nDONE: END\n')
            config = InterpreterConfig(dialect='bbc', strict_dialect=True)
            interp = BASICInterpreter(config)
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.load(path)
            self.assertEqual(len(interp.program), 3)
            self.assertNotIn('GOTO not allowed', buf.getvalue())

    def test_cli_dialect_flag(self):
        import mini_basic

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'ok.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('PRINT "mits ok"\nEND\n')
            buf = io.StringIO()
            with redirect_stdout(buf):
                status = mini_basic.main(['--dialect', 'mits', path, '--quiet'])
            self.assertEqual(status, mini_basic.EXIT_HOLD_CONSOLE)
            self.assertIn('mits ok', buf.getvalue())

    def test_on_error_goto_resume_next(self):
        lines = [
            (10, 'ON ERROR GOTO 100'),
            (20, 'DATA 1'),
            (30, 'READ A'),
            (40, 'READ B'),
            (50, 'PRINT "done"'),
            (60, 'END'),
            (100, 'PRINT "trap"'),
            (110, 'RESUME NEXT'),
        ]
        out = self.run_program(lines)
        self.assertEqual(out, 'trap\ndone')
        self.assertNotIn('? READ error', out)

    def test_on_error_goto_resume_retry(self):
        lines = [
            (10, 'ON ERROR GOTO 100'),
            (20, 'DATA "hi"'),
            (30, 'READ A$'),
            (40, 'READ B$'),
            (50, 'PRINT A$'),
            (60, 'END'),
            (100, 'RESTORE'),
            (110, 'RESUME'),
        ]
        out = self.run_program(lines)
        self.assertEqual(out, 'hi')
        self.assertNotIn('? READ error', out)

    def test_on_error_goto_0_disables_trap(self):
        lines = [
            (10, 'ON ERROR GOTO 100'),
            (20, 'ON ERROR GOTO 0'),
            (30, 'READ A'),
            (40, 'END'),
            (100, 'PRINT "trap"'),
        ]
        buf = io.StringIO()
        interp = BASICInterpreter()
        for line_num, statement in lines:
            interp.program[line_num] = statement
        with redirect_stdout(buf):
            interp.run()
        out = buf.getvalue()
        self.assertIn('? READ error', out)
        self.assertNotIn('trap', out)

    def test_on_error_sets_erl(self):
        lines = [
            (10, 'ON ERROR GOTO 100'),
            (20, 'READ A'),
            (30, 'END'),
            (100, 'PRINT _erl'),
            (110, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '20')

    def test_question_print_shorthand(self):
        lines = [
            (10, '? "hello"'),
            (20, '? 6 * 7'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines), 'hello\n42')

    def test_question_print_no_space(self):
        lines = [
            (10, '?5'),
            (20, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '5')

    def test_question_print_immediate(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.execute_immediate('? 1, 2, 3')
        self.assertEqual(buf.getvalue(), '         1         2         3\n')

    def test_expand_question_print_helper(self):
        self.assertEqual(BASICInterpreter._expand_question_print('? 5'), 'PRINT 5')
        self.assertEqual(BASICInterpreter._expand_question_print('?5'), 'PRINT 5')
        self.assertEqual(BASICInterpreter._expand_question_print('?'), 'PRINT')
        self.assertEqual(BASICInterpreter._expand_question_print('PRINT 5'), 'PRINT 5')

    def test_renumber_default(self):
        interp = BASICInterpreter()
        interp.set_program_line(100, 'PRINT 1')
        interp.set_program_line(200, 'GOTO 300')
        interp.set_program_line(300, 'END')
        interp.renumber_program()
        self.assertEqual(list(interp.program.keys()), [10, 20, 30])
        self.assertEqual(interp.program[20], 'GOTO 30')

    def test_renumber_start_step(self):
        interp = BASICInterpreter()
        interp.set_program_line(5, 'PRINT "a"')
        interp.set_program_line(15, 'END')
        interp.renumber_program(100, 25)
        self.assertEqual(list(interp.program.keys()), [100, 125])
        self.assertEqual(interp.program[100], 'PRINT "a"')

    def test_renumber_updates_on_error_goto(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, 'ON ERROR GOTO 500')
        interp.set_program_line(20, 'READ A')
        interp.set_program_line(500, 'RESUME NEXT')
        interp.renumber_program(1000, 100)
        self.assertEqual(interp.program[1000], 'ON ERROR GOTO 1200')
        self.assertEqual(interp.program[1100], 'READ A')
        self.assertEqual(interp.program[1200], 'RESUME NEXT')

    def test_renumber_preserves_labels(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, 'GOTO DONE')
        interp.set_program_line(20, 'DONE: END')
        interp.renumber_program(100, 10)
        lines = [(100, interp.program[100]), (110, interp.program[110])]
        run_interp = BASICInterpreter()
        for line_num, statement in lines:
            run_interp.set_program_line(line_num, statement)
        self.assertEqual(self._run_loaded_program(run_interp), '')

    def test_renumber_repl_commands(self):
        interp = BASICInterpreter()
        interp.set_program_line(1, 'PRINT "ok"')
        interp.set_program_line(2, 'END')
        self.assertTrue(_execute_repl_line(interp, 'RENUMBER 100, 10'))
        self.assertEqual(list(interp.program.keys()), [100, 110])
        interp.new()
        interp.set_program_line(5, 'PRINT "ren"')
        interp.set_program_line(6, 'END')
        self.assertTrue(_execute_repl_line(interp, 'REN'))
        self.assertEqual(list(interp.program.keys()), [10, 20])

    def test_parse_renumber_command(self):
        self.assertEqual(_parse_renumber_command('RENUMBER'), (10, 10))
        self.assertEqual(_parse_renumber_command('ren 100'), (100, 10))
        self.assertEqual(_parse_renumber_command('REN 100,50'), (100, 50))
        self.assertIsNone(_parse_renumber_command('RENAME'))
        with self.assertRaises(ValueError):
            _parse_renumber_command('REN 10,0')

    def test_expand_repl_abbrev_dotted(self):
        self.assertEqual(_expand_repl_abbrev('H.'), 'HELP')
        self.assertEqual(_expand_repl_abbrev('L.'), 'LIST')
        self.assertEqual(_expand_repl_abbrev('L. 10-20'), 'LIST 10-20')
        self.assertEqual(_expand_repl_abbrev('LO. prog.bas'), 'LOAD prog.bas')
        self.assertEqual(_expand_repl_abbrev('R.'), 'RUN')
        self.assertEqual(_expand_repl_abbrev('10 L.'), '10 L.')

    def test_expand_repl_abbrev_unique_prefix(self):
        self.assertEqual(_expand_repl_abbrev('LI 100'), 'LIST 100')
        self.assertEqual(_expand_repl_abbrev('LO my.bas'), 'LOAD my.bas')
        self.assertEqual(_expand_repl_abbrev('L'), 'L')

    def test_repl_l_dot_lists_program(self):
        interp = BASICInterpreter()
        interp.set_program_line(10, 'PRINT 1')
        interp.set_program_line(20, 'END')
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertTrue(_execute_repl_line(interp, 'L.'))
        self.assertIn('10 PRINT 1', buf.getvalue())

    def test_repl_help_enters_browser(self):
        interp = BASICInterpreter()
        with patch('mini_basic.runtime._run_help_browser') as browser:
            self.assertTrue(_execute_repl_line(interp, 'H.'))
        browser.assert_called_once()

    def test_help_browser_menu_and_functions(self):
        from mini_basic.repl.help_browser import run_help_browser

        lines = iter(['2', ''])

        def fake_read(_prompt: str) -> str:
            return next(lines)

        buf = io.StringIO()
        with redirect_stdout(buf):
            run_help_browser('', read_line=fake_read)
        out = buf.getvalue()
        self.assertIn('=== HELP menu ===', out)
        self.assertIn('FUNCTIONS', out)
        self.assertIn('SIN(x)', out)

    def test_help_browser_starts_at_topic(self):
        from mini_basic.repl.help_browser import run_help_browser

        lines = iter([''])

        def fake_read(_prompt: str) -> str:
            return next(lines)

        buf = io.StringIO()
        with redirect_stdout(buf):
            run_help_browser('REPL', read_line=fake_read)
        out = buf.getvalue()
        self.assertIn('=== REPL commands ===', out)
        self.assertIn('H.=HELP', out)

    def test_help_browser_empty_line_exits(self):
        from mini_basic.repl.help_browser import run_help_browser

        lines = iter([''])

        def fake_read(_prompt: str) -> str:
            return next(lines)

        buf = io.StringIO()
        with redirect_stdout(buf):
            run_help_browser('', read_line=fake_read)
        self.assertIn('=== HELP menu ===', buf.getvalue())

    def test_help_browser_index_returns_to_menu(self):
        from mini_basic.repl.help_browser import run_help_browser

        lines = iter(['9', '0', ''])

        def fake_read(_prompt: str) -> str:
            return next(lines)

        buf = io.StringIO()
        with redirect_stdout(buf):
            run_help_browser('', read_line=fake_read)
        out = buf.getvalue()
        self.assertEqual(out.count('=== HELP menu ==='), 2)
        self.assertIn('=== REPL commands ===', out)

    def test_help_browser_zero_returns_to_menu(self):
        from mini_basic.repl.help_browser import run_help_browser

        lines = iter(['9', '0', ''])

        def fake_read(_prompt: str) -> str:
            return next(lines)

        buf = io.StringIO()
        with redirect_stdout(buf):
            run_help_browser('', read_line=fake_read)
        out = buf.getvalue()
        self.assertEqual(out.count('=== HELP menu ==='), 2)

    def test_help_browser_menu_rejects_topic_name(self):
        from mini_basic.repl.help_browser import run_help_browser

        lines = iter(['REPL', '2', ''])

        def fake_read(_prompt: str) -> str:
            return next(lines)

        buf = io.StringIO()
        with redirect_stdout(buf):
            run_help_browser('', read_line=fake_read)
        out = buf.getvalue()
        self.assertIn('numbered menu', out)
        self.assertIn('SIN(x)', out)

    def test_help_menu_redraw_accepts_positional_selection(self):
        from mini_basic.repl.help_browser import _print_help_menu

        buf = io.StringIO()
        with redirect_stdout(buf):
            _print_help_menu(3)
        out = buf.getvalue()
        self.assertIn('>  3 STRINGS', out)

    def test_help_modes_topic_lists_implementation_status(self):
        from mini_basic.repl.help_topics import normalize_help_topic, print_help_topic

        self.assertEqual(normalize_help_topic('MODE'), 'MODES')
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_help_topic('MODES')
        out = buf.getvalue()
        self.assertIn('=== BBC MODE n', out)
        self.assertIn('MODE 2   160x256', out)
        self.assertIn('8x8', out)
        self.assertIn('2x4', out)
        self.assertIn('implemented', out)
        self.assertIn('under construction', out)
        self.assertIn('MODE 7   teletext', out)
        self.assertIn('Column guide', out)

    def test_repl_matrix_command(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertTrue(_execute_repl_line(interp, 'MA.'))
        out = buf.getvalue()
        self.assertIn('=== Dialect compatibility ===', out)
        self.assertIn('ELIZA.BAS', out)
        self.assertIn('BETH.BAS', out)
        self.assertIn('ON GOTO / ON GOSUB', out)

    def test_repl_bye_quits(self):
        interp = BASICInterpreter()
        for word in ('bye', 'BYE', 'quit', 'exit', 'goodbye', 'q'):
            with self.subTest(word=word):
                self.assertFalse(_execute_repl_line(interp, word))

    def test_print_dialect_compatibility_matrix(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            _print_dialect_compatibility_matrix()
        out = buf.getvalue()
        self.assertIn('mits', out)
        self.assertIn('commodore', out)
        self.assertIn('tiny', out)
        self.assertIn('IF ... GOTO nn', out)
        self.assertIn('FG$ / BG$ / ANSI colors', out)

    def test_on_error_gosub_return(self):
        lines = [
            (10, 'ON ERROR GOSUB 100'),
            (20, 'READ A'),
            (30, 'PRINT "after"'),
            (40, 'END'),
            (100, 'PRINT "trap"'),
            (110, 'RETURN'),
        ]
        self.assertEqual(self.run_program(lines), 'trap\nafter')

    def test_on_error_gosub_traps_return_without_gosub(self):
        lines = [
            (10, 'ON ERROR GOSUB 200'),
            (20, 'GOTO 200'),
            (30, 'END'),
            (200, 'PRINT "trapped" : RETURN'),
        ]
        self.assertEqual(self.run_program(lines), 'trapped\ntrapped')

    def test_option_base_one_arrays(self):
        lines = [
            (10, 'OPTION BASE 1'),
            (20, 'DIM A(3)'),
            (30, 'A(1) = 10'),
            (40, 'A(3) = 30'),
            (50, 'PRINT A(1), A(3)'),
            (60, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '        10        30')

    def test_defint_implicit_integer(self):
        lines = [
            (10, 'DEFINT A-Z'),
            (20, 'I = 7'),
            (30, 'PRINT I, I%'),
            (40, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '         7         7')

    def test_fn_scalar_product_array_params(self):
        lines = [
            (10, 'DIM A%(1)'),
            (20, 'DIM B%(1)'),
            (30, 'A%(0)=3: A%(1)=4'),
            (40, 'B%(0)=5: B%(1)=6'),
            (50, 'PRINT FNscalar_product(A%(), B%())'),
            (60, 'END'),
            (100, 'DEF FNscalar_product(A%(), B%())'),
            (110, 'LOCAL I%, S%'),
            (120, 'S%=0'),
            (130, 'FOR I%=0 TO 1'),
            (140, 'S%=S%+A%(I%)*B%(I%)'),
            (150, 'NEXT'),
            (160, '=S%'),
            (170, 'END DEF'),
        ]
        self.assertEqual(self.run_program(lines), '39')

    def test_whole_array_copy(self):
        lines = [
            (10, 'DIM A%(1,1)'),
            (20, 'DIM Q%(1,1)'),
            (30, 'A%(0,0)=7'),
            (40, 'Q%()=A%()'),
            (50, 'PRINT Q%(0,0)'),
            (60, 'END'),
        ]
        self.assertEqual(self.run_program(lines).strip(), '7')

    def test_whole_array_fill_binary_literal(self):
        lines = [
            (10, 'DIM A%(1)'),
            (20, 'A%()=%1111'),
            (30, 'PRINT A%(0); A%(1)'),
            (40, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '1515')

    def test_inkey_timeout_returns_minus_one(self):
        lines = [
            (10, 'PRINT INKEY(1)'),
            (20, 'END'),
        ]
        with patch.object(BASICInterpreter, '_inkey_value', return_value=''):
            self.assertEqual(self.run_program(lines).strip(), '-1')

    def test_inkey_timeout_returns_key_code(self):
        lines = [
            (10, 'PRINT INKEY(100)'),
            (20, 'END'),
        ]
        with patch.object(BASICInterpreter, '_inkey_value', return_value='A'):
            self.assertEqual(self.run_program(lines).strip(), '65')

    def test_bitwise_xor_eqv_imp(self):
        interp = BASICInterpreter()
        self.assertEqual(interp.eval_expr('5 XOR 3'), 6.0)
        self.assertEqual(interp.eval_expr('5 EOR 3'), 6.0)
        self.assertEqual(interp.eval_expr('5 EQV 3'), -7.0)
        self.assertEqual(interp.eval_expr('0 IMP -1'), -1.0)

    def test_div_integer_division(self):
        interp = BASICInterpreter()
        self.assertEqual(interp.eval_expr('17 DIV 5'), 3.0)
        self.assertEqual(interp.eval_expr('-17 DIV 5'), -4.0)

    def test_report_after_trapped_error(self):
        lines = [
            (10, 'ON ERROR GOTO 100'),
            (20, 'READ A'),
            (30, 'END'),
            (100, 'PRINT REPORT$'),
            (110, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '? READ error')

    def test_at_dir_lib_usr_strings(self):
        import os
        import tempfile

        interp = BASICInterpreter()
        with tempfile.TemporaryDirectory() as tmp:
            bas_path = os.path.join(tmp, 'game.bas')
            with open(bas_path, 'w', encoding='utf-8') as handle:
                handle.write('PRINT @dir$\n')
            interp.load(bas_path)
            expected_dir = os.path.normpath(tmp) + os.sep
            self.assertEqual(interp._eval_string_expr('@dir$'), expected_dir)
        self.assertTrue(interp._eval_string_expr('@usr$').endswith(os.sep))
        self.assertTrue(interp._eval_string_expr('@lib$').endswith(os.sep))

    def test_swap_variables_and_array_elements(self):
        lines = [
            (10, 'A%=1: B%=9'),
            (20, 'SWAP A%, B%'),
            (30, 'DIM N%(1)'),
            (40, 'N%(0)=3: N%(1)=7'),
            (50, 'SWAP N%(0), N%(1)'),
            (60, 'PRINT A%; B%; N%(0); N%(1)'),
            (70, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '9173')

    def test_compound_let_increment_and_float_add(self):
        lines = [
            (10, 'I%=0'),
            (20, 'I% += 1'),
            (30, 'c=0.5'),
            (40, 'c += 0.03'),
            (50, 'PRINT I%; c'),
            (60, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '10.53')

    def test_compound_let_all_operators(self):
        lines = [
            (10, 'A%=10'),
            (20, 'A% -= 3'),
            (30, 'A% *= 2'),
            (40, 'A% /= 4'),
            (50, 'LET B$ = "ab"'),
            (60, 'B$ += "cd"'),
            (70, 'DIM N%(0)'),
            (80, 'N%(0)=5'),
            (90, 'N%(0) += 7'),
            (100, 'PRINT A%; B$; N%(0)'),
            (110, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '3abcd12')

    def test_split_at_depth_basic(self):
        interp = BASICInterpreter()
        self.assertEqual(interp._split_at_depth('a,b,c', ','), ['a', 'b', 'c'])
        self.assertEqual(
            interp._split_at_depth('(a,b),c', ','),
            ['(a,b)', 'c'],
        )
        self.assertEqual(interp._split_at_depth('a;b;c', ';'), ['a', 'b', 'c'])
        self.assertEqual(
            interp._split_at_depth('"a"+"b"', '+', skip_empty=True),
            ['"a"', '"b"'],
        )
        self.assertEqual(interp._split_at_depth('', ','), [''])
        self.assertEqual(
            interp._split_at_depth('a,,b', ',', skip_empty=True),
            ['a', 'b'],
        )

    def test_split_at_depth_bbc_strings(self):
        interp = BASICInterpreter()
        self.assertEqual(
            interp._split_at_depth('"a""b",c', ','),
            ['"a""b"', 'c'],
        )
        self.assertEqual(
            interp._split_at_depth('PRINT "x,y",z', ','),
            ['PRINT "x,y"', 'z'],
        )

    def test_split_first_at_depth_basic(self):
        interp = BASICInterpreter()
        self.assertEqual(
            interp._split_first_at_depth('a,b,c', ','),
            ('a', 'b,c'),
        )
        self.assertEqual(
            interp._split_first_at_depth('(a,b),c', ','),
            ('(a,b)', 'c'),
        )
        self.assertEqual(
            interp._split_first_at_depth('a:(b:c)', ':'),
            ('a', '(b:c)'),
        )
        self.assertEqual(interp._split_first_at_depth('', ','), ('', ''))
        self.assertEqual(interp._split_first_at_depth('no delim', ','), ('no delim', ''))

    def test_split_first_at_depth_bbc_strings(self):
        interp = BASICInterpreter()
        self.assertEqual(
            interp._split_first_at_depth('"a""b",c', ','),
            ('"a""b"', 'c'),
        )
        self.assertEqual(
            interp._split_first_at_depth('WHEN "x:y": PRINT', ':'),
            ('WHEN "x:y"', 'PRINT'),
        )

    def test_split_channel_prefix_uses_depth_split(self):
        interp = BASICInterpreter()
        self.assertEqual(
            interp._split_channel_prefix('PRINT#1, "a,b"'),
            ('PRINT#1', '"a,b"'),
        )

    def test_parse_otherwise_spec_colon_in_string(self):
        interp = BASICInterpreter()
        self.assertEqual(
            interp._parse_otherwise_spec('OTHERWISE "a:b": PRINT'),
            ('OTHERWISE "a:b"', 'PRINT'),
        )
        self.assertEqual(
            interp._parse_otherwise_spec('IF A% THEN'),
            ('IF A%', None),
        )

    def test_case_when_endcase_simple_values(self):
        lines = [
            (10, 'A%=2'),
            (20, 'CASE A% OF'),
            (30, 'WHEN 1: PRINT "one"'),
            (40, 'WHEN 2, 3: PRINT "few"'),
            (50, 'OTHERWISE: PRINT "other"'),
            (60, 'ENDCASE'),
            (70, 'END'),
        ]
        self.assertEqual(self.run_program(lines), 'few')

    def test_case_when_endcase_multiline_body(self):
        lines = [
            (10, 'A%=9'),
            (20, 'CASE A% OF'),
            (30, 'WHEN 1 TO 3'),
            (40, 'PRINT "low"'),
            (50, 'WHEN 8 TO 10'),
            (60, 'PRINT "high"'),
            (70, 'OTHERWISE'),
            (80, 'PRINT "mid"'),
            (90, 'ENDCASE'),
            (100, 'END'),
        ]
        self.assertEqual(self.run_program(lines), 'high')

    def test_case_true_of_when_conditions(self):
        lines = [
            (10, 'A%=4'),
            (20, 'CASE TRUE OF'),
            (30, 'WHEN A% < 0: PRINT "neg"'),
            (40, 'WHEN A% > 5: PRINT "big"'),
            (50, 'WHEN A% = 4: PRINT "four"'),
            (60, 'OTHERWISE: PRINT "else"'),
            (70, 'ENDCASE'),
            (80, 'END'),
        ]
        self.assertEqual(self.run_program(lines), 'four')

    def test_case_true_when_inline_without_colon(self):
        lines = [
            (10, 'R%=2'),
            (20, 'CASE TRUE OF'),
            (30, 'WHEN R%<=0.5 A=1: B=2'),
            (40, 'WHEN R%>0.5 A=9: B=2'),
            (50, 'ENDCASE'),
            (60, 'PRINT A; B'),
            (70, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '92')

    def test_shift_operators_in_expressions(self):
        interp = BASICInterpreter()
        interp.int_variables['B'] = 200
        self.assertEqual(interp.eval_expr('B%>>1'), 100.0)
        self.assertEqual(interp.eval_expr('1<<3'), 8.0)

    def test_width_function_and_statement(self):
        lines = [
            (10, 'PRINT WIDTH("ABC")'),
            (20, 'WIDTH 12'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '24')

    def test_mouse_statement_assigns_values(self):
        lines = [
            (10, 'MOUSE X%, Y%, B%'),
            (20, 'PRINT X%; Y%; B%'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '000')

    def test_refresh_off_on_and_star_refresh(self):
        lines = [
            (10, 'OSCLI "REFRESH OFF"'),
            (20, 'OSCLI "REFRESH ON"'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '')

    def test_star_refresh_presents_after_refresh_off(self):
        """wheel.txt: bare *REFRESH must flip the buffer when display is enabled."""
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='pygame', optimization_level=0),
        )
        interp.program = {
            10: 'MODE 8',
            20: 'ORIGIN 640, 512',
            30: 'OSCLI "REFRESH OFF"',
            40: 'GCOL 0, 1',
            50: 'CIRCLEFILL 0, 0, 80',
            60: 'OSCLI "REFRESH"',
            70: 'END',
        }
        with patch('time.sleep'), patch.object(interp, '_shutdown_display', lambda *a, **k: None):
            interp.run()
        display = interp._display
        self.assertFalse(interp._refresh_enabled)
        from mini_basic.display import count_framebuffer_pixels

        pixels = display.capture_framebuffer()
        self.assertGreater(count_framebuffer_pixels(pixels, colour=1), 1000)

    def test_clock_analogue_face_draws_in_mode2_os_coords(self):
        """Clock.bas uses BBC OS units (640,512 centre) scaled to any MODE."""
        import os

        path = os.path.join(_ROOT, 'Clock.bas')
        if not os.path.isfile(path):
            self.skipTest('missing Clock.bas')
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='pygame', optimization_level=0),
        )
        interp.load(path)
        calls = [0]
        orig_wait = interp._execute_wait

        def wait_once(*args, **kwargs):
            calls[0] += 1
            if calls[0] >= 1:
                raise SystemExit()
            return orig_wait(*args, **kwargs)

        interp._execute_wait = wait_once
        with patch('time.sleep'), patch.object(interp, '_shutdown_display', lambda *a, **k: None):
            try:
                interp.run()
            except SystemExit:
                pass
        from mini_basic.display import count_framebuffer_pixels

        display = interp._display
        self.assertEqual(display._mode, 2)
        self.assertFalse(interp._refresh_enabled)
        self.assertTrue(display._use_mos_font())
        pixels = display.capture_framebuffer()
        self.assertGreater(count_framebuffer_pixels(pixels, colour=7), 200)
        self.assertGreater(
            count_framebuffer_pixels(pixels, colour=1)
            + count_framebuffer_pixels(pixels, colour=2)
            + count_framebuffer_pixels(pixels, colour=4),
            10,
        )
        h = display.graphics_height
        w = display.graphics_width
        cx = w // 2
        cy = h // 2
        white = 7
        top = sum(
            1 for y in range(h) for x in range(w)
            if pixels[y][x] == white and y < cy
        )
        bottom = sum(
            1 for y in range(h) for x in range(w)
            if pixels[y][x] == white and y > cy
        )
        left = sum(
            1 for y in range(h) for x in range(w)
            if pixels[y][x] == white and x < cx
        )
        right = sum(
            1 for y in range(h) for x in range(w)
            if pixels[y][x] == white and x > cx
        )
        self.assertGreater(top, 20, 'hour ticks should appear above centre')
        self.assertGreater(bottom, 20, 'hour ticks should appear below centre')
        self.assertGreater(left, 20, 'hour ticks should appear left of centre')
        self.assertGreater(right, 20, 'hour ticks should appear right of centre')

    def test_move_by_and_rectangle_fill(self):
        lines = [
            (10, 'MODE 8'),
            (20, 'GCOL 2'),
            (30, 'MOVE 10, 10'),
            (40, 'MOVE BY 5, 5'),
            (50, 'RECTANGLE FILL 0, 0, 4, 4'),
            (60, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '')

    # [REMOVED for Phase 1 hygiene] Long-running graphics corpus samples test.
    # Moved conceptually to test/manual/ or test/phase2_graphics/ + stuck list.
    # Dedicated bounded graphics tests live in test_bbc_graphics.py etc.

    def test_data_deferred_expression_read(self):
        lines = [
            (10, 'P = 3'),
            (20, 'T = P * 2'),
            (30, 'DATA P, T'),
            (40, 'READ A, B'),
            (50, 'PRINT A; B'),
            (60, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '36')

    def test_data_deferred_read_evaluates_variables(self):
        lines = [
            (10, 'p = 2'),
            (20, 'q = -p'),
            (30, 'DATA p, q, p * 3'),
            (40, 'READ a, b, c'),
            (50, 'PRINT a + b + c'),
            (60, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '6')

    def test_matrix_comma_fill_rotation_y(self):
        from test.bbc_expect import assert_matrix_almost, rotation_matrix_y_degrees

        expected = rotation_matrix_y_degrees(0.5)
        lines = [
            (10, 'DIM b(2,2)'),
            (20, 'b = 0.5'),
            (30, 'b() = COS(b), 0, -SIN(b), 0, 1, 0, SIN(b), 0, COS(b)'),
            (40, 'END'),
        ]
        interp = BASICInterpreter()
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp.run()
        matrix = interp.array_storage[('b', 'float')][2]
        assert_matrix_almost(self, matrix, expected)

    def test_matrix_dot_multiply_matches_left_factor(self):
        from test.bbc_expect import (
            assert_matrix_almost,
            matrix3_identity,
            matrix3_multiply,
            rotation_matrix_y_degrees,
        )

        b = rotation_matrix_y_degrees(0.5)
        expected = matrix3_multiply(b, matrix3_identity())
        lines = [
            (10, 'DIM b(2,2), c(2,2)'),
            (20, 'b = 0.5'),
            (30, 'b() = COS(b), 0, -SIN(b), 0, 1, 0, SIN(b), 0, COS(b)'),
            (40, 'c() = 1, 0, 0, 0, 1, 0, 0, 0, 1'),
            (50, 'c() = b() . c()'),
            (60, 'END'),
        ]
        interp = BASICInterpreter()
        for line_num, statement in lines:
            interp.program[line_num] = statement
        interp.run()
        matrix = interp.array_storage[('c', 'float')][2]
        assert_matrix_almost(self, matrix, expected)

    def test_sum_array_slice_to_range(self):
        lines = [
            (10, 'DIM tmp(2,4)'),
            (20, 'FOR I%=0 TO 4'),
            (30, 'tmp(1,I%)=I%+1'),
            (40, 'NEXT'),
            (50, 'I%=1'),
            (60, 'PRINT SUM(tmp(1, I% TO I%+2))'),
            (70, 'END'),
        ]
        self.assertEqual(self.run_program(lines).strip(), '9')

    def test_sinrad_cosrad_radians(self):
        import math

        lines = [
            (10, 'PRINT SINRAD(PI/2)'),
            (20, 'PRINT COSRAD(0)'),
            (30, 'END'),
        ]
        rows = self.run_program(lines).splitlines()
        self.assertAlmostEqual(float(rows[0]), math.sin(math.pi / 2), places=9)
        self.assertAlmostEqual(float(rows[1]), 1.0, places=9)

    def test_ispal_percent_stub_high_color(self):
        lines = [
            (10, 'IF @ispal% THEN PRINT "pal" ELSE PRINT "hicolor"'),
            (20, 'END'),
        ]
        self.assertEqual(self.run_program(lines).strip(), 'hicolor')

    # [REMOVED for Phase 1] soccerball/wheel/vdu5 graphics verification tests.
    # These exercise internal gfx state + corpus programs. Moved to phase2 / dedicated files
    # (see test_graphics_confirm.py, verify_*.py, examples + test/manual/).

    def test_on_error_oscli_stub(self):
        lines = [
            (10, 'ON ERROR OSCLI "REFRESH ON"'),
            (20, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '')

    def test_on_error_inline_handler_does_not_run_at_setup(self):
        """BBCSDL ON ERROR line must register only; MODE 3/END must not run before line 20."""
        lines = [
            (
                10,
                'ON ERROR OSCLI "REFRESH ON" : IF ERR=17 CHAIN "x" ELSE MODE 3 : PRINT REPORT$ : END',
            ),
            (20, 'PRINT "ok"'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines), 'ok')

    def test_def_fn_acorn_multiline_body(self):
        lines = [
            (10, 'DEF FNtwice(N%)'),
            (20, 'N% = N% * 2'),
            (30, '=N%'),
            (40, 'PRINT FNtwice(5)'),
            (50, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '10')

    def test_val_string_space_functions(self):
        lines = [
            (10, 'PRINT VAL("42px")'),
            (20, 'PRINT STRING$(3, "*")'),
            (30, 'PRINT SPACE$(2); "x"'),
            (40, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '42\n***\n  x')

    def test_line_input_preserves_commas(self):
        lines = [
            (10, 'LINE INPUT "Go:", A$'),
            (20, 'PRINT A$'),
            (30, 'END'),
        ]
        self.assertEqual(
            self.run_program(lines, inputs=['a,b,c']),
            'Go:a,b,c',
        )

    def test_line_input_hash_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'lines.txt')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('one,two\nsecond\n')
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                lines = [
                    (10, 'LET CH = OPENIN("lines.txt")'),
                    (20, 'LINE INPUT#CH, A$'),
                    (30, 'LINE INPUT#CH, B$'),
                    (40, 'PRINT A$; "|"; B$'),
                    (50, 'CLOSE#CH'),
                    (60, 'END'),
                ]
                self.assertEqual(self.run_program(lines), 'one,two|second')
            finally:
                os.chdir(cwd)

    def test_print_using_numeric_format(self):
        lines = [
            (10, 'WCI = 42.37'),
            (20, 'PRINT USING "####.#"; WCI'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '  42.4')

    def test_print_using_format_variable(self):
        lines = [
            (10, 'W$ = "####.#"'),
            (20, 'PRINT USING W$; 7.26'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '   7.3')

    def test_write_hash_file_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                lines = [
                    (10, 'LET CH = OPENOUT("out.csv")'),
                    (20, 'WRITE#CH, 42, "hi"'),
                    (30, 'CLOSE#CH'),
                    (40, 'END'),
                ]
                self.run_program(lines)
                with open('out.csv', encoding='utf-8') as handle:
                    self.assertEqual(handle.read(), '42,"hi"\n')
            finally:
                os.chdir(cwd)

    def test_err_after_on_error_trap(self):
        lines = [
            (10, 'ON ERROR GOTO 100'),
            (20, 'READ A'),
            (30, 'END'),
            (100, 'PRINT ERR, ERL'),
            (110, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '         4        20')

    def test_randomize_reproducible_rnd(self):
        lines = [
            (10, 'RANDOMIZE 42'),
            (20, 'PRINT RND(1)'),
            (30, 'RANDOMIZE 42'),
            (40, 'PRINT RND(1)'),
            (50, 'END'),
        ]
        out = self.run_program(lines).splitlines()
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0], out[1])

    def test_cont_after_stop(self):
        interp = BASICInterpreter()
        lines = [
            (10, 'PRINT "one"'),
            (20, 'STOP'),
            (30, 'PRINT "two"'),
            (40, 'END'),
        ]
        for line_num, statement in lines:
            interp.program[line_num] = statement

        buf1 = io.StringIO()
        with redirect_stdout(buf1):
            interp.run()
        out1 = buf1.getvalue()
        self.assertIn('one', out1)
        self.assertIn('Break in 20', out1)
        self.assertNotIn('two', out1)
        self.assertTrue(interp.stopped)

        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            interp.cont()
        self.assertIn('two', buf2.getvalue())
        self.assertFalse(interp.stopped)

    def test_cant_continue_without_stop(self):
        interp = BASICInterpreter()
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.cont()
        self.assertIn("?Can't continue", buf.getvalue())

    def test_cant_continue_after_new(self):
        interp = BASICInterpreter()
        for line_num, statement in [(10, 'STOP'), (20, 'END')]:
            interp.program[line_num] = statement
        with redirect_stdout(io.StringIO()):
            interp.run()
        interp.new(announce=False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.cont()
        self.assertIn("?Can't continue", buf.getvalue())

    def test_repl_cont_command(self):
        interp = BASICInterpreter()
        interp.program[10] = 'PRINT "x"'
        interp.program[20] = 'STOP'
        interp.program[30] = 'PRINT "y"'
        interp.program[40] = 'END'
        with redirect_stdout(io.StringIO()):
            interp.run()
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertTrue(_execute_repl_line(interp, 'CONT'))
        self.assertIn('y', buf.getvalue())

    def test_inkey_empty_without_key(self):
        lines = [
            (10, 'PRINT "["; INKEY$; "]"'),
            (20, 'END'),
        ]
        with patch.object(BASICInterpreter, '_inkey_value', return_value=''):
            self.assertEqual(self.run_program(lines), '[]')

    def test_inkey_returns_pressed_key(self):
        lines = [
            (10, 'PRINT INKEY$'),
            (20, 'END'),
        ]
        with patch.object(BASICInterpreter, '_inkey_value', return_value='q'):
            self.assertEqual(self.run_program(lines), 'q')

    def test_random_file_io_trand_style(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                lines = [
                    (30, 'OPEN "R", 1, "TESTRAND.DAT", 32'),
                    (40, 'FIELD #1, 10 AS N$, 5 AS A$, 17 AS D$'),
                    (60, 'LSET N$ = "John"'),
                    (70, 'LSET A$ = "25"'),
                    (80, 'LSET D$ = "Engineer"'),
                    (90, 'PUT #1, 1'),
                    (100, 'LSET N$ = "Jane"'),
                    (110, 'LSET A$ = "30"'),
                    (120, 'LSET D$ = "Manager"'),
                    (130, 'PUT #1, 2'),
                    (210, 'GET #1, 1'),
                    (220, 'PRINT "R1:"; N$; "|"; A$'),
                    (290, 'PRINT LOC(1), LOF(1)'),
                    (350, 'GET #1, 2'),
                    (360, 'LSET A$ = "31"'),
                    (370, 'PUT #1, 2'),
                    (380, 'GET #1, 2'),
                    (390, 'PRINT "R2:"; N$; "|"; A$'),
                    (420, 'RSET N$ = "Al"'),
                    (430, 'PRINT "["; N$; "]"'),
                    (450, 'CLOSE #1'),
                    (470, 'END'),
                ]
                out = self.run_program(lines).splitlines()
                self.assertEqual(out[0], 'R1:John      |25   ')
                self.assertEqual(out[1], '         1        64')
                self.assertEqual(out[2], 'R2:Jane      |31   ')
                self.assertEqual(out[3], '[        Al]')
                self.assertTrue(os.path.exists('TESTRAND.DAT'))
            finally:
                os.chdir(cwd)


    def test_file_command_context_load(self):
        ctx = file_command_context('LOAD ')
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.command, 'LOAD')
        self.assertEqual(ctx.partial_path, '')

    def test_file_command_context_save_pretty(self):
        ctx = file_command_context('SAVE PRETTY my')
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.command, 'SAVE')
        self.assertEqual(ctx.partial_path, 'my')

    def test_file_command_context_abbrev_expanded(self):
        self.assertIsNone(file_command_context('LO. '))
        # Abbrev expansion strips trailing space; completer restores it (see configure_readline).
        ctx = file_command_context('LOAD ')
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.command, 'LOAD')

    def test_compute_matches_filters_by_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, 'alpha.bas'), 'w', encoding='utf-8').close()
            open(os.path.join(tmp, 'beta.bas'), 'w', encoding='utf-8').close()
            matches = compute_matches(tmp, 'LOAD a', 'a')
            self.assertEqual(matches, ['alpha.bas'])

    def test_load_completion_includes_subdirectories(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, 'examples'))
            open(os.path.join(tmp, 'examples', 'menu.bas'), 'w', encoding='utf-8').close()
            matches = compute_matches(tmp, 'LOAD e', 'e')
            self.assertIn(f'examples{os.sep}', matches)
            inside = compute_matches(tmp, f'LOAD examples{os.sep}', '')
            self.assertTrue(
                any(name in m for name in ('menu.bas', f'examples{os.sep}menu.bas'))
                for m in inside
            )

    def test_load_save_completion_bas_and_backup_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in (
                'game.bas',
                'old.bak',
                'save.backup',
                'draft.bas~',
                'notes.txt',
                'readme.md',
            ):
                open(os.path.join(tmp, name), 'w', encoding='utf-8').close()
            load_all = compute_matches(tmp, 'LOAD ', '')
            self.assertIn('game.bas', load_all)
            self.assertIn('old.bak', load_all)
            self.assertIn('save.backup', load_all)
            self.assertIn('draft.bas~', load_all)
            self.assertNotIn('notes.txt', load_all)
            self.assertNotIn('readme.md', load_all)
            save_all = compute_matches(tmp, 'SAVE ', '')
            self.assertIn('game.bas', save_all)
            self.assertNotIn('notes.txt', save_all)

    def test_configure_readline_installs_completer(self):
        fake_readline = MagicMock()
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, 'game.bas'), 'w', encoding='utf-8').close()
            ok = configure_readline(
                working_dir=lambda: tmp,
                expand_abbrev=lambda s: s,
                get_readline=lambda: fake_readline,
            )
            self.assertTrue(ok)
            fake_readline.set_completer_delims.assert_called_once()
            fake_readline.set_completer.assert_called_once()
            completer = fake_readline.set_completer.call_args[0][0]
            fake_readline.get_line_buffer.return_value = 'LOAD '
            fake_readline.get_endidx.return_value = 6
            self.assertEqual(completer('', 0), 'game.bas')
            self.assertIsNone(completer('', 1))

    def test_interactive_repl_configures_readline(self):
        interp = BASICInterpreter()
        fake_readline = MagicMock()
        # Force the readline/input() path (Windows would otherwise use windows_repl_input).
        with patch('mini_basic.runtime.sys.platform', 'linux'):
            with patch('mini_basic.runtime._get_readline_module', return_value=fake_readline):
                with patch('mini_basic.runtime._configure_repl_readline', return_value=True) as configure:
                    with patch('builtins.input', side_effect=['QUIT']):
                        from mini_basic import _interactive_repl
                        _interactive_repl(interp)
        configure.assert_called_once()

    def test_windows_repl_input_history_up_down(self):
        history: list[str] = []
        history.extend(['FIRST', 'SECOND'])

        def fake_getwch():
            if fake_getwch.calls:  # type: ignore[attr-defined]
                return fake_getwch.calls.pop(0)  # type: ignore[attr-defined]
            return '\n'

        fake_getwch.calls = ['\xe0', 'H', '\n']  # type: ignore[attr-defined]
        result = windows_repl_input(
            '> ',
            working_dir=lambda: '.',
            expand_abbrev=lambda s: s,
            getwch=fake_getwch,
            history=history,
        )
        self.assertEqual(result, 'SECOND')
        self.assertEqual(len(history), 2)

        fake_getwch.calls = ['\xe0', 'H', '\xe0', 'H', '\n']  # type: ignore[attr-defined]
        result = windows_repl_input(
            '> ',
            working_dir=lambda: '.',
            expand_abbrev=lambda s: s,
            getwch=fake_getwch,
            history=history,
        )
        self.assertEqual(result, 'FIRST')

    def test_windows_repl_input_tab_completes_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, 'game.bas'), 'w', encoding='utf-8').close()
            keys = list('LOAD g\t\n')
            result = windows_repl_input(
                '> ',
                working_dir=lambda: tmp,
                expand_abbrev=lambda s: s,
                getwch=lambda: keys.pop(0),
            )
            self.assertEqual(result, 'LOAD game.bas')

    def test_windows_repl_input_tab_cycles_multiple_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('mandelbrot.bas', 'mandelbrot2.bas', 'mandelbrot_color.bas'):
                open(os.path.join(tmp, name), 'w', encoding='utf-8').close()
            keys = list('LOAD Man\t\t\t\n')
            result = windows_repl_input(
                '> ',
                working_dir=lambda: tmp,
                expand_abbrev=lambda s: s,
                getwch=lambda: keys.pop(0),
            )
            self.assertEqual(result, 'LOAD mandelbrot2.bas')

    def test_advance_tab_completion_applies_unique_directory(self):
        matches = [f'examples{os.sep}', f'exercises{os.sep}']
        first, cycle = advance_tab_completion('exampl', matches, None)
        self.assertEqual(first, f'examples{os.sep}')
        self.assertIsNone(cycle)

    def test_accept_unique_completion(self):
        matches = [f'examples{os.sep}', f'exercises{os.sep}']
        self.assertEqual(
            accept_unique_completion('exampl', matches),
            f'examples{os.sep}',
        )
        self.assertIsNone(accept_unique_completion('ex', matches))

    def test_windows_repl_input_right_accepts_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, 'examples'))
            keys = list('LOAD ex\t') + ['\xe0', 'M', '\n']
            result = windows_repl_input(
                '> ',
                working_dir=lambda: tmp,
                expand_abbrev=lambda s: s,
                getwch=lambda: keys.pop(0),
            )
            self.assertEqual(result, f'LOAD examples{os.sep}')

    def test_advance_tab_completion_extends_then_cycles(self):
        matches = ['mandelbrot.bas', 'mandelbrot2.bas', 'mandelbrot_color.bas']
        first, cycle = advance_tab_completion('Man', matches, None)
        self.assertEqual(first, 'mandelbrot')
        second, cycle = advance_tab_completion('mandelbrot', matches, cycle)
        self.assertEqual(second, 'mandelbrot.bas')
        third, cycle = advance_tab_completion('mandelbrot', matches, cycle)
        self.assertEqual(third, 'mandelbrot2.bas')

    def test_compute_matches_prefers_shorter_names_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in (
                'Mandelbrot - ANSI color - no line numbers.bas',
                'mandelbrot.bas',
                'mandelbrot2.bas',
            ):
                open(os.path.join(tmp, name), 'w', encoding='utf-8').close()
            matches = compute_matches(tmp, 'LOAD Man', 'Man')
            self.assertEqual(matches[0], 'mandelbrot.bas')

    def test_interactive_repl_uses_windows_input_on_win32(self):
        interp = BASICInterpreter()
        with patch('mini_basic.runtime._configure_repl_readline', return_value=True):
            with patch('mini_basic.runtime.sys.platform', 'win32'):
                with patch('mini_basic.runtime.sys.stdin.isatty', return_value=True):
                    with patch('mini_basic.repl.windows_input.windows_repl_input', return_value='QUIT') as win_in:
                        from mini_basic import _interactive_repl
                        _interactive_repl(interp)
        win_in.assert_called_once()

    def test_read_string_data_into_string_array(self):
        lines = [
            (10, 'DIM A$(3)'),
            (20, 'FOR I=0 TO 3:READ A$(I):NEXT I'),
            (30, 'PRINT A$(0); A$(3)'),
            (40, 'END'),
            (100, 'DATA 4,hello,world,bye'),
        ]
        self.assertEqual(self.run_program(lines), '4bye')

    def test_compact_if_with_or_condition(self):
        lines = [
            (10, 'Y=5:M=5:N=9:OK=0'),
            (20, 'IF M=Y OR N=Y OK=1'),
            (30, 'PRINT OK'),
            (40, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '1')

    def test_plot_notx_negates_x(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.program = {
            10: 'X=25:Y=30',
            20: 'IF 1 PLOT 69,NOTX,Y',
            30: 'END',
        }
        coords = []

        class _FakeDisplay:
            def plot_code(self, code, x, y):
                coords.append((code, x, y))

            def poll(self):
                return True

            def present(self):
                return None

            def pump_events(self):
                return None

        interp._display = _FakeDisplay()
        interp._display_live = True
        with patch.object(interp, '_ensure_display'), patch.object(
            interp, '_flush_display', lambda *a, **k: None,
        ):
            interp.run()
        self.assertEqual(coords, [(69, -25, 30)])

    def test_himem_lomem_page_defaults(self):
        lines = [
            (10, 'PRINT (HIMEM-LOMEM)/40'),
            (20, 'END'),
        ]
        self.assertEqual(self.run_program(lines), '10000')

    def test_if_else_for_read_data(self):
        lines = [
            (10, 'MAX=10'),
            (11, 'DIM A$(MAX)'),
            (15, 'X=0'),
            (16, 'IF X<>0 PROCskip ELSE FOR I=0 TO 3:READ A$(I):NEXT I'),
            (20, 'PRINT A$(2)'),
            (30, 'END'),
            (100, 'DATA 4,\\Qfly\\N2\\Y3\\,\\Agoldfish,\\Asparrow,'),
            (200, 'DEF PROCskip'),
            (210, 'ENDPROC'),
        ]
        out = self.run_program(lines)
        self.assertNotIn('? ', out)
        self.assertIn('goldfish', out)

    def test_if_then_for_read_data_fallback(self):
        """animal.txt startup: IF cond THEN FOR... must not leave READ/NEXT as trailing stmts."""
        lines = [
            (10, 'MAX=10'),
            (11, 'DIM A$(MAX)'),
            (15, 'X=0'),
            (16, 'IF X<>0 PROCskip'),
            (17, 'IF A$(0)="" OR LEFT$(A$(1),2)<>"\\Q" THEN FOR I=0 TO 3:READ A$(I):NEXT I'),
            (20, 'PRINT A$(2)'),
            (30, 'END'),
            (100, 'DATA 4,\\Qfly\\N2\\Y3\\,\\Agoldfish,\\Asparrow,'),
            (200, 'DEF PROCskip'),
            (210, 'ENDPROC'),
        ]
        out = self.run_program(lines)
        self.assertNotIn('? ', out)
        self.assertIn('goldfish', out)

    def test_himem_lomem_compiled_assignment(self):
        lines = [
            (10, 'MAX=(HIMEM-LOMEM)/40'),
            (20, 'PRINT MAX'),
            (30, 'END'),
        ]
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        for line_num, statement in lines:
            interp.program[line_num] = statement
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertEqual(buf.getvalue().strip(), '10000')
        self.assertEqual(interp.variables.get('MAX'), 10000.0)

    # [REMOVED for Phase 1] pygame wait/ctrl-c / tee display loop tests.
    # These belong in interactive or phase2 graphics isolation work (test/manual/ or dedicated test_pygame_*).
                self.poll_calls = 0

            def begin_run(self):
                self._open = True

            def end_run(self):
                self._open = False

            def hold_open(self):
                return None

            def pump_events(self):
                self._open = False

            def poll(self):
                self.poll_calls += 1
                return self._open

            def present(self):
                return None

            def mark_dirty(self):
                return None

        interp._display = _ClosingDisplay()
        interp._display_live = True
        with patch.object(interp, '_ensure_display'), patch.object(
            interp, '_flush_program_output', lambda: None,
        ):
            interp.run()
        self.assertGreater(interp._display.poll_calls, 0)
        self.assertFalse(interp._display_live)


if __name__ == "__main__":
    unittest.main()

