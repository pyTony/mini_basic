"""examples/mini/superstartrek_readable.bas (a mini-dialect port) must behave like the MITS original.

The readable port keeps every line number and only renames variables and turns
numeric jump targets into labels, so with the same random seed and the same
typed commands both listings print the same text (runs of spaces and leading zeros ignored). The comparison needs the
original listing (examples/mits/superstartrek.bas) and is skipped without it.
"""
from __future__ import annotations

import io
import os
import random
import re
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(120)]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(ROOT, 'examples', 'mits', 'superstartrek.bas')
READABLE = os.path.join(ROOT, 'examples', 'mini', 'superstartrek_readable.bas')

SCRIPTS = {
    'tour': 'SRS\nLRS\nDAM\nSHE\n500\nNAV\n3\n2\nPHA\n100\nTOR\n5\nCOM\n0\nCOM\n1\n'
            'COM\n2\nCOM\n3\nCOM\n4\n1,1\n3,3\nCOM\n5\nSRS\nXXX\n',
    'travel': 'NAV\n1\n4\nNAV\n3\n4\nNAV\n5\n2\nSRS\nNAV\n7\n3\nLRS\nSHE\n0\nNAV\n2\n6\n'
              'NAV\n4\n8\nLRS\nDAM\nXXX\n',
    'combat': 'SHE\n1000\nPHA\n300\nPHA\n300\nTOR\n1\nTOR\n2\nTOR\n8\nSRS\nPHA\n50\nXXX\n',
}


def _play(path: str, seed: int, script: str, dialect: str = 'mits') -> tuple[bool, str, str]:
    interp = BASICInterpreter(
        # single_precision off: compare program logic, not MITS 6-digit PRINT.
        InterpreterConfig(dialect=dialect, display='none', display_locked=True,
                          single_precision=False)
    )
    interp._rng = random.Random(seed)
    # Acorn RND(1) draws 32-bit values; use the MITS stream so seeds line up.
    interp._rnd_ms_dialect = lambda: True
    out, err = io.StringIO(), io.StringIO()
    with mock.patch('sys.stdin', io.StringIO(script)):
        with redirect_stdout(out), redirect_stderr(err):
            loaded = interp.load(path, announce=False)
            if loaded:
                interp.run()
    return loaded, out.getvalue(), err.getvalue()


def _squash(text: str) -> str:
    text = re.sub(r'(?<![\d.])0\.', '.', text)  # MITS prints .5, mini 0.5
    return '\n'.join(' '.join(line.split()) for line in text.splitlines())


class ReadableStarTrekTests(unittest.TestCase):

    def test_readable_listing_plays(self):
        loaded, out, err = _play(READABLE, 1, SCRIPTS['tour'], 'mini')
        self.assertTrue(loaded)
        self.assertEqual(err, '')
        self.assertIn('YOUR ORDERS ARE AS FOLLOWS', out)
        self.assertIn('COMMAND? ', out)
        self.assertIn('THE GALAXY', out)  # library computer galaxy map
        self.assertNotIn('rror', out)

    def test_readable_uses_labels_not_numbers_for_jumps(self):
        with open(READABLE, encoding='utf-8') as handle:
            source = handle.read()
        code = [line.partition(' ')[2] for line in source.splitlines()]
        code = [re.sub(r'"[^"]*"', '', c.split(':REM')[0]) for c in code
                if not c.lstrip().startswith('REM')]
        numeric = [c for c in code if re.search(r'\b(GOTO|GOSUB|THEN)\s+\d', c)]
        self.assertEqual(numeric, [])

    @unittest.skipUnless(os.path.isfile(ORIGINAL), 'original listing missing')
    def test_same_output_as_the_original(self):
        for name, script in SCRIPTS.items():
            for seed in (1, 2, 3):
                with self.subTest(script=name, seed=seed):
                    a = _play(READABLE, seed, script, 'mini')
                    b = _play(ORIGINAL, seed, script)
                    self.assertEqual(a[0], b[0])
                    self.assertEqual(a[2], b[2])
                    self.assertEqual(_squash(a[1]), _squash(b[1]))


if __name__ == '__main__':
    unittest.main()
