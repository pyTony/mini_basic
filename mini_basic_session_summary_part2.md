# mini_basic debugging session — handoff summary, part 2

Continues from the earlier "mini_basic_session_summary.md" (wheel.bas /
soccer-ball / CLS-CLG / *REFRESH / %-suffix regex / alt-screen-buffer /
TerminalDisplay lazy-grid work). This part covers everything since: Towers of
Hanoi, PygameDisplay colour-code garbling, Mandelbrot performance work, and a
long chain of PROC/FN numeric-name parsing bugs found via the OpenGL globe
demo. Ends mid-task — the PROC/FN pattern consolidation is started but not
finished.

## Fixed and confirmed working

1. **`_read_get_char()` (`io.py`) — blocking `GET` never presented pending
   output first.** `PRINT TAB(0,1)"Press SPACE to start": A=GET` never showed
   the prompt before blocking — `_flush_program_output()` only flushes the
   plain text-console buffer, not the pygame display. **Fix**: added
   `self._display.present(force=True)` right before the blocking wait loop,
   inside the `if self._display_enabled():` block. Confirmed fixed via
   screenshot — prompt now visible before the blocking wait.

2. **`_RE_PROC_CALL` / `_RE_DEF_PROC` (`runtime.py`)** — both required
   `[A-Za-z][A-Za-z0-9_]*` for the PROC name, rejecting real BBC BASIC's
   legal numeric PROC names (`PROC 4(...)`, `DEF PROC 4(...)` — genuinely
   valid; `PROC`/`FN` names live in a separate namespace from variables and
   aren't restricted to starting with a letter). **Fix applied**: both
   patterns widened to `[A-Za-z][A-Za-z0-9_]*|[0-9]+`. Confirmed via
   `git diff` — matches exactly.

3. **`RE_FN_CALL` (`expr/patterns.py`)** — same restriction, same fix
   (`{VAR_BASE_PATTERN}|[0-9]+}`). Confirmed applied and working:
   `? FN4(1,2,3,4)` now resolves correctly (was: "no function FN4").

4. **Three more copies of the identical restriction in `defs.py`**:
   `_parse_def_fn_header`, `_def_fn_header_return_suffix`,
   `_parse_def_fn_rest` — all had their own independent
   `{self._VAR_BASE_PATTERN}`-only patterns for the `FN` name. All three
   fixed with the same `|[0-9]+` addition. Confirmed via `git diff` and via
   end-to-end test: `0 DEF FN4(a,b,c,d)=a+b+c+d` / `? FN4(1,2,3,4)` → `10`,
   and `RUN` completes cleanly with no errors.

5. **`PROC` gaining a spurious space before digits in `LIST` output**
   (`bbc_detokenize.py`) — `_KEYWORDS_NEED_SPACE_AFTER` incorrectly included
   `'PROC'`. Real BBC BASIC for SDL2 never spaces `PROC`/`FN` from their
   name, regardless of whether the name starts with a letter or a digit
   (confirmed empirically: `PROCtriangulate` and `PROC4` both render glued in
   real SDL BASIC). Root cause took several wrong turns to find — initially
   suspected a digit-vs-letter branch inside `_needs_space_after_keyword`,
   which turned out to be a red herring; the actual bug was `PROC`'s mere
   *presence* in the set at all. **Fix**: removed `'PROC'` from
   `_KEYWORDS_NEED_SPACE_AFTER`. Confirmed working — `LIST` now shows
   `PROC4(...)` glued, matching real SDL BASIC.
   **Not yet checked**: whether `'FN'` is also in that set — same reasoning
   would apply if so; flagged multiple times as worth checking, never
   confirmed either way.

6. **`_parse_command` memoization (`program.py` / `core.py`)** — profiling
   the Mandelbrot demo (`mandelbrot_archimedes_mode9.bas`, ~200s vs ~3s for
   real SDL BASIC on the identical program) showed `_normalize_bbc_dialect_line`
   and `_parse_command` together consuming ~260s of cumulative time across
   1,375,359 calls — the same handful of hot-loop lines being re-parsed via a
   multi-pass regex pipeline on every single execution rather than once per
   distinct line. **Fix**: added `self._parse_command_cache: Dict[str,
   Tuple[str, str]] = {}`, initialized in both `__init__` (`core.py` — needed
   because `_parse_command` gets called during `load()`/dialect-validation,
   before `_prepare_run()` ever runs) and reset in `_prepare_run()`
   (`program.py`, for clean state on reload). `_parse_command` itself checks
   the cache first and populates it on all three return paths (`PROC` match,
   main `cmd`/`rest` match, and the fallback `('', line.strip())` — the first
   attempt only covered the `PROC` branch, missing the two paths that
   actually carry ~100% of real traffic, which is why the first measurement
   showed zero improvement; caught and fixed).
   **Result**: 200s → 144s (~30% reduction). `_prepare_run()`'s own prep-time
   loop (which already called `_parse_command` once per statement to build
   FOR/WHILE/REPEAT jump tables) now pre-warms the cache for free, so all
   runtime calls are pure hits from the first execution onward.

## Fixed, workaround (not a real interpreter fix)

7. **Mandelbrot's `WHILE CONT AND (I%<MAXITER%)` — 129s in
   `_eval_bbc_boolean_expr`'s recursive-descent chain.** Root cause: the
   expression compiler (`_get_compiled_expr` in `expr.py`) explicitly bails
   out (`raise ValueError('boolean expression')`) whenever it detects a
   logical `AND`/`OR` combining a bare variable with a comparison — this
   shape isn't supported by the compile-to-Python-bytecode backend at all
   (deliberate scope limit, not a bug), so every evaluation falls through to
   the full text-parsing interpreter path instead of a compiled fast path.
   **Workaround applied** (source-level, not an interpreter fix): rewrote the
   loop to avoid the pattern —
   ```basic
   WHILE I% < MAXITER%
     ...
     IF (ZX*ZX+ZY*ZY > 4) THEN EXIT WHILE
   ENDWHILE
   ```
   (note: the escape direction also got flipped by mistake mid-session —
   `< 4` instead of `> 4` — which caused a temporary all-black-screen
   regression; corrected back to `> 4`, the correct Mandelbrot escape test.)
   **Result**: 144s → 126.39s. Confirmed both correctness (renders properly)
   and the timing win.
   **Still open**: the compiler's `AND`/`OR`-of-comparisons limitation itself
   is unfixed — any other program using this very common WHILE-condition
   shape will hit the same slow path. Explicitly deferred; not attempted this
   session.

## Found, root cause identified, NOT yet fixed

8. **`PygameDisplay.write()` doesn't consume BBC VDU colour control codes.**
   Towers-of-Hanoi's discs render as garbled accented characters (`äü`, `é`,
   `à`, `ç`) instead of coloured bars. Root cause: `CHR$17` is `VDU 17`
   (`COLOUR n` — sets a colour and consumes the *next* byte as its parameter,
   never rendered as a glyph itself) in real BBC BASIC. `PygameDisplay`'s
   glyph-writing loop has no case for this — it draws every byte as a
   character, and whatever bitmap font it uses maps bytes 128–159 to
   Latin-1/CP850 accented letters, which is what's showing up.
   **Not fixed** — never got `PygameDisplay.write()`'s actual source pasted
   (repeatedly requested, conversation moved on to other things before it
   arrived). Needed: the method body (`display.py`, roughly lines
   1085–1256) to find the glyph loop and add VDU-code handling (at minimum
   `VDU 17,n`; ideally the broader family — `18` GCOL, `19` palette remap,
   `31` cursor positioning — but `17` alone fixes this specific program).

