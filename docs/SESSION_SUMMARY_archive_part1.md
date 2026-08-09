# mini_basic debugging session — handoff summary

Context: working through `wheel.bas` (spinning rainbow wheel) and a soccer-ball
rotation demo in a custom Python BBC BASIC interpreter (`mini_basic`). Also
inspected a real Richard Russell BBC BASIC for SDL2 program (`clock.bas`) to
scope future dialect work. Several real bugs were found and fixed in the
interpreter itself, not just workarounds in the BASIC source.

## Fixed bugs (root cause identified, patch applied or drafted)

1. **`display.py` — swapped tuple unpacking, `IndexError` on non-square modes**
   `bbc_graphics.py` stores dirty pixels as `rgb_dirty.add((sx, sy))` (x first).
   `display.py`'s fast-path present loop unpacked them as
   `for sy, sx in self._gfx.rgb_dirty:` — reversed. Harmless on square canvases;
   crashed with `IndexError: list index out of range` on MODE 8 (640×512) because
   a real `sx` up to 639 got used as a row index against a 512-row array.
   **Fix**: `for sx, sy in self._gfx.rgb_dirty:`.

2. **`wheel.bas` — degrees fed into `SIN`/`COS` (expects radians)**
   `x1% = m1%* SIN(a1%-t%)` used a raw degree value. Symptom: circles scattered
   randomly instead of forming a rotating ring.
   **Fix**: wrap in `RAD()`: `SIN(RAD(a1%-t%))` / `COS(RAD(a1%-t%))`.

3. **`wheel.bas` — all circles converging to one colour**
   `COLOR 1,r%,g%,b%` redefines logical colour slot 1 mode-wide (palette
   remap), so every previously-drawn circle using `GCOL 1` instantly changes
   colour too. Real BBC hardware behaves this way; the interpreter's true-colour
   RGB layer masked it until tested against a real emulator.
   **Fix**: give each of the 6 rainbow bands its own logical colour slot
   (`slot% = band% + 1`, `COLOR slot%,...`, `GCOL slot%`) instead of sharing
   slot 1.

4. **`CLS` used where `CLG` was needed (recurred twice, two different programs)**
   `CLS` clears the *text* screen; `CLG` clears the *graphics* screen. Both
   `wheel.bas` and the soccer-ball program had `CLS`/`REM CLS` where `CLG` was
   needed, causing trails/ghosting since the graphics buffer was never cleared.

5. **Per-line auto-`present()` causing visible mid-frame tearing**
   `execution.py` calls `_flush_display()` after every executed line,
   rate-limited only by wall-clock time (`_present_min_interval`, 1/20s in
   `core.py`), not by logical frame boundaries. Slow pure-Python circle fills
   meant a real present could fire mid-sweep, showing half-drawn frames.
   **Fix**: use the interpreter's existing (previously unused in these
   programs) `*REFRESH OFF` / bare `*REFRESH` mechanism — `*REFRESH OFF` once
   before the animation loop disables per-line auto-present entirely; a bare
   `*REFRESH` once per frame (after all drawing, before `WAIT`) does one atomic
   `present(force=True)`. True double buffering, already implemented in the
   interpreter, just not used in these programs.

6. **`_clear_screen()` (the `CLS` handler in `io.py`) ignored `*REFRESH OFF`**
   Even with `*REFRESH OFF` active, `CLS` unconditionally called
   `self._display.present(force=True)` at the end — flashing a blank frame
   every time `CLS` ran inside an animation loop, defeating the double
   buffering from fix #5.
   **Fix**: gate that forced present on `self._refresh_enabled`, matching how
   `_flush_display` already behaves.

7. **`%`-suffix + following word loses its separating space (root cause of
   several confusing "parse" errors)**
   In `core.py`'s `_space_expr_segment` (used by `LIST` formatting and — more
   importantly — by whatever normalizes lines during load/store, so it affects
   runtime too), this line was far too broad:
   ```python
   segment = re.sub(r'([%$!#]+)\s+(\w)', r'\1\2', segment)
   ```
   Intended to glue a binary-literal `%` onto following digits (`% 1010` →
   `%1010`), but it matched *any* of `%`/`$`/`!`/`#` followed by whitespace and
   *any* word character — so `band% OF` silently became `band%OF`, breaking
   `CASE band% OF`'s header regex (which needs whitespace before `OF`) with a
   generic, unhelpful `? CASE error`. Worked "by accident" in cases like
   `N%DIV 256 OF` only because extra trailing content preserved a later space
   elsewhere in the string.
   **Fix**: narrow to `re.sub(r'%\s+([01])', r'%\1', segment)` — only glue `%`
   to an immediately-following binary digit; drop `$`/`!`/`#` entirely since
   they never act as binary-literal prefixes.

8. **`os.system('cls')` permanently wipes Windows Terminal scrollback**
   `_clear_screen()`'s Windows fallback shelled out to native `cls`, which on
   Windows Terminal/PowerShell 7 purges the entire scrollback buffer, not just
   the visible screen — losing all prior terminal history irrecoverably.
   **Fix (two parts)**:
   - Enter/leave the terminal's **alternate screen buffer** so the
     interpreter's own repaints happen on a disposable canvas and never touch
     real scrollback: `\x1b[?1049h` added to `_ensure_ansi_console()` (after
     ANSI/VT mode is confirmed enabled — must be added *outside* the
     `sys.platform != 'win32'` early-return, so it applies on Linux/Mac too,
     not just Windows), and `\x1b[?1049l` added to `_restore_console()` on
     clean shutdown.
   - Confirmed via debug log that this works: content is discarded (as
     alt-screen is *designed* to do) but real pre-session scrollback is no
     longer destroyed.

