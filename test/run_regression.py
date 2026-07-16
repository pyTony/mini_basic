#!/usr/bin/env python3
"""
Run only previously-passed *non-stuck* tests for fast regression.

Usage:
  python test/run_regression.py -v
  python test/run_regression.py -v --timeout 120

This parses the last full run output saved in test/_run_progress.log (looking for
"... TestName\nok" lines), then drops any whose dotted name matches a pattern in
test/stuck_tests.txt (interactive, pygame, graphics, corpus, etc.).

The result is a quick, reliable subset of tests that passed before and are not
known to be problematic.

Optional --timeout N  : overall timeout in seconds for the regression run.
Individual long-running tests are also protected internally (see graphics test).

You asked for this separation so that "regression before continuing" only re-runs
the safe ones.
"""
import test_logging
test_logging.setup_logging()

import concurrent.futures
import fnmatch
import os
import re
import sys
import unittest

# Ensure no stray pygame windows at start of any regression (per AGENT_POLICY §8)
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
try:
    from mini_basic.display import ensure_no_pygame_leftovers
    ensure_no_pygame_leftovers()
except Exception:
    pass
from typing import List, Set


def _run_suite_with_timeout(suite, runner, timeout_seconds: float = 0):
    """Run the suite, with an optional overall timeout."""
    if timeout_seconds <= 0:
        return runner.run(suite)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(runner.run, suite)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            print(f"\n*** Overall regression timeout after {timeout_seconds}s ***")
            # Return a dummy result that indicates failure due to timeout
            class _TimeoutResult:
                def wasSuccessful(self): return False
            return _TimeoutResult()

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_TEST_DIR)
_LOG_PATH = os.path.join(_TEST_DIR, '_run_progress.log')
_STUCK_PATH = os.path.join(_TEST_DIR, 'stuck_tests.txt')


def load_stuck_patterns() -> List[str]:
    patterns: List[str] = []
    if not os.path.isfile(_STUCK_PATH):
        return patterns
    with open(_STUCK_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                patterns.append(line)
    return patterns


def load_last_passed_tests() -> List[str]:
    """Parse the last test run block in the log and return dotted test names that passed (ok)."""
    if not os.path.isfile(_LOG_PATH):
        print(f"No log at {_LOG_PATH}", file=sys.stderr)
        return []

    with open(_LOG_PATH, encoding='utf-8') as f:
        lines = f.readlines()

    # Find the last run block
    last_run_start = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith('=== test run '):
            last_run_start = i
            break

    if last_run_start < 0:
        print("No test run block found in log", file=sys.stderr)
        return []

    passed: List[str] = []
    # Collect from last run until next run or end
    for i in range(last_run_start + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith('=== test run '):
            break
        # Lines like:   ... test_foo.Bar.test_baz
        # followed by     ok (0.12s) or FAIL
        if line.startswith('... '):
            test_name = line[4:].strip()
            # Next line should be the status
            if i + 1 < len(lines):
                status_line = lines[i + 1].strip()
                if status_line.startswith('ok ') or status_line == 'ok':
                    passed.append(test_name)
    return passed


def filter_tests(test_names: List[str], stuck_patterns: List[str]) -> List[str]:
    filtered = []
    for name in test_names:
        if any(fnmatch.fnmatch(name, pat) or name.startswith(pat) for pat in stuck_patterns):
            continue
        filtered.append(name)
    return filtered


def main() -> int:
    # Ensure we can import test.* even when run from elsewhere
    if _ROOT_DIR not in sys.path:
        sys.path.insert(0, _ROOT_DIR)

    stuck = load_stuck_patterns()
    passed = load_last_passed_tests()

    if not passed:
        print("No previously passed tests found in log. Run a full test first.", file=sys.stderr)
        return 1

    regression = filter_tests(passed, stuck)
    print(f"Found {len(passed)} tests that reported 'ok' in the last full run (from _run_progress.log).")
    print(f"Excluding {len(passed) - len(regression)} that currently match stuck_tests.txt.")
    print(f"Running {len(regression)} regression tests...")
    if len(regression) < len(passed):
        print("(Stuck tests are filtered even if they had 'ok' in the historical log, per the separation you requested.)")

    if not regression:
        print("No regression tests to run after filtering.")
        return 0

    loader = unittest.TestLoader()
    try:
        suite = loader.loadTestsFromNames(regression)
    except Exception as e:
        print(f"Error loading some tests: {e}", file=sys.stderr)
        # Fall back to running what we can
        suite = unittest.TestSuite()
        for name in regression:
            try:
                suite.addTests(loader.loadTestsFromNames([name]))
            except Exception as ee:
                print(f"  Skipping un-loadable: {name} ({ee})", file=sys.stderr)

    runner = unittest.TextTestRunner(verbosity=2 if '-v' in sys.argv or '--verbose' in sys.argv else 1)

    # Optional overall timeout for the regression run (e.g. --timeout 120)
    timeout = 0.0
    for i, arg in enumerate(sys.argv):
        if arg == '--timeout' and i + 1 < len(sys.argv):
            try:
                timeout = float(sys.argv[i + 1])
            except ValueError:
                pass

    result = _run_suite_with_timeout(suite, runner, timeout)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    try:
        code = main()
    finally:
        try:
            from mini_basic.display import ensure_no_pygame_leftovers
            ensure_no_pygame_leftovers()
        except Exception:
            pass
    sys.exit(code)
