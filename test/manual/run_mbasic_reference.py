"""Run upstream tests_with_results programs against mini_basic.

Example: python test/manual/run_mbasic_reference.py C:/Users/admin/mbasic
Comparison matches upstream utils/run_tests.py: actual.strip() == expected.strip().
Programs run in isolated temporary directories; upstream files are read only.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import difflib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def worker(program: Path, dialect: str) -> int:
    sys.path.insert(0, str(ROOT))
    from mini_basic import BASICInterpreter, InterpreterConfig

    output, errors = io.StringIO(), io.StringIO()
    error = ''
    with redirect_stdout(output), redirect_stderr(errors):
        try:
            interp = BASICInterpreter(InterpreterConfig(
                dialect=dialect, display='none', display_locked=True,
                identifiers_case_sensitive=False,
            ))
            interp.working_dir = str(Path.cwd())
            emitted_errors = []
            emit_error = interp._emit_error

            def record_error(message):
                emitted_errors.append(message)
                emit_error(message)

            interp._emit_error = record_error
            # CP/M text files may be padded after a Ctrl+Z end-of-file marker.
            source = program.read_text(encoding='utf-8-sig').partition('\x1a')[0]
            for raw in source.splitlines():
                number, separator, statement = raw.strip().partition(' ')
                if not number:
                    continue
                if not separator or not number.isdecimal():
                    raise ValueError(f'Expected numbered BASIC line: {raw!r}')
                interp.set_program_line(int(number), statement)
            interp.run()
            if emitted_errors:
                error = '; '.join(emitted_errors)
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    print(json.dumps({'output': output.getvalue(), 'error': error,
                      'stderr': errors.getvalue()}))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', type=Path,
                        default=ROOT / 'test/corpus/mbasic521',
                        help='MBASIC checkout or tests_with_results directory')
    parser.add_argument('--match', default='*.bas', help='program filename glob')
    parser.add_argument('--timeout', type=float, default=10)
    parser.add_argument('--dialect', choices=('mbasic', 'mits'), default='mbasic')
    parser.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        return worker(args.worker, args.dialect)
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    source = args.source.resolve()
    if (source / 'basic/dev/tests_with_results').is_dir():
        source /= 'basic/dev/tests_with_results'
    programs = sorted(source.glob(args.match))
    if not programs:
        parser.error(f'No programs match {args.match!r} in {source}')
    passed = failed = 0
    for program in programs:
        reference = program.with_suffix('.txt')
        if not reference.is_file():
            print(f'FAIL {program.name}: missing {reference.name}')
            failed += 1
            continue
        try:
            with tempfile.TemporaryDirectory(prefix='mini-mbasic-') as directory:
                result = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()),
                     '--worker', str(program), '--dialect', args.dialect],
                    cwd=directory, stdin=subprocess.DEVNULL,
                    capture_output=True, text=True, encoding='utf-8',
                    timeout=args.timeout,
                )
            if result.returncode:
                raise RuntimeError(result.stderr or f'worker exit {result.returncode}')
            actual = json.loads(result.stdout)
            expected = reference.read_text(encoding='utf-8-sig').strip()
            output = actual['output'].strip()
            if actual['error'] or output != expected:
                failed += 1
                print(f'FAIL {program.name}: {actual["error"] or "output differs"}')
                diff = list(difflib.unified_diff(
                    expected.splitlines(keepends=True), output.splitlines(keepends=True),
                    fromfile=reference.name, tofile='mini_basic output',
                ))
                print(''.join(diff[:80]))
                if len(diff) > 80:
                    print('(diff truncated to 80 lines)')
            else:
                passed += 1
                print(f'PASS {program.name}')
        except subprocess.TimeoutExpired:
            failed += 1
            print(f'FAIL {program.name}: timeout after {args.timeout:g}s')
        except (OSError, ValueError, RuntimeError) as exc:
            failed += 1
            print(f'FAIL {program.name}: {exc}')
    print(f'Results: {passed} passed, {failed} failed, {len(programs)} total')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
