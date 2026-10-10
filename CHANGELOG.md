# Changelog (dev branch — full history)

Format: one line per merged PR, newest first, auto-generated from PR descriptions by `scripts/update_changelog.py` (`.github/workflows/update-changelog.yml` refreshes this branch on every PR merged to `main`). `main`'s own `CHANGELOG.md` tracks tagged releases only. See [GitHub Issues](https://github.com/pyTony/mini_basic/issues) for open work.


## 2026-10-10

- [#89](https://github.com/pyTony/mini_basic/pull/89) fix: Russell-format SYS token was loaded as a tab (main backport) — Backport of c4828b4 from the dev line (main has no test/ tree, so the regression tests live on dev). ccaed8b passes byte 0x09 through as whitespace before the keyword lookup, but in Russell-format tokenized .bbc files 0x09 is the SYS keyword, so every SYS statement lost its keyword (41 of 82 tokenized files in the…
- [#88](https://github.com/pyTony/mini_basic/pull/88) Fix/russell sys token

## 2026-10-09

- [#87](https://github.com/pyTony/mini_basic/pull/87) Breakout: add speed% control variable, sub-step ball movement (main) — a single `speedmul%` (percent, 100 = current speed) scales both the serve velocity and the paddle-hit redirect. `PROCmoveball` splits each tick's ball movement into `ballsubsteps%` (3) smaller steps, redrawing (and running wall/paddle/brick collision checks on) each one. `PROCdrawpaddle` moved earlier in the main…
- [#85](https://github.com/pyTony/mini_basic/pull/85) Breakout: pull back ball speed ~25%, add dialect hint (main) — ball speed scaled down ~25% (serve velocity 21/27 → 16/20, paddle-hit redirect multiplier 3/10 → 9/40, minimum redirect 12 → 9). Added `REM dialect: bbc` as the first line so the file self-selects the `bbc` dialect on load, matching the documented hint syntax in `docs/BASIC_VARIANTS.md`.
- [#80](https://github.com/pyTony/mini_basic/pull/80) Normalize star-command spacing on tokenized LOAD (*MUSIC not * MUSIC) — Same as #79, targeting `main` directly (the affected files are identical between `dev` and `main`).
- [#81](https://github.com/pyTony/mini_basic/pull/81) Restore main to its lean release tree — main is pruned back to exactly its pre-leak file set (`.github`, `basics`, `docs`, `mini_basic`, `showcase`, plus the usual root files) while keeping the real fix (already in `mini_basic/runtime_parts/program.py`) and the later sprite-art work (PR #78) intact.
- [#74](https://github.com/pyTony/mini_basic/pull/74) Fix LOAD parsing for bare line numbers and OSCLI spacing — Fix LOAD parsing for bare line numbers and OSCLI spacing.
- [#76](https://github.com/pyTony/mini_basic/pull/76) Fix blank spacer line numbers breaking LOAD/LIST (tokenized .bbc fails, .bas shows ": N" garbling) — Same fix as #75, targeting `main` directly since the affected code (`mini_basic/runtime_parts/program.py`) is identical on both branches (no diff between `dev` and `main` for that file) and the loader bug affects any tokenized `.bbc` or spacer-line `.bas` program, not just the `dev`-only `examples/` assets.
- [#78](https://github.com/pyTony/mini_basic/pull/78) Breakout: wire in sprite art (logo, ball, brick) — &lt;!-- ccr-projects-attribution: {"github_login":"pyTony"} --&gt;

## 2026-10-08

- [#73](https://github.com/pyTony/mini_basic/pull/73) Speed up breakout.bbc game movements — Speed up breakout game movements and fix paddle collision
- [#72](https://github.com/pyTony/mini_basic/pull/72) Breakout: quieter background music, 50% faster ball — `*MUSIC` volume is 20% (a bit more muted), and the ball moves 50% faster — both at serve and in the paddle-hit redirect. Wall and brick bounces just flip the sign of the existing velocity, so they needed no change.
- [#70](https://github.com/pyTony/mini_basic/pull/70) Breakout: music/sample-sound update (missed by #67) + perf fix — &lt;!-- ccr-projects-attribution: {"github_login":"pyTony"} --&gt;

## 2026-10-07

- [#67](https://github.com/pyTony/mini_basic/pull/67) Backport: fix breakout.bbc title text staying on screen, punchier hit sound — a `CLS` before the game loop clears the title text; the hit sample is re-trimmed to a punchier ~280ms transient.
- [#65](https://github.com/pyTony/mini_basic/pull/65) Fix window title bar pushed off screen when window is taller than the display — The vertical clamp now has a floor of `_TITLE_BAR_ESTIMATE` (40px) instead of 0, so the title bar always keeps enough room to stay on screen, even when the window barely fits vertically.
- [#64](https://github.com/pyTony/mini_basic/pull/64) Backport: sample (WAV) playback and the Breakout demo game — backport of `*PLAY` sample playback (PRs #61/#62/#63 on `dev`) plus the finished Breakout game, including the hesitation/stutter fix, narrower playfield, and the sampled paddle-hit sound from Tony's clip. Since `main` has no `examples/` directory at all (it ships only the curated `showcase/`), the game and its two…

## 2026-10-06

- [#57](https://github.com/pyTony/mini_basic/pull/57) Backport: basic SOUND support (pygame tone synthesis) — Companion backport of #54 (merged to `dev`) onto `main`, same change: `SOUND channel,amplitude,pitch,duration` now plays an approximate tone (sine wave; white noise on channel 0, BBC's traditional noise channel) through pygame's mixer instead of being a silent stub. See #54's description for the full before/after…

## 2026-10-05

- [#59](https://github.com/pyTony/mini_basic/pull/59) Fix docs implying graphics isn't for regular users — Tony flagged that the docs wrongly implied graphics mode isn't for regular users — in reality, graphics (`MODE`, pygame window) is the normal way most programs run (the showcase reel is almost entirely pygame demos); it's a separate pip extra only because pygame is a native dependency, not because it's a niche…
- [#55](https://github.com/pyTony/mini_basic/pull/55) Pre-1.0: showcase refinements, SyntaxWarning fixes, pygame deprecation fix — Follow-up to #52, continuing the pre-1.0 release-cleanup thread:
- [#52](https://github.com/pyTony/mini_basic/pull/52) Pre-1.0: fix CIRCLE FILL/VDU19 graphics bugs, remove redundant launcher scripts — - Both graphics bugs are fixed in `mini_basic/bbc_graphics.py` and `mini_basic/display.py` — the non-numpy fallback paths now match the numpy fast paths' handling of the truecolour RGB overlay. Verified against the full `test/test_graphics_confirm.py` + `test/test_display.py` suites on the `dev` branch (companion…
- [#51](https://github.com/pyTony/mini_basic/pull/51) Fix doubled PRINT output in REPL immediate mode — Every immediate-mode PRINT prints exactly once, regardless of whether the expression is a float, a big integer, or wraps a memoized FN call.
- [#49](https://github.com/pyTony/mini_basic/pull/49) Fix --list: launcher drops flags, REM comments with colons get mangled — `./minibasic` forwards all CLI arguments via `"$@"`, so `--list` (and any other flag) reaches the interpreter. The LIST/SAVE statement splitter now stops looking for `:` once a comment starts, taking the rest of the line verbatim, so comments with colons list unchanged.
- [#50](https://github.com/pyTony/mini_basic/pull/50) Fix tab completion for quoted LOAD/SAVE/RUN/CD filenames (main backport) — `LOAD "demo` + Tab completes to `LOAD "demo.bas"`.
- [#47](https://github.com/pyTony/mini_basic/pull/47) Backport: Implement LIBRARY statement; make INSTALL actually load libraries — both `LIBRARY` and `INSTALL` load the named file and merge its `DEF PROC` / `DEF FN` definitions into the running program. The library's own top-level code is never executed — only the definitions become callable, matching real BBC BASIC semantics.
- [#46](https://github.com/pyTony/mini_basic/pull/46) Fix PRINT line-wrap splitting ANSI escape sequences mid-sequence — each row of ANSIColour.bbc's output is emitted as a single unbroken line, with every CSI sequence intact, matching real Brandy's behaviour.

## 2026-10-04

- [#45](https://github.com/pyTony/mini_basic/pull/45) Backport: stop presenting partial frames once WAIT paces the program (main) — Without `*REFRESH` (BBCSDL/BB4W-only, unsupported on real BASIC V/Archimedes), mini_basic presented the screen after every executed line, including mid-draw states — e.g. right after `CLS` but before the shapes drawn afterward. mini_basic's software renderer is slow enough per frame that this showed as a…
- [#43](https://github.com/pyTony/mini_basic/pull/43) Fix PROC unregistered when body has no ENDPROC at end of program — `ANSIColour.bbc` runs correctly and prints the expected ANSI colour grid. `Circle.bbc`'s `PROCcircle` is now found and called correctly (the file still hits two unrelated, pre-existing bugs further in — `DIM mem%15` without parentheses, and the `|mem% = ...` indirection-assignment operator — which are out of scope…
- [#42](https://github.com/pyTony/mini_basic/pull/42) Backport: VDU 19 palette set + fix stale RGB overlay hiding fills (main) — Two chained bugs affected any BBC BASIC program (e.g. `soccerball_bbc_V.bas`) that redefines the background colour with `VDU 19` and then draws filled shapes on top each frame:
- [#39](https://github.com/pyTony/mini_basic/pull/39) Fix bare WAIT (no argument) raising a runtime error (backport to main) — `WAIT` with no argument always raised `? WAIT error` in `_execute_wait`, in every dialect. Already fixed on `dev` in #38, but `main` (the lean release tree) didn't have it — a `main` checkout running a BASIC V soccerball demo that uses bare `WAIT` for frame pacing still crashed.

## 2026-10-03

- [#34](https://github.com/pyTony/mini_basic/pull/34) Remove test/ from main — tests live on dev — PR #33 (the PRINT `AND`/comparison fix) added `test/__init__.py` and `test/test_print_and_comparison.py` to `main`. `main` is intentionally the lean 1.00 release tree (`mini_basic/`, `basics/`, the HTML handbook, `CHANGELOG.md` only) — `test/`, `tools/`, `examples/`, etc. live only on `dev`.
- [#33](https://github.com/pyTony/mini_basic/pull/33) Fix PRINT a>0 AND b>0 printing 0 for true/true — `PRINT A>0 AND B>0` printed `0` even when both comparisons were true. `X = A>0 AND B>0` / `PRINT X` and `IF A>0 AND B>0 THEN ...` gave the correct `-1`, so this was a PRINT-only bug (as noted in the project's bug report). The struct-member case `PRINT M.W% > 0 AND M.H% > 0` also worked incorrectly before this fix…
- [#32](https://github.com/pyTony/mini_basic/pull/32) Release cleanup: showcase on main, main is HTML-only (README.md excepted) — `main` is a lean, self-contained release tree.
- [#26](https://github.com/pyTony/mini_basic/pull/26) Release 1.00 cleanup: split main (lean) from dev (full tree) — `main` is the lean release tree: the `mini_basic/` package,

## 2026-10-02

- [#30](https://github.com/pyTony/mini_basic/pull/30) Add v1.0 demo reel: launcher script + README showcase — a "demo reel" of 8 confirmed-working programs, picked to span graphics/animation, fractals, raw interpreter performance, extended struct support, and classic recursive algorithms:
- [#31](https://github.com/pyTony/mini_basic/pull/31) Implement TINT statement (brightness blend on text colour) — `TINT target,level` works. `target` 0 = foreground, 1 = background; `level` is 0/64/128/192. It blends that brightness into the *current* text colour (set by the preceding `COLOUR`) without changing its base hue, matching real BBC BASIC semantics, and resets to 0 whenever `COLOUR` or `MODE` picks a new base colour…
- [#29](https://github.com/pyTony/mini_basic/pull/29) Remove stale compatibility blockers from bbcsdl_scan — those stale patterns are removed. The genuine gaps stay, re-weighted: `OSCLI LOAD/FONT/MDISPLAY` (image/font loading) and `ON MOUSE`/`ON MOVE` event hooks are weighted lower than `SYS`/OpenGL/Box2D/inline-asm/raw fn-pointers, since pygame is itself an SDL wrapper and could plausibly support the former later —…
- [#27](https://github.com/pyTony/mini_basic/pull/27) Pull merged-PR info from GitHub into TODO.md — `TODO.md` now has two sections: the open-issues checklist as before, plus a "Recently merged PRs" list (number, title, merge date) for the 10 most recently merged PRs. The `update-todo.yml` workflow regenerates both sections the same way — on every merge to `main`, or via manual `workflow_dispatch`.
- [#28](https://github.com/pyTony/mini_basic/pull/28) Restore INKEY(-n) key table entries dropped by a manual merge — the full key table is back. Added a regression test (`test_key_table_names_punctuation_and_function_keys`) that checks every code `_BBC_INKEY_CHARS` recognizes is also present in `_BBC_NEGATIVE_INKEY_KEYS`, so the two tables can't silently disagree again — the existing `test_key_table_names_common_keys` only…
- [#25](https://github.com/pyTony/mini_basic/pull/25) Add auto-generated TODO.md refreshed on each merge — There is no `TODO.md`. "Open work" only exists as the GitHub issues list (#11-#14), and there's no automated link between merged PRs and that list — nothing updates automatically.
- [#24](https://github.com/pyTony/mini_basic/pull/24) Fix bare-FN-call rewrite hijacking plain fn-prefixed variables — the rewrite only fires when `FN<name>` is an actually-defined user function (or a recognized `gfx*`/`sortinit` builtin stub); any other `FN`-prefixed identifier is left as a normal variable.

## 2026-09-28

- [#23](https://github.com/pyTony/mini_basic/pull/23) Fix INKEY(-n) key-down scan and glued INKEY-99 syntax — the key table now covers the full BBC Micro layout plus BB4W/BBCSDL extras (F-keys, punctuation, CAPSLOCK, END, Shift/Ctrl/Alt left+right variants) and mouse buttons `-10`/`-11`/`-12`. A terminal (non-pygame) fallback treats the pending input character as its key, held for 0.1s so one frame of a game loop can scan…
- [#10](https://github.com/pyTony/mini_basic/pull/10) docs: add CHANGELOG.md for merge history — `CHANGELOG.md` lists each merged PR (#2-#9) with a one-line summary, newest first. `index.html` is kept — it's the front door to the `docs/site/` HTML handbook, linked from README.md/HOWTO.md/docs/INDEX.md, not Grok-only as first thought. Ongoing task tracking moves to GitHub Issues (#11-#14) instead of a…

## 2026-09-26

- [#21](https://github.com/pyTony/mini_basic/pull/21) Fix --trace CLI flag being silently reset by load() — `--trace` traces the loaded program's execution the same way `TRACE ON` does.
- [#22](https://github.com/pyTony/mini_basic/pull/22) Nested structs and whole-struct copy (bounce.bbc runs) — bounce.bbc runs, balls spawn, bounce and get removed at the right edge. It also no longer quits after the first frame.
- [#20](https://github.com/pyTony/mini_basic/pull/20) Fix redundant re-sort in _register_numeric_var (surks.bbc perf) — the list is only re-sorted when a pattern is actually newly added, and already-registered variable names are cached so a repeat `LET` skips rebuilding/recompiling patterns and rescanning the list entirely. Re-profiling `surks.bbc` shows ~32% more statements executed in the same time window.
- [#17](https://github.com/pyTony/mini_basic/pull/17) Add ELLIPSE [FILL] x,y,a,b[,angle] command (surks.bbc) — `ELLIPSE [FILL] x,y,a,b[,angle]` draws an outline or filled ellipse, with an optional rotation angle in radians (BBC BASIC convention). `surks.bbc` now runs past its ellipse-drawing loop.
- [#19](https://github.com/pyTony/mini_basic/pull/19) Fix unrecognized single-line colon-joined DEF PROC bodies — `PROCCLER` (and any other procedure defined entirely on one physical line with a colon-joined body, e.g. `DEF PROCfoo:stmt:stmt:ENDPROC`) is correctly recognized and runs. `pointer.bbc` now gets past its startup init and into its interactive input loop instead of crashing.
- [#16](https://github.com/pyTony/mini_basic/pull/16) docs: SYS and struct support are partial, not out of scope — the docs describe the small named `SYS` table (`runtime_parts/sys_calls.py`: ticks, delay, display mode) and flat `DIM name{a%,b$,c}` struct support that already work, and narrow the "deferred" rows to what's genuinely still missing (a general SYS FFI, nested/array structs, structs as PROC/FN parameters).
- [#15](https://github.com/pyTony/mini_basic/pull/15) Fix PLOT arc seam flicker on rotation (swirl.bbc) — the arc's cut-off ends stay lit across rotation instead of toggling pixel by pixel.
- [#5](https://github.com/pyTony/mini_basic/pull/5) Run swirl.bbc: SYS SDL calls, struct members in mini, ABSSIN, PLOT arcs — swirl runs error-free and draws thick, colour-graded arcs. Any SYS name that isn't in the table still reports "? Out of scope".
- [#6](https://github.com/pyTony/mini_basic/pull/6) BBC DIM p n memory blocks with ?/! reads and stores — `DIM p n` and `DIM p% n` reserve `n+1` bytes on the interpreter's byte-array heap and store the block's address in the (plain or `%`) variable, matching BBC BASIC's non-array `DIM` form. Reads work with `p?1`, `p!4`, `p%?i%`, and in the `bbc` dialect also the unary `?p` / `!p` / `?(p+1)` forms. Writes now work too:…
- [#3](https://github.com/pyTony/mini_basic/pull/3) disco.bbc: byte variables and RECTANGLE outline / SWAP / TO — disco.bbc runs without errors, drawing its gradient grid and swapping tiles.
- [#4](https://github.com/pyTony/mini_basic/pull/4) Stop the program when the pygame window is closed with X — closing the window runs any `ON CLOSE` handler and stops the program, like Escape.
- [#7](https://github.com/pyTony/mini_basic/pull/7) Fill PLOT 112-119 parallelograms instead of drawing a line — the diamonds render as filled shapes matching BBC BASIC's output.
- [#8](https://github.com/pyTony/mini_basic/pull/8) perf: fix Mandelbrot ANSI slowdown (WHILE guard fast path + IF parse cache) — Mandel_ANSI now runs in ~0.47s, with identical output. mand_arch is unchanged (it already used the fast path).
- [#9](https://github.com/pyTony/mini_basic/pull/9) Scope COLOUR 136-143 flash to non-custom palette entries; skip Windows-only test — the interpreter tells the display when a background colour in the 136-143 range was just given a custom RGB, and the display keeps that colour solid instead of flashing; a plain `COLOUR 136` (no custom palette) still flashes as before. The path test now skips on non-Windows platforms instead of failing.
- [#2](https://github.com/pyTony/mini_basic/pull/2) Edge-case fixes: == equality, INKEY(-256) platform id, negative INKEY in bbc — `INKEY(-256)` returns the BBCSDL platform id (`&73`), negative `INKEY` works in bbc, and `==` is treated as `=` in comparisons. `disco.bbc` starts and animates.
