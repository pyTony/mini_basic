"""Feature matrix generation and content checks."""
from __future__ import annotations

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic.feature_matrices import (
    all_matrix_text,
    array_matrix_rows,
    trigonometry_rows,
    write_matrix_files,
)

pytestmark = [pytest.mark.phase0]


class FeatureMatrixTests(unittest.TestCase):
    def test_matrices_mention_key_features(self):
        text = all_matrix_text()
        self.assertIn('SINRAD', text)
        self.assertIn('CIRCLE FILL', text)
        self.assertIn('soccerball.txt', text)
        self.assertIn('Deferred feature sets', text)
        self.assertIn('DATA expr at READ', text)

    def test_trig_matrix_documents_degrees_vs_radians(self):
        rows = {row[0]: row for row in trigonometry_rows()}
        self.assertEqual(rows['SIN/COS/TAN argument'][1], 'degrees (BB4W)')
        self.assertEqual(rows['SINRAD/COSRAD/TANRAD'][1], 'radians (BB4W/SDL)')

    def test_write_matrix_files(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            paths = write_matrix_files(__import__('pathlib').Path(tmp))
            # 01, 01b, 02–07, ALL_MATRICES
            self.assertEqual(len(paths), 9)
            all_path = __import__('pathlib').Path(tmp) / 'ALL_MATRICES.txt'
            self.assertTrue(all_path.is_file())
            content = all_path.read_text(encoding='utf-8')
            self.assertIn('Array / matrix ops', content)

    def test_array_matrix_lists_dot_multiply(self):
        features = [row[0] for row in array_matrix_rows()]
        self.assertIn('c() = a() . b()', features)


if __name__ == '__main__':
    unittest.main()