## Found but not yet fixed / in progress

9. **`TerminalDisplay` (the default `--display terminal` backend used for
   virtually all interactive REPL sessions) does a full unconditional 30-row
   grid repaint on every single `present()` call** — this is why a bare
   `PRINT "Yes"` visually looks like a screen clear. Root cause chain:
   - `_ensure_display()` (`graphics.py`) always creates a `TerminalDisplay`
     (grid-based) as the default backend — there is no lighter-weight default;
     the plain buffered console path in `io.py` only activates when
     `_program_stdout is not None` (output redirection/tests), never in normal
     interactive use.
   - `TerminalDisplay.present()` has one whole-screen `_dirty` flag, no
     per-row tracking, and `newline()`'s scroll-emulation (`pop(0)` + append
     blank row) means literally every row's content changes on every scroll
     anyway — so per-row dirty-tracking alone wouldn't fix a scrolling REPL.
   - **Agreed fix direction**: make the grid *lazy*. Stream plain text with
     native terminal scrolling (no cursor jumps, no grid) until the program's
     first actual positioning call (`goto()`, which only ever fires from
     `PRINT TAB`, `VDU 31`, `HOME`). At that point — and only then — promote to
     the existing grid-tracked/full-repaint mode, since real BBC programs that
     use positioned output always clear the screen first anyway (confirmed:
     positioned output without a prior clear isn't a realistic use case).
   - Drafted patch (needs to be applied and tested): add `_positioned` flag +
     `_stream_buf` to `TerminalDisplay`; `write()` branches to a new
     `_write_streaming()` method when not yet positioned; `present()` gets an
     early streaming branch; `goto()` promotes to grid mode once, doing a
     visible-only clear (`\x1b[2J\x1b[H`) at the transition; `clear()` (plain
     `CLS`) stays lightweight pre-promotion.

10. **pygame window close leaves the interpreter in a broken state**
    Closing the pygame window mid-session raises `ProgramExit` correctly (via
    `poll()` detecting `pygame.QUIT`), but `self._display`/`self._screen`
    aren't reset — so *any* subsequent REPL statement (even plain `PRINT`)
    crashes with `pygame.error: Surface is not initialized`. Root cause not
    yet located — `_ensure_display()`'s guard (`if self._display is None:`)
    doesn't check whether a previously-created display is still actually
    *open*, so it never recreates one after a close.
    **Not yet fixed** — needs `_ensure_display()` to check `self._display_live`
    /an "is this still open" state, not just object identity, and either
    recreate the display or cleanly fall back to a null/text backend.

## Confirmed working (no fix needed)

- **Chained single-line `IF cond1 IF cond2 stmt`** already works correctly as
  an emergent property of how single-line `IF` re-dispatches its THEN-clause
  as a fresh statement (confirmed via `--debug` trace: outer `IF` evaluates
  `COND='2>1'`, re-executes `THEN='IF 4>2 PRINT "Yes"'` as a new statement,
  which is itself an `IF` and recurses naturally). One cosmetic oddity in the
  debug trace (`ARITH OPERAND: 1 IF 4` during condition-boundary scanning)
  self-corrects and didn't affect the result, but might be worth a look if
  more complex chained conditions ever misbehave.

## Explicitly requested for future work (priority list from user)

- `CHAIN`
- `ON ERROR`
- `REPORT$`
- Multi-line `IF ... THEN ... ELSE ... ENDIF` blocks (currently only
  single-line `IF` confirmed working)
- `SGN` (and likely other numeric functions: `SIN`, `COS`, `ABS`, etc.) called
  **without parentheses** (`SGNc` = `SGN(c)`) — real classic BBC BASIC syntax.
  Currently: `SGN` doesn't appear anywhere in `expr.py`/`core.py`/`execution.py`
  /`io.py`, so its actual implementation (and any bare-call handling) lives in
  `expr/compile.py`, not yet inspected. Existing bare-call handling in
  `_expand_builtin_calls` is special-cased only for a handful of *string*
  functions (`CHR$`, `STR$`, `LEFT$`, `RIGHT$`, `MID$`) — no equivalent exists
  for numeric functions yet. User reported a bare `?` with no message text on
  failure (worse than the normal `? <description> error at line N` format) —
  cause not yet diagnosed; needs `expr/compile.py` plus a verbatim repro to
  pin down.

## Reference material encountered

`clock.bas` (Richard Russell's "realistic analogue clock" demo, BBC BASIC for
SDL2) was inspected as a real-world dialect stress-test. Uses `%%` (genuine
64-bit integer suffix, distinct from 32-bit `%`, needed because `p%%`/`k%%`/
`o%%`/`clock%%` hold real memory addresses) plus `!`/`?` indirection operators,
`DIM var EXT#filehandle`, `OSCLI "LOAD"/"MDISPLAY"` for bitmap I/O, and
`@dir$`/`@lib$`/`@ispal%` system variables. None of this is implemented and
most of it (OS-level bitmap load/display commands specifically) may not be
worth implementing at all — flagged as scope-decision material, not a bug
list.

## Files inspected this session
`display.py`, `bbc_graphics.py`, `bbc_modes.py`, `io.py`, `execution.py`,
`core.py`, `graphics.py`. Not yet inspected: `expr/compile.py` (numeric
function dispatch — needed for the `SGN` item), whatever module defines
`_display_enabled`'s counterpart display-state tracking for the pygame-close
issue (item 10).