## Found, root cause identified, fix drafted but NOT yet applied/verified

9. **`_parse_proc_call` (`program.py`, line ~1136) — the actual crash blocking
   the OpenGL globe demo (`world.bbc`).** This is a *separate* function from
   `_RE_PROC_CALL`/`_RE_DEF_PROC` (item 2) — it's what `_execute_statement`
   calls at *runtime* to dispatch an executing `PROC` call (as opposed to
   `_parse_command`'s classification-time regex match). It has its own
   independent copy of the same `{self._VAR_BASE_PATTERN}`-only pattern,
   raising `ValueError('invalid PROC call')` for `PROC4(...)`. This is what
   was actually crashing `world.bbc` on its very first `PROC 4(file%, 6144)`
   call — item 2's fix never touched this code path at all.
   **This makes item 2 the seventh confirmed occurrence** of this exact
   duplicated-regex bug across the codebase (2 in `runtime.py`, 1 in
   `expr/patterns.py`, 3 in `defs.py`, 1 in `program.py`).
   **Fix drafted, not yet confirmed applied**:
   ```python
   rf'^({self._VAR_BASE_PATTERN}|[0-9]+)\s*(?:\((.*)\))?$',
   ```
   replacing the existing `rf'^({self._VAR_BASE_PATTERN})\s*(?:\((.*)\))?$'`
   at `program.py:1137`. **Needs to be applied and `world.bbc` re-run to
   confirm it gets past the `PROC4` call** — this was the last concrete task
   before the session ended for the night.

   Side note on debugging method: this bug took an unusually long detour to
   find because the program appeared to "hang" indefinitely at "Please
   wait..." with 0% CPU. Turned out to be pure output buffering — Python
   block-buffers stdout/stderr when redirected to a file, and the crash
   traceback (which happened almost instantly) was sitting unflushed while
   the interpreter's `hold_open()`/window-idle loop kept the process alive
   indefinitely after the crash was already "handled" further up the stack
   in a way that swallowed it before it could print... actually: the
   `faulthandler.dump_traceback_later` approach initially *also* showed the
   idle-loop stack (because `run()` had already returned — the crash killed
   the run loop, which fell through to normal post-run cleanup/hold-open,
   masking the fact that anything had gone wrong at all). The traceback only
   became visible once `-u` (unbuffered) was used on a plain foreground run.
   **Lesson for next time**: always use `python -u` when redirecting output
   to a file for later inspection, especially for anything that might crash
   fast — block-buffering can make a fast crash look identical to an
   infinite hang.

## Consolidation work — started, not finished

Given seven independent hand-written copies of the same
`[A-Za-z][A-Za-z0-9_]*` (+ digit-name fix) pattern were found across the
session, added a shared constant to prevent an eighth:

```python
# expr/patterns.py
PROC_FN_NAME_PATTERN = rf'({VAR_BASE_PATTERN}|[0-9]+)'
```

**Still needed**:
- Add `'PROC_FN_NAME_PATTERN'` to `patterns.py`'s `__all__` (not yet done —
  currently unexported, unusable from other modules).
