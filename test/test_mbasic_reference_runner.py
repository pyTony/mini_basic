"""Reference-runner failures must stay visible rather than becoming smoke passes."""
from pathlib import Path
import subprocess
import sys

import pytest

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]
RUNNER = Path(__file__).parent / 'manual/run_mbasic_reference.py'


@pytest.mark.parametrize('expected, succeeds, suffix', [
    ('hello world\n', True, ''),
    ('hello world\n', True, '\x1a' * 20),
    ('hello  world\n', False, ''),
    ('hello world\nextra\n', False, ''),
])
def test_reference_output_comparison(tmp_path, expected, succeeds, suffix):
    (tmp_path / 'sample.bas').write_text('10 PRINT "hello world"\n' + suffix, encoding='utf-8')
    (tmp_path / 'sample.txt').write_text(expected, encoding='utf-8')
    result = subprocess.run([sys.executable, str(RUNNER), str(tmp_path)],
                            capture_output=True, text=True, timeout=15)
    assert (result.returncode == 0) is succeeds, result.stdout + result.stderr
    if not succeeds:
        assert 'output differs' in result.stdout
        assert 'mini_basic output' in result.stdout


def test_reference_missing_output_fails(tmp_path):
    (tmp_path / 'sample.bas').write_text('10 END\n', encoding='utf-8')
    result = subprocess.run([sys.executable, str(RUNNER), str(tmp_path)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 1
    assert 'missing sample.txt' in result.stdout


def test_reference_program_timeout(tmp_path):
    (tmp_path / 'sample.bas').write_text('10 A=A+1\n20 GOTO 10\n', encoding='utf-8')
    (tmp_path / 'sample.txt').write_text('', encoding='utf-8')
    result = subprocess.run([sys.executable, str(RUNNER), str(tmp_path), '--timeout', '1'],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 1
    assert 'timeout after' in result.stdout


def test_reference_program_writes_are_isolated(tmp_path):
    (tmp_path / 'sample.bas').write_text(
        '10 OPEN "O",1,"OUT.TXT"\n20 PRINT #1,"data"\n30 CLOSE 1\n40 PRINT "done"\n',
        encoding='utf-8',
    )
    (tmp_path / 'sample.txt').write_text('done\n', encoding='utf-8')
    result = subprocess.run([sys.executable, str(RUNNER), str(tmp_path)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / 'OUT.TXT').exists()


def test_handled_error_is_not_a_reference_failure(tmp_path):
    (tmp_path / 'sample.bas').write_text(
        '10 ON ERROR GOTO 100\n20 ERROR 5\n30 PRINT "recovered"\n40 END\n100 RESUME NEXT\n',
        encoding='utf-8',
    )
    (tmp_path / 'sample.txt').write_text('recovered\n', encoding='utf-8')
    result = subprocess.run([sys.executable, str(RUNNER), str(tmp_path)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
