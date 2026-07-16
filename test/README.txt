mini-BASIC tests
================

Run from the project root (mini_basic):

  python -m unittest discover -s test -p "test_*.py" -v

Or a single module:

  python -m unittest test.test_mini_basic -v

Quiet:

  python -m unittest discover -s test -q

Layout
------

  test/test_mini_basic.py   Main suite (150+ tests)
  test/manual/              Scratch scripts, not part of CI discovery

Corpus paths (ELIZA.BAS, BETH.BAS) resolve to the project root automatically.

BBCSDL example corpus (178 programs):

  python test/manual/fetch_bbcsdl_corpus.py
  python -m mini_basic.bbcsdl_scan test/corpus/bbcsdl --tier A
  python -m unittest test.test_bbcsdl_corpus -v

Manual scratch
--------------

  python test/manual/user_prog_scratch.py

Separating stuck tests + regression on previously-passed tests
--------------------------------------------------------------

Some tests (interactive input, pygame/graphics, long-running corpus, display-dependent)
can hang or become "stuck" on certain platforms (e.g. Windows without proper display).

1. Maintain test/stuck_tests.txt (one pattern or dotted test name per line, comments with #).

2. After a full clean run that you trust, the _run_progress.log records what passed.

3. To run *only* previously-passed tests while skipping stuck ones (ideal for quick regression before continuing work):

   python test/run_regression.py -v

   This loads the last successful tests from the log, drops any matching stuck patterns,
   and runs only the regression subset.

You can also combine with the normal discover while excluding stuck patterns via -k (limited)
or by temporarily moving/renaming the stuck test files.

To force a full run (including stuck) use the normal unittest commands above.

Timeouts for long-running / potentially hanging tests
-----------------------------------------------------

Some tests (especially graphics samples with `REPEAT ... UNTIL FALSE` display loops,
corpus runs, or pygame-dependent code) can take a very long time or appear to hang.

The test suite uses two layers of protection:

1. **Internal timeouts** (in `test/test_mini_basic.py`):
   - A helper `_run_with_timeout(...)` (based on `concurrent.futures.ThreadPoolExecutor`)
     is used around execution of risky programs.
   - If a test exceeds the limit it raises `TimeoutError`, which the test can catch
     (treating it as "finished its useful work").
   - This allows the rest of the test suite / regression run to continue.

2. **pytest-timeout** (recommended when using pytest directly):
   ```bash
   pip install pytest-timeout
   pytest --timeout=30 -q test/
   ```
   You can also mark individual tests:
   ```python
   import pytest

   @pytest.mark.timeout(10)
   def test_something_slow(self): ...
   ```

The combination of `stuck_tests.txt` + internal timeouts + `pytest-timeout` means one
misbehaving test no longer blocks the entire run.

See `test/test_mini_basic.py` for the `_run_with_timeout` helper and its usage on
the BBC SDL graphics tier test.

Running regression on only previously-passed tests (skipping stuck ones)
-----------------------------------------------------------------------

After a successful full run, the last passed tests are recorded in test/_run_progress.log.

Use the helper:

  python test/run_regression.py -v

This will:
- Load tests that passed in the *last* recorded run.
- Drop any that match patterns in test/stuck_tests.txt (edit that file to add/remove stuck tests such as interactive_animal, pygame_*, graphics_confirm, etc.).
- Run only the safe regression subset.

This is ideal before continuing development: it avoids re-running potentially stuck/hanging tests (graphics, interactive input, certain corpus) while still verifying that everything that used to pass still passes.

Edit test/stuck_tests.txt to maintain the list of potentially problematic tests (one pattern per line, # for comments).

New testing direction (compositional + generative) - Phased Approach
-------------------------------------------------------------------

**Phase 1 (current priority): Solid non-graphics foundation**
- Core: control flow (FOR/WHILE/REPEAT/IF/CASE/EXIT), expressions (array refs + FN/PROC calls + substitution), DEF FN/PROC (LOCAL arrays/strings, deep nesting), arrays/DIM, DATA/READ, file I/O (OPEN*/PRINT#/INPUT# + errors inside control), REPL/editing (NEW/RENUMBER/AUTO/DELETE/SAVE/LOAD/CHAIN of complex progs + CONT), error recovery (ON ERROR/RESUME/REPORT + state after errors in nests).
- Hypothesis generative tests for programs with 4-5+ levels of nesting/composition.
- Focused files only (test_control_flow.py, test_expressions_arrays_fns.py, test_def_proc_composition.py, test_file_io_composition.py, test_repl_state.py, test_error_recovery.py, test_dialects.py). No new code in god file test_mini_basic.py.
- Non-stuck by design: bounded loops in generators, display='none', no long REPEAT UNTIL FALSE, pytest-timeout + internal _run_with_timeout.
- Parameterize over dialects ('mini' + 'bbc' minimum). Assert invariants (final state matches expectations/Python sim for pure parts, output patterns, correct ? errors + line nums, no resource leaks) + differential testing.
- Drive work from coverage (target _eval_numeric*, _substitute_array_references, _execute_statement control paths, _build_user_*, file channel code, etc.).

**Phase 2 (later): Graphics tests refactor**
- Refactor existing (test_graphics_confirm.py, test_bbc_graphics.py, etc.) with isolation (patch _flush_display/time.sleep/display, use 'terminal' or dummy, bounded/short runs or early exit).
- High-level assertions on internal _gfx state (pixel counts in bounding boxes/regions, color presence, no obvious clipping) + optional reference snapshots.
- New compositional graphics in dedicated files only after Phase 1 solid.
- Keep current graphics-heavy tests in stuck_tests.txt during Phase 1.

Run Phase 1 coverage (exclude graphics):
  python -m pytest --cov=mini_basic.runtime --cov-report=term-missing -q test/ --ignore-glob='*graphics*' --ignore-glob='*display*' --ignore-glob='*pygame*'

See test/test_compositional.py (compositional nesting + file + proc/fn) and test/test_control_flow.py (WHILE/REPEAT/EXIT/IF nests) for Phase 1 examples.
Other safe non-gfx: test_dialect_hint.py, test_dim_memory.py, test_parsing.py, test_unknown_syntax.py, test_save_case.py (use with care).

Practical Phase 1 non-gfx check (focused + regression):
  python -m pytest -q test/test_compositional.py test/test_control_flow.py
  python test/run_regression.py -q

For broader (but still phase-1 safe) runs, also ignore the entries in stuck_tests.txt (animal, agon, save_case, unknown_syntax, etc.).

Run Phase 1 coverage (exclude graphics):
  python -m pytest --cov=mini_basic.runtime --cov-report=term-missing -q test/test_compositional.py test/test_control_flow.py -q --tb=no


Example stuck_tests.txt entry:
  test_interactive_animal
  test_pygame_input_events
  test_graphics_confirm
  test_rotation_integration

# Pygame safety rule (see AGENT_POLICY.txt section 8):
# Autonomous/agent runs MUST avoid creating real pygame windows (use display='none' + SDL_VIDEODRIVER=dummy).
# Always ensure cleanup via ensure_no_pygame_leftovers() to prevent leftover windows.
# Cooperative user-present verification: agent instructs user to run `mini_basic --pygame ...` themselves.
# Never auto-spawn windows during background / scheduled / LLM-only work.