- Update `RE_FN_CALL` in the same file to reference the new constant instead
  of its own inline `{VAR_BASE_PATTERN}|[0-9]+}` (note: `PROC_FN_NAME_PATTERN`
  is self-parenthesizing — don't double-wrap when substituting it in).
- Go back through all seven fixed sites (`runtime.py` ×2, `patterns.py` ×1,
  `defs.py` ×3, `program.py` ×1 — plus whichever fix from item 9 above still
  needs applying) and replace their now-duplicated inline patterns with an
  import of `PROC_FN_NAME_PATTERN`, so future edge cases only need fixing in
  one place.
- Files using `self._VAR_BASE_PATTERN` (instance attribute) rather than the
  module-level `VAR_BASE_PATTERN` import will need `PROC_FN_NAME_PATTERN`
  imported alongside it — same caveat about it already containing its own
  parens.

## Git state (as of this session)

Repo is on branch `fix/hanoi-animal-demo-approvals`, pre-existing large
uncommitted working tree — **most of the uncommitted changes are NOT from
this session** (large amounts of unrelated corpus/benchmark tooling,
`WORK_LOG.txt`, `README.md`, feature matrices, a tracked `.pyc` file, and two
`deleted:` entries — `mini_basic/diffcheck.py` and `mini_basic/pyproject.toml`
— that were never explained and are worth checking whether intentional
before anyone commits `-A`).

**Confirmed as this session's work, `git diff`-verified correct**, ready to
commit selectively:
- `mini_basic/runtime.py` — item 2
- `mini_basic/expr/patterns.py` — item 3 (pre-consolidation version)
- `mini_basic/runtime_parts/defs.py` — item 4 (minor formatting cleanup
  suggested: one edit merged two lines together on save; still syntactically
  valid, just ugly — worth a manual tidy before committing)
- `mini_basic/bbc_detokenize.py` — item 5 (also had a leftover commented-out
  `#print(...)  # TEMP` debug line flagged for removal before commit — not
  confirmed removed)
- `mini_basic/runtime_parts/core.py` — item 6 (cache init)
- `mini_basic/runtime_parts/program.py` — item 6 (cache logic) — **will also
  need item 9's fix folded in once applied**, same file

**Not yet reviewed / not confirmed as session work**: `runtime_parts/expr.py`,
`bbc_graphics.py`, `expr/compile.py` — all show as modified in `git status`
but were never `git diff`-checked against what we actually changed this
session. Do this before assuming they're safe to commit alongside the above.

**Suggested commit split** (proposed, not yet executed):
```powershell
git add mini_basic/runtime.py mini_basic/expr/patterns.py mini_basic/runtime_parts/defs.py mini_basic/runtime_parts/program.py
git commit -m "Fix PROC/FN numeric-name parsing (7 duplicate regex sites)"

git add mini_basic/bbc_detokenize.py
git commit -m "Fix PROC gaining spurious space before digits in LIST output"

git add mini_basic/runtime_parts/core.py
git commit -m "Add _parse_command memoization cache (Mandelbrot: 200s -> 126s combined with WHILE-condition workaround)"
```
(`program.py` folded into the first commit above since it'll carry both the
cache logic from item 6 *and* the `_parse_proc_call` fix from item 9 once
applied — split further if preferred.)

## Priority list carried over from before (still open, untouched this session)

- `CHAIN`, `ON ERROR`, `REPORT$` — full implementations
- Multi-line `IF...THEN...ELSE...ENDIF` blocks
- `SGN` (and other numeric functions) called without parentheses — still
  needs `expr/compile.py` inspected, never obtained this session either
- pygame-window-close leaving `self._display` in a broken state after
  `ProgramExit` — still unlocated

## Reference material

`world.bbc` (OpenGL rotating globe, R.T. Russell 2016) is a much heavier
dialect stress-test than `clock.bas` was — beyond the PROC/FN numeric-name
issue, it uses `INSTALL @lib$+"ogllib"`, `ON CLOSE`, `ON MOVE`, `FN_initgl`/
`FN_load3d`/`FN_loadtexture` (real OpenGL bindings), `DIM ... {...}` structure
syntax, and compound `+=` operators. Very likely hits a hard wall at the
`FN_initgl` call even once PROC/FN parsing is fully fixed — genuine OpenGL
rendering is almost certainly not implemented in this interpreter. Worth
treating "does item 9's fix get PROC4/triangulation running" as the
realistic ceiling for this particular demo, not "does the globe actually
spin."
