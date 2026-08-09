"""BBC BASIC for SDL 2.0 parity when --dialect bbc."""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

# Includes optional pygame display cases — phase2 isolation.
pytestmark = [pytest.mark.phase2, pytest.mark.graphics]


class BBCDialectSDLTests(unittest.TestCase):
    def _run_bbc(self, lines, *, display='none'):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display=display, optimization_level=0),
        )
        for line_num, statement in lines:
            interp.program[line_num] = statement
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        return buf.getvalue().rstrip('\n'), interp

    def test_numbered_program_allowed_without_warning(self):
        buf = io.StringIO()
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        with redirect_stdout(buf):
            interp.load(os.path.join(_ROOT, 'mandelbrot_color_BBC.bas'), announce=True)
        output = buf.getvalue()
        self.assertNotIn('numbered program not allowed', output)

    def test_endwhile_parsed_as_wend(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        cmd, rest = interp._parse_command('ENDWHILE')
        self.assertEqual(cmd, 'WEND')
        self.assertEqual(rest, '')

    def test_endif_parsed_directly(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        cmd, rest = interp._parse_command('ENDIF')
        self.assertEqual(cmd, 'ENDIF')

    def test_split_end_if_normalized_in_bbc_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        cmd, _ = interp._parse_command('END IF')
        self.assertEqual(cmd, 'ENDIF')

    def test_split_end_while_normalized_to_endwhile(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        cmd, _ = interp._parse_command('END WHILE')
        self.assertEqual(cmd, 'WEND')

    def test_break_maps_to_exit_for_in_bbc_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        cmd, rest = interp._parse_command('BREAK')
        self.assertEqual(cmd, 'EXIT')
        self.assertEqual(rest.strip().upper(), 'FOR')

    def test_break_stays_break_in_mini_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none'))
        cmd, rest = interp._parse_command('BREAK')
        self.assertEqual(cmd, 'BREAK')

    def test_on_close_quit_statement(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.program = {10: 'ON CLOSE QUIT', 20: 'END'}
        with redirect_stdout(io.StringIO()):
            interp.run()
        self.assertEqual(interp.on_close_action, 'QUIT')

    def test_colour_two_arguments(self):
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='pygame', optimization_level=0),
        )
        interp.program = {
            10: 'COLOUR 7,0',
            20: 'PRINT "hi"',
            30: 'END',
        }
        with patch('time.sleep'), patch.object(interp, '_shutdown_display', lambda *a, **k: None):
            with redirect_stdout(io.StringIO()):
                interp.run()
        self.assertEqual(interp.text_fg_colour, 7)
        self.assertEqual(interp.text_bg_colour, 0)

    def test_break_in_for_loop_exits_like_exit_for(self):
        out, _ = self._run_bbc([
            (10, 'FOR I = 1 TO 5'),
            (20, 'BREAK'),
            (30, 'NEXT'),
            (40, 'PRINT I'),
            (50, 'END'),
        ])
        self.assertEqual(out, '1')

    def test_inkey_negative_scan_returns_minus_one_when_idle(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        self.assertEqual(interp._inkey_bbc_negative_scan(-256), -1.0)

    def test_inkey_negative_in_expression(self):
        out, _ = self._run_bbc([
            (10, 'PRINT INKEY(-256)'),
            (20, 'END'),
        ])
        self.assertEqual(out, '-1')

    def test_modulo_keyword_in_expressions(self):
        out, _ = self._run_bbc([
            (10, 'PRINT 17 MOD 5'),
            (20, 'END'),
        ])
        self.assertEqual(out, '2')

    def test_cls_print_auto_enables_pygame_for_bbc(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='terminal', optimization_level=0),
        )
        parsed = [(10, 'CLS', 0), (20, 'PRINT "x"', 0)]
        with patch('mini_basic.util.session.session_supports_gui', return_value=True):
            interp._maybe_auto_enable_pygame_display(parsed, announce=False)
        self.assertEqual(interp.config.display, 'pygame')

    def test_repl_graphics_command_auto_enables_pygame(self):
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='terminal', optimization_level=0),
        )
        with patch('mini_basic.util.session.session_supports_gui', return_value=True):
            with patch.object(interp, '_shutdown_display', lambda *a, **k: None):
                with redirect_stdout(io.StringIO()):
                    interp.execute_immediate('MODE 8')
        self.assertEqual(interp.config.display, 'pygame')

    def test_repl_gcol_auto_enables_pygame(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='terminal', optimization_level=0),
        )
        with patch('mini_basic.util.session.session_supports_gui', return_value=True):
            with redirect_stdout(io.StringIO()):
                interp._maybe_auto_enable_pygame_from_text('GCOL 0, 1', announce=False)
        self.assertEqual(interp.config.display, 'pygame')

    def test_tier_a_poem_output_matches_bbc_logical(self):
        """Basic text + TAB output parity for the simplest SDL corpus sample."""
        path = os.path.join(_ROOT, 'test', 'corpus', 'bbcsdl', 'samples', 'tier_a_poem.txt')
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
        )
        interp.load(path)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        out = buf.getvalue().rstrip('\n')
        # Logical: one line of text, then a line with five asterisks (TAB positions consecutive on same line)
        self.assertIn('Hello from MODE 7', out)
        self.assertIn('*****', out)


if __name__ == '__main__':
    unittest.main()