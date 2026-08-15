"""Animal-style behaviour as short programs — do not LOAD the full listing."""
from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig
from test.animal_snippets import (
    FNART_LINES,
    FNQUERY_LINES,
    FNSTRIP_LINES,
    bbc_none,
    load_lines,
)

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


class InteractiveAnimalTests(unittest.TestCase):
    def run_program(self, lines, inputs=None):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        for line_num, statement in lines:
            interp.program[line_num] = statement
        inputs = inputs or []
        with patch('builtins.input', side_effect=inputs):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.run()
        return buf.getvalue().rstrip('\n')

    def test_animal_fnstrip_no_restore_read_errors(self):
        interp = load_lines(bbc_none(), FNSTRIP_LINES)
        errors = []

        def traced(msg, line_num, stmt_index=0, **_k):
            errors.append((line_num, msg))

        interp._runtime_error = traced
        fn = interp._lookup_user_function('STRIP')
        result = interp._eval_user_function(fn, ['"ostrich"'])
        self.assertEqual(errors, [])
        self.assertEqual(result, 'ostrich')

    def test_himem_lomem_max_formula(self):
        """animal startup: MAX=(HIMEM-LOMEM)/40 is 10000 in this runtime."""
        interp = bbc_none()
        interp.set_program_line(10, 'MAX=(HIMEM-LOMEM)/40')
        interp.set_program_line(20, 'END')
        interp.run()
        max_val = interp.variables.get('MAX')
        if max_val is None:
            max_val = float(interp.int_variables.get('MAX', 0))
        self.assertEqual(max_val, 10000.0)

    def test_animal_procnew_input_prompt(self):
        interp = bbc_none()
        interp.set_program_line(10, 'INPUT "What animal were you thinking of? ",V$')
        interp.set_program_line(20, 'INPUT "Type your question: ",X$')
        rest = interp.program[10].split(None, 1)[1]
        prompt, vars_ = interp._parse_input_statement(rest)
        self.assertEqual(vars_, ['V$'])
        self.assertIn('What animal were you thinking of', prompt)
        emitted: list[str] = []
        interp._print_program_text = lambda text, newline=False: emitted.append(text)
        interp.print_column = 25
        interp._emit_input_prompt(prompt)
        self.assertEqual(emitted[0], '\n')
        self.assertIn('What animal were you thinking of? ', emitted[1])
        self.assertNotIn('thinkingof', ''.join(emitted))
        rest_q = interp.program[20].split(None, 1)[1]
        prompt_q, vars_q = interp._parse_input_statement(rest_q)
        self.assertEqual(vars_q, ['X$'])
        self.assertIn('Type your question', prompt_q)

    def test_animal_fnquery_exit_on_n(self):
        interp = load_lines(bbc_none(), FNQUERY_LINES)
        cond = 'FNquery("Are you thinking of an animal ")="N"'
        with patch.object(interp, '_read_program_input', return_value='n'):
            self.assertTrue(interp._eval_condition(cond))

    def test_animal_procedures_include_exit(self):
        interp = bbc_none()
        interp.set_program_line(10, 'DEF PROCexit')
        interp.set_program_line(20, 'PRINT "Animals I already know are:"')
        interp.set_program_line(30, 'ENDPROC')
        interp._prepare_run()
        self.assertIn('exit', {k.lower() for k in interp.user_procedures})
        proc = next(p for n, p in interp.user_procedures.items() if n.lower() == 'exit')
        self.assertGreater(proc.body_end, proc.body_start)

    def test_animal_save_on_y_writes_dat_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            usr = tmp + os.sep
            lines = [
                (10, 'DIM A$(3)'),
                (20, 'A$(2)="\\Agoldfish"'),
                (30, 'INPUT A$'),
                (40, 'IF A$="Y" THEN X=OPENOUT(@usr$+"animal.dat"):PRINT#X,A$(2):CLOSE#X:PRINT "Animal data saved."'),
                (50, 'PRINT "Close the game window to exit."'),
                (60, 'END'),
            ]
            interp = bbc_none()
            load_lines(interp, lines)
            interp._bbc_at_usr = lambda: usr
            with patch.object(interp, '_read_program_input', return_value='Y'):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    interp.run()
            out = buf.getvalue()
            self.assertIn('Animal data saved.', out)
            self.assertIn('Close the game window to exit.', out)
            saved = os.path.join(tmp, 'animal.dat')
            self.assertTrue(os.path.isfile(saved))
            self.assertIn('goldfish', open(saved, encoding='utf-8').read())

    def test_animal_fnquery_accepts_y(self):
        interp = load_lines(bbc_none(), FNQUERY_LINES + FNART_LINES + FNSTRIP_LINES)
        errors = []

        def traced(msg, line_num, stmt_index=0, **_k):
            errors.append(msg)

        interp._runtime_error = traced
        with patch.object(interp, '_read_program_input', return_value='y'):
            result = interp._eval_user_function(
                interp._lookup_user_function('QUERY'),
                ['"Are you thinking of an animal ? "'],
            )
        self.assertEqual(errors, [])
        self.assertEqual(result, 'Y')
        for name in ('QUERY', 'ART', 'STRIP', 'NOSPACE'):
            fn = interp._lookup_user_function(name)
            self.assertIsNotNone(fn, name)
            self.assertEqual(fn.return_kind, 'str', name)

    def test_bbc_backslash_string_literal(self):
        interp = bbc_none()
        self.assertEqual(interp._decode_string_literal('"\\"'), '\\')
        self.assertEqual(interp._decode_string_literal('"say ""hi"""'), 'say "hi"')
        self.assertEqual(interp._eval_string_expr('"\\" + "Y"'), '\\Y')

    def test_animal_procquestion_instr_backslash(self):
        interp = bbc_none()
        interp.set_program_line(10, 'Q$="\\QDoes it fly\\N2\\Y3\\"')
        interp.set_program_line(20, 'END')
        interp.run()
        length = int(interp.eval_expr('INSTR(Q$,"\\",3)-3'))
        prompt = interp._eval_string_expr(f'MID$(Q$,3,{length})')
        self.assertEqual(prompt, 'Does it fly')
        interp.str_variables['C'] = 'Y'
        interp._assign('T$', '"\\"+C$')
        self.assertEqual(interp.str_variables['T'], '\\Y')

    def test_animal_fnart_returns_article(self):
        interp = load_lines(bbc_none(), FNART_LINES)
        fn = interp._lookup_user_function('ART')
        self.assertEqual(fn.return_kind, 'str')
        self.assertEqual(interp._eval_user_function(fn, ['"elephant"']), 'an elephant')
        self.assertEqual(interp._eval_user_function(fn, ['"cat"']), 'a cat')

    def test_instr_equals_zero_in_if_condition(self):
        lines = [
            (10, 'A$="Does it fly"'),
            (20, 'IF INSTR(A$,"(Y/N)")=0 THEN PRINT "yes"'),
            (30, 'END'),
        ]
        self.assertEqual(self.run_program(lines), 'yes')

    def test_print_string_concat_with_fn_calls(self):
        lines = [
            (10, 'DIM A$(4)'),
            (11, 'A$(2)="\\Agoldfish"'),
            (12, 'K=2'),
            (13, 'V$="ostrich"'),
            (20, 'PRINT "What question distinguishes "+FNart(V$)+" from "+FNart(MID$(A$(K),3))+"?"'),
            (30, 'END'),
            (100, 'DEF FNart(noun$)'),
            (110, 'IF INSTR("AEIOUaeiou",LEFT$(noun$,1)) THEN = "an "+noun$ ELSE = "a "+noun$'),
        ]
        out = self.run_program(lines)
        self.assertIn(
            'What question distinguishes an ostrich from a goldfish?',
            out,
        )

    def test_animal_fnquery_appends_y_n_hint(self):
        interp = load_lines(bbc_none(), FNQUERY_LINES)
        emitted: list[str] = []

        def capture(text, newline=False, **_kwargs):
            emitted.append(text)

        interp._print_program_text = capture
        with patch.object(interp, '_read_program_input', return_value='y'):
            interp._assign('A$', 'FNquery("Does it fly")')
        self.assertIn('(Y/N)', ''.join(emitted))

    def test_animal_fnquery_concatenated_prompt(self):
        interp = load_lines(bbc_none(), FNQUERY_LINES + FNART_LINES)
        interp.set_program_line(10, 'DIM A$(4)')
        interp.set_program_line(11, 'A$(2)="\\Agoldfish"')
        interp.set_program_line(12, 'K=2')
        interp._prepare_run()
        interp.variables['K'] = 2.0
        interp.execute_line(10, interp.program[10], [10, 11, 12])
        interp.execute_line(11, interp.program[11], [10, 11, 12])
        errors = []

        def traced(msg, line_num, stmt_index=0, **_k):
            errors.append((line_num, msg))

        interp._runtime_error = traced
        with patch.object(interp, '_read_program_input', return_value='n'):
            interp._assign('A$', 'FNquery("Is it "+FNart(MID$(A$(K),3)))')
        self.assertEqual(errors, [])
        self.assertEqual(interp.str_variables.get('A'), 'N')
