import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from mini_basic import BASICInterpreter, InterpreterConfig

from test.test_mini_basic import _CORPUS_ROOT


class InteractiveAnimalTests(unittest.TestCase):
    """Tests involving the classic ANIMAL game (interactive input)."""

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

    def test_animal_fnstrip_no_restore_read_errors(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        errors = []

        def traced(msg, line_num, stmt_index=0):
            errors.append((line_num, msg))

        interp._runtime_error = traced
        result = interp._eval_user_function(
            interp.user_functions['STRIP'],
            ['"ostrich"'],
        )
        self.assertEqual(errors, [])
        self.assertEqual(result, 'ostrich')

    def test_animal_startup_no_errors_with_compiled_exprs(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        buf = io.StringIO()
        line_nums = sorted(interp.program)
        with patch('time.sleep'), patch.object(interp, '_flush_display', lambda *a, **k: None):
            with redirect_stdout(buf):
                for ln in line_nums:
                    if ln < 210:
                        interp.execute_line(ln, interp.program[ln], line_nums)
        out = buf.getvalue()
        errors = [line for line in out.splitlines() if line.startswith('?')]
        self.assertEqual(errors, [], out)
        max_val = interp.variables.get('MAX')
        if max_val is None:
            max_val = float(interp.int_variables.get('MAX', 0))
        self.assertEqual(max_val, 10000.0)

    def test_animal_wrong_guess_prompts_to_teach_new_animal(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='terminal'))
        interp.load(path)
        interp._prepare_run()
        errors: list[str] = []

        def traced(msg, line_num, stmt_index=0, **kwargs):
            errors.append(str(msg))

        interp._runtime_error = traced
        line_nums = sorted(interp.program)
        for ln in line_nums:
            if ln < 210:
                t = interp.program[ln].upper()
                if 'OPENIN' in t or 'PROCread' in t:
                    continue
                with redirect_stdout(io.StringIO()):
                    interp.execute_line(ln, interp.program[ln], line_nums)
        inputs = iter(['y', 'n', 'n', 'platypus', 'Does it lay eggs', 'y'])

        def read_input(*_a, **_k):
            return next(inputs)

        interp.program[290] = 'UNTIL TRUE'
        buf = io.StringIO()
        with patch.object(interp, '_read_program_input', side_effect=read_input), patch(
            'time.sleep',
        ), patch.object(interp, '_flush_display', lambda *a, **k: None):
            with redirect_stdout(buf):
                interp.run()
        out = buf.getvalue()
        self.assertEqual(errors, [], out)
        self.assertIn('Sorry, I guessed', out)
        self.assertIn('What animal were you thinking of?', out)
        self.assertIn('What question distinguishes', out)

    def test_animal_procnew_input_prompt(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        rest = interp.program[370].split(None, 1)[1]
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
        rest_q = interp.program[400].split(None, 1)[1]
        prompt_q, vars_q = interp._parse_input_statement(rest_q)
        self.assertEqual(vars_q, ['X$'])
        self.assertIn('Type your question', prompt_q)

    def test_animal_procnew_print_chained_strings(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        line_nums = sorted(interp.program)
        for ln in line_nums:
            if ln < 200:
                interp.execute_line(ln, interp.program[ln], line_nums)
        interp.str_variables['V'] = 'ostrich'
        interp.variables['K'] = 2.0
        interp.print_column = 0
        line390 = interp.program[390]
        content = line390.split(None, 1)[1]
        text, _, _ = interp._render_print_content(content, '', 0)
        self.assertEqual(
            text,
            'What question distinguishes an ostrich from a goldfish?',
        )

    def test_animal_fnquery_exit_on_n(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        cond = 'FNquery("Are you thinking of an animal ")="N"'
        with patch.object(interp, '_read_program_input', return_value='n'):
            self.assertTrue(interp._eval_condition(cond))

    def test_animal_procedures_include_exit(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        self.assertIn('EXIT', interp.user_procedures)
        proc = interp.user_procedures['EXIT']
        self.assertGreater(proc.body_end, proc.body_start)

    def test_animal_save_on_y_writes_dat_file(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        with tempfile.TemporaryDirectory() as tmp:
            usr = tmp + os.sep
            interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
            interp.load(path)
            interp._prepare_run()
            interp._bbc_at_usr = lambda: usr
            line_nums = sorted(interp.program)
            for ln in line_nums:
                if ln < 200:
                    with redirect_stdout(io.StringIO()):
                        interp.execute_line(ln, interp.program[ln], line_nums)
            inputs = iter(['n', 'y'])

            def read_input(*_args, **_kwargs):
                return next(inputs)

            def stop_wait(*_args, **_kwargs):
                raise KeyboardInterrupt

            buf = io.StringIO()
            with patch.object(interp, '_read_program_input', side_effect=read_input), patch.object(
                interp, '_execute_wait', side_effect=stop_wait,
            ):
                main_loop = next(
                    ln
                    for ln, text in interp.program.items()
                    if 'Are you thinking of an animal' in text and 'PROCexit' in text
                )
                try:
                    with redirect_stdout(buf):
                        interp.execute_line(main_loop, interp.program[main_loop], line_nums)
                except KeyboardInterrupt:
                    pass
            out = buf.getvalue()
            self.assertIn('Animal data saved.', out)
            self.assertIn('Close the game window to exit.', out)
            saved = os.path.join(tmp, 'animal.dat')
            self.assertTrue(os.path.isfile(saved))
            lines = open(saved, encoding='utf-8').read().splitlines()
            self.assertGreaterEqual(len(lines), 4)
            self.assertIn('goldfish', ''.join(lines))

    def test_animal_answer_n_calls_procexit(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        errors: list[str] = []

        def traced(msg, line_num, stmt_index=0):
            errors.append(msg)

        interp._runtime_error = traced
        line_nums = sorted(interp.program)
        main_loop = next(
            ln
            for ln, text in interp.program.items()
            if 'Are you thinking of an animal' in text and 'PROCexit' in text
        )
        for ln in line_nums:
            if ln < 200:
                with redirect_stdout(io.StringIO()):
                    interp.execute_line(ln, interp.program[ln], line_nums)
        inputs = iter(['n', 'n'])

        def read_input(*_args, **_kwargs):
            return next(inputs)

        def stop_wait(*_args, **_kwargs):
            raise KeyboardInterrupt

        with patch.object(interp, '_read_program_input', side_effect=read_input), patch.object(
            interp, '_execute_wait', side_effect=stop_wait,
        ):
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    interp.execute_line(main_loop, interp.program[main_loop], line_nums)
            except KeyboardInterrupt:
                pass
        out = buf.getvalue()
        self.assertEqual(errors, [])
        self.assertIn('Animals I already know', out)
        self.assertNotIn('Does it fly', out)

    def test_animal_fnquery_accepts_y(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        errors = []

        def traced(msg, line_num, stmt_index=0):
            errors.append(msg)

        interp._runtime_error = traced
        with patch.object(interp, '_read_program_input', return_value='y'):
            result = interp._eval_user_function(
                interp.user_functions['QUERY'],
                ['"Are you thinking of an animal ? "'],
            )
        self.assertEqual(errors, [])
        self.assertEqual(result, 'Y')
        for name in ('CONVLC', 'NOSPACE', 'CAPITAL', 'QUERY', 'ART', 'STRIP'):
            fn = interp.user_functions[name]
            self.assertEqual(fn.return_kind, 'str', name)

    def test_bbc_backslash_string_literal(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        self.assertEqual(interp._decode_string_literal('"\\"'), '\\')
        self.assertEqual(interp._decode_string_literal('"say ""hi"""'), 'say "hi"')
        self.assertEqual(
            interp._eval_string_expr('"\\" + "Y"'),
            '\\Y',
        )

    def test_animal_procquestion_instr_backslash(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        line_nums = sorted(interp.program)
        for ln in line_nums:
            if ln < 200:
                interp.execute_line(ln, interp.program[ln], line_nums)
        interp.int_variables['K'] = 1
        interp.str_variables['Q'] = str(interp._array_get('A', 'str', [1]))
        length = int(interp.eval_expr('INSTR(Q$,"\\",3)-3'))
        prompt = interp._eval_string_expr(f'MID$(Q$,3,{length})')
        self.assertEqual(prompt, 'Does it fly')
        interp.str_variables['C'] = 'Y'
        interp._assign('T$', '"\\"+C$')
        self.assertEqual(interp.str_variables['T'], '\\Y')

    def test_animal_fnart_returns_article(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        fn = interp.user_functions['ART']
        self.assertEqual(fn.return_kind, 'str')
        self.assertEqual(
            interp._eval_user_function(fn, ['"elephant"']),
            'an elephant',
        )
        self.assertEqual(
            interp._eval_user_function(fn, ['"cat"']),
            'a cat',
        )

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
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        line_nums = sorted(interp.program)
        for ln in line_nums:
            if ln < 200:
                interp.execute_line(ln, interp.program[ln], line_nums)
        emitted: list[str] = []

        def capture(text, newline=False, **_kwargs):
            emitted.append(text)

        interp._print_program_text = capture
        with patch.object(interp, '_read_program_input', return_value='y'):
            interp._assign('A$', 'FNquery("Does it fly")')
        self.assertIn('(Y/N)', ''.join(emitted))

    def test_animal_fnquery_concatenated_prompt(self):
        path = os.path.join(
            _CORPUS_ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'games',
            'animal.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('animal.txt corpus file missing')
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.load(path)
        interp._prepare_run()
        line_nums = sorted(interp.program)
        for ln in line_nums:
            if ln < 200:
                interp.execute_line(ln, interp.program[ln], line_nums)
        interp.variables['K'] = 2.0
        errors = []

        def traced(msg, line_num, stmt_index=0):
            errors.append((line_num, msg))

        interp._runtime_error = traced
        with patch.object(interp, '_read_program_input', return_value='n'):
            interp._assign(
                'A$',
                'FNquery("Is it "+FNart(MID$(A$(K),3)))',
            )
        self.assertEqual(errors, [])
        self.assertEqual(interp.str_variables.get('A'), 'N')

