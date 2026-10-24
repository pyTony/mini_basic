"""mits / commodore: PRINT items written with no separator.

MS BASIC lists ``PRINT "THE"K9"KLINGON"`` as three items, exactly as if they
were separated by ``;`` -- so the number prints with its sign space and
trailing space ("THE 15 KLINGON"). The ``;`` is inserted when the line is
entered (canonicalize), so execution needs no extra checks.
"""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]

MS = ('mits', 'commodore')  # the MS BASIC family


def _interp(dialect: str) -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )


def _stored(dialect: str, text: str) -> str:
    interp = _interp(dialect)
    interp.set_program_line(10, text)
    return interp.program[10]


def _run(dialect: str, src: str) -> str:
    interp = _interp(dialect)
    for raw in src.strip().splitlines():
        num, _, text = raw.partition(' ')
        interp.set_program_line(int(num), text)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        interp.run()
    return out.getvalue()


class AdjacentItemSeparatorTests(unittest.TestCase):

    CASES = (
        ('PRINT "A"K9"B"', 'PRINT "A";K9;"B"'),
        ('PRINT"THE"K9"KLINGON WARSHIPS"', 'PRINT"THE";K9;"KLINGON WARSHIPS"'),
        ('PRINT "STARDATE"T0+T9"  THIS GIVES YOU"T9"DAYS."',
         'PRINT "STARDATE";T0+T9;"  THIS GIVES YOU";T9;"DAYS."'),
        ('PRINT "TOTAL"X*2"UNITS"', 'PRINT "TOTAL";X*2;"UNITS"'),
        ('PRINT TAB(10)"X"', 'PRINT TAB(10);"X"'),
        ('PRINT LEFT$("AB",1)"X"', 'PRINT LEFT$("AB",1);"X"'),
        ('PRINT "A"B$', 'PRINT "A";B$'),
        ('IF A THEN PRINT "X"K ELSE PRINT "Y"K', 'IF A THEN PRINT "X";K ELSE PRINT "Y";K'),
        ('A=1:PRINT "X"A:B=2', 'A=1:PRINT "X";A:B=2'),
        ('PRINT "N"K"," "M"', 'PRINT "N";K;"," "M"'),
    )

    UNCHANGED = (
        'PRINT "A";K9;"B"',
        'PRINT "A",K9,"B"',
        'PRINT "A"+B$+"C"',
        'PRINT B$+"C"',
        'PRINT "A";',
        'PRINT "A"',
        'PRINT K9',
        'PRINT',
        'PRINT USING "###";X',
        'PRINT "PRINT"',
        'PRINT "A" "B"',
        'LET A$="X"',
        'DATA "A"K,"B"',
        'REM PRINT "A"K"B"',
        'PRINT -X',
        'PRINT "A"-1',
    )

    def test_separator_is_inserted_in_every_ms_dialect(self):
        for dialect in MS:
            for source, expected in self.CASES:
                self.assertEqual(_stored(dialect, source), expected, msg=(dialect, source))

    def test_forms_that_must_not_change(self):
        for dialect in MS:
            for source in self.UNCHANGED:
                self.assertEqual(_stored(dialect, source), source, msg=(dialect, source))

    def test_canonicalize_is_idempotent(self):
        interp = _interp('mits')
        for source, _ in self.CASES:
            once = interp.canonicalize_program_line(source)
            self.assertEqual(interp.canonicalize_program_line(once), once, msg=source)

    def test_mini_bbc_and_tiny_are_not_touched(self):
        for dialect in ('mini', 'bbc', 'tiny'):
            self.assertEqual(_stored(dialect, 'PRINT "A"K9"B"'), 'PRINT "A"K9"B"')

    def test_numbers_print_with_ms_padding(self):
        for dialect in MS:
            out = _run(
                dialect,
                '10 K9=15 : T0=2800 : T9=30\n'
                '20 PRINT "DESTROY THE"K9"KLINGON WARSHIPS"\n'
                '30 PRINT "ON STARDATE"T0+T9"  THIS GIVES YOU"T9"DAYS."\n'
                '40 PRINT "PHOTON TORPEDOES  "K9\n',
            )
            self.assertEqual(
                out.splitlines(),
                [
                    'DESTROY THE 15 KLINGON WARSHIPS',
                    'ON STARDATE 2830   THIS GIVES YOU 30 DAYS.',
                    'PHOTON TORPEDOES   15 ',
                ],
                msg=dialect,
            )


if __name__ == '__main__':
    unittest.main()
