mini-BASIC tests
================

Run from the project root (mini_basic). pytest is preferred; collection is limited
to this test/ tree (see pytest.ini testpaths).

Preferred regression
--------------------

  python -m pytest -q test/test_mini_basic.py --timeout=30

  python -m pytest -q -m "phase1 and not slow" --timeout=20

  python -m pytest -q test/test_mini_basic.py test/test_parsing.py \
    test/test_compositional.py test/test_control_flow.py --timeout=20

MITS dialect / M6502 C-port examples
------------------------------------

  Summary: docs/MITS_IMPLEMENTATION.md (42/48 non-interactive tutorials pass)

  python -m pytest -q -m "m6502_cport" --timeout=30
  python -m pytest -q -m "mits and not slow" --timeout=45

  Markers: mits, m6502_cport, phase0, non_gfx (see pytest.ini)

  Manual: python -m mini_basic -q --dialect mits examples\m6502-cport\01_hello.bas

Control-flow multi-statement regression (must stay green)
---------------------------------------------------------

Saucer/FOR/IF bugs were colon-split + re-entry gaps. Run these after any
control-flow change:

  python -m pytest -q test/test_control_flow.py --timeout=20

Key classes in test/test_control_flow.py (phase1):

  TestForSameLineBody     FOR X=…:S=… body with NEXT later; saucer P/NI;
                          double FOR on one line; multiline + inline
  TestIfColonTail         compact IF false skips colon tail (saucer M/N init
                          + plot); THEN/ELSE colon; silhouette not all points
  TestWhileAndRepeatForms WHILE/WEND multi + same-line WHILE:body:WEND;
                          REPEAT trailing body / fully inline
  TestCaseWhenColon       CASE/WHEN match + colon tail; non-match skip
  TestOnErrorColonTail    ON ERROR multi-statement handler; IF ERR= compiled
  TestRepeatSameLineAndInkey  REPEAT:body:UNTIL + INKEY$ (earlier)
  TestNestedForMatching   hypothesis nested FOR/NEXT (safe_var stems; was skipped)
  TestForCaseSensitiveToVar  case-sensitive ``to`` / ``to0`` loop vars; glued 1TO n

Piechart / OSCLI simple regressions:
  python -m pytest -q test/test_piechart_regression.py --timeout=20
  # or: python -m unittest test.test_piechart_regression -v

  test_piechart_regression.py — ON ERROR IF ERR=; @tmp$; GSAVE/DISPLAY BMP;
  COSa glue; piechart corpus smoke (no OSCLI/NameError)

Also phase1: test_compositional.py, test_parsing.py (IF THEN true colons).

Legacy unittest
---------------

  python -m unittest test.test_mini_basic -v
  python -m unittest discover -s test -p "test_*.py" -q

Layout
------

  test/test_mini_basic.py   Main suite (~360+ tests)
  test/test_compositional.py, test_control_flow.py   Phase 1 foundation
  test/manual/              Scratch scripts (not required for CI)
  test/corpus/              BBCSDL corpus files
  test/corpus_audit_probe.py  Writes CORPUS_AUDIT.txt from CORPUS_RUNNABLE.txt

Corpus paths (ELIZA.BAS, BETH.BAS) resolve to examples/museum/ automatically.

BBCSDL example corpus:

  python test/manual/fetch_bbcsdl_corpus.py
  python -m mini_basic.bbcsdl_scan test/corpus/bbcsdl --tier A
  python test/corpus_audit_probe.py

Manual scratch
--------------

  python test/manual/user_prog_scratch.py

Stuck / slow tests
------------------

Some interactive, pygame, or infinite-loop corpus samples can hang.

1. Maintain test/stuck_tests.txt (one pattern or name per line; # comments).
2. Prefer markers: phase1, non_gfx, graphics, slow (pytest.ini).
3. Do not use run_regression.py (removed); use pytest markers instead.

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

  python -m pytest -q -m "phase1 and not slow" --timeout=20

Prefer pytest markers. stuck_tests.txt still documents hangers for -k filters.

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

**Phase 2: Graphics test isolation (markers live)**
- Suites marked ``pytest.mark.phase2`` + ``graphics`` (excluded from
  ``-m "phase1 and not slow"``):
    test_graphics_confirm, test_display, test_pygame_input_events,
    test_clock_xor_hands, test_animal_text_print, test_bbc_dialect_sdl
- Pure framebuffer math without pygame window: test_bbc_graphics.py is
  phase1 + non_gfx (still runs with phase1).
- Run phase2 (includes phase0+1 via conftest expansion):
    python -m pytest -q -m "phase2 and not slow" --timeout=60
- Or only graphics suites:
    python -m pytest -q -m "graphics and not slow" --timeout=60
- stuck_tests.txt still lists hangers for -k filters.

Run Phase 1 coverage (exclude graphics):
  python -m pytest --cov=mini_basic.runtime --cov-report=term-missing -q test/ --ignore-glob='*graphics*' --ignore-glob='*display*' --ignore-glob='*pygame*'

See test/test_compositional.py (compositional nesting + file + proc/fn) and test/test_control_flow.py (WHILE/REPEAT/EXIT/IF nests) for Phase 1 examples.
Other safe non-gfx: test_dialect_hint.py, test_dim_memory.py, test_parsing.py, test_unknown_syntax.py, test_save_case.py (use with care).

Practical Phase 1 non-gfx check (focused + regression):
  python -m pytest -q test/test_compositional.py test/test_control_flow.py
  python -m pytest -q test/test_control_flow.py::TestForSameLineBody \
    test/test_control_flow.py::TestIfColonTail \
    test/test_control_flow.py::TestWhileAndRepeatForms \
    test/test_control_flow.py::TestCaseWhenColon --timeout=20
  python -m pytest -q -m "phase1 and not slow" --timeout=20

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