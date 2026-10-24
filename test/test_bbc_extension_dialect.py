"""A .bbc file selects the bbc dialect without needing a dialect hint line."""
from __future__ import annotations

import os
import tempfile
import unittest

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]

# Tokenized program: a%=3.7 : PRINT a%  (two lines numbered 0)
TOKENIZED = b'\n\x00\x00a%=3.7\r\x08\x00\x00\xf1 a%\r\x04\x00\x00\r\x00\xff\xff'


def _load(name: str, data: bytes, **config) -> str:
    interp = BASICInterpreter(
        InterpreterConfig(display='none', display_locked=True, **config)
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, name)
        with open(path, 'wb') as handle:
            handle.write(data)
        assert interp.load(path, announce=False)
    return interp.config.dialect


class BbcExtensionTests(unittest.TestCase):

    def test_text_bbc_file_selects_bbc(self):
        self.assertEqual(_load('prog.bbc', b'10 PRINT 1\n'), 'bbc')
        self.assertEqual(_load('PROG.BBC', b'10 PRINT 1\n'), 'bbc')

    def test_tokenized_bbc_file_selects_bbc(self):
        self.assertEqual(_load('prog.bbc', TOKENIZED), 'bbc')

    def test_bas_file_keeps_the_default(self):
        self.assertEqual(_load('prog.bas', b'10 PRINT 1\n'), 'mini')

    def test_file_hint_beats_the_extension(self):
        self.assertEqual(_load('prog.bbc', b'1 REM dialect: mits\n10 PRINT 1\n'), 'mits')

    def test_explicit_dialect_beats_the_extension(self):
        self.assertEqual(
            _load('prog.bbc', b'10 PRINT 1\n', dialect='mini', dialect_locked=True),
            'mini',
        )


if __name__ == '__main__':
    unittest.main()
