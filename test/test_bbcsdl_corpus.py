"""BBCSDL example corpus blocker scanner tests."""
import os
import sys
import unittest
from pathlib import Path

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic.bbcsdl_scan import (
    format_scan_report,
    scan_bbcsdl_file,
    scan_bbcsdl_source,
    scan_bbcsdl_tree,
)

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]

_SAMPLES = Path(_ROOT) / 'test' / 'corpus' / 'bbcsdl' / 'samples'
_CORPUS = Path(_ROOT) / 'test' / 'corpus' / 'bbcsdl'


class BBCSdlScanTests(unittest.TestCase):
    def test_tier_a_sample_scores_low(self):
        source = (_SAMPLES / 'tier_a_poem.txt').read_text(encoding='utf-8')
        result = scan_bbcsdl_source(source)
        self.assertEqual(result.tier, 'A')
        self.assertLess(result.score, 12)

    def test_tier_c_sample_detects_sdl_blockers(self):
        source = (_SAMPLES / 'tier_c_hangman_stub.txt').read_text(encoding='utf-8')
        result = scan_bbcsdl_source(source)
        names = set(result.blocker_names())
        self.assertIn('SYS', names)
        self.assertIn('INSTALL', names)
        self.assertIn('fn_ptr', names)
        self.assertIn(result.tier, ('C', 'D'))

    def test_scan_tree_samples(self):
        results = scan_bbcsdl_tree(_SAMPLES)
        self.assertEqual(len(results), 2)
        tiers = {item.tier for item in results}
        self.assertIn('A', tiers)

    def test_format_report_nonempty(self):
        results = scan_bbcsdl_tree(_SAMPLES)
        report = format_scan_report(results, limit=10)
        self.assertIn('BBCSDL corpus compatibility scan', report)
        self.assertIn('tier_a_poem.txt', report)

    def test_full_corpus_if_present(self):
        txt_files = list(_CORPUS.rglob('*.txt'))
        # samples + README only => skip
        if len(txt_files) < 10:
            self.skipTest('Run test/manual/fetch_bbcsdl_corpus.py to populate corpus')
        results = scan_bbcsdl_tree(_CORPUS)
        self.assertGreater(len(results), 50)
        tier_a = [item for item in results if item.tier == 'A']
        self.assertGreater(len(tier_a), 0, 'expected some tier-A programs in full corpus')
        report = format_scan_report(sorted(results, key=lambda r: r.score)[:15], limit=15)
        self.assertIn('tier', report.lower())


if __name__ == '__main__':
    unittest.main()