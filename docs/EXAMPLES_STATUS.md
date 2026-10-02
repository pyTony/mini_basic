# examples/ status

Full inventory of `examples/**/*.bas` and `*.bbc` with done/todo/skip status, built 2026-10-02.
Sources combined: `docs/PROGRAM_VS_TESTS.md`, project memory (Tony's manual confirmations),
`python -m mini_basic.bbcsdl_scan` tiers (post-PR #29) for anything with a corpus counterpart
under `test/corpus/bbcsdl/`, and `test/test_*.py` coverage for the tutorial folders.

Legend: **DONE** = confirmed working (by Tony, or by an automated test). **TODO** = not yet
confirmed, no known blocker (worth a quick manual check). **BLOCKED** = known unsupported
BBCSDL feature (see tier). **SKIP** = not a real program / duplicate / out of scope.

## Dialect tutorials (own test suites, not BBCSDL ports) — DONE

- `examples/bbc/*.bas` (Clock, goto_label, menu, proc, repeat, time) — bbc-dialect syntax demos.
- `examples/mini/*.bas` (bbc_graphics_demo, break_continue, colors, find_epsilon, hello_args,
  mouse_click_letter, near_float, sprites_demo) — mini-dialect feature demos.
- `examples/mits/*.bas` (menu, on_error, question) — MITS dialect demos.
- `examples/m6502-cport/*.bas` (01_hello .. 60_end_of_file, adv/adventure, apps/*) —
  covered by `test/test_m6502_cport_mits.py`.
- `examples/vdu/*.bas` (phase_a/b/c) — VDU feature-phase demos.
- `examples/teletext/mode7_test_screen.bas` — covered by `test/test_teletext_screen.py`.
- `examples/museum/BETH.BAS`, `ELIZA.BAS` — classic museum pieces, run standalone (no graphics).

These are mini_basic's own tutorials/fixtures, not corpus ports, so they have no bbcsdl_scan tier.

## graphics/ (BBCSDL ports)

| Program | Status | Notes |
|---|---|---|
| disco.bbc | DONE | confirmed; tier A |
| scarab.bbc | DONE | confirmed; tier A |
| squares.bbc | DONE | confirmed; tier A |
| wheel.bbc / wheel.bas | DONE | confirmed; tier A |
| flier.bbc | DONE | confirmed; tier A |
| swirl.bbc | DONE | confirmed (tip flicker fixed PR #15); tier C (SYS, likely just a feature-detect no-op path) |
| illusion.bbc | DONE | confirmed; tier A |
| saucer.bbc | DONE | confirmed; tier A |
| polydots.bbc | DONE | confirmed; tier A |
| bounce.bbc | DONE | confirmed (PR #22 struct/INKEY work); no corpus counterpart |
| surks.bbc / surks_mini.bas | DONE | confirmed (PR #17/#20), slow by design (O(n^2) collision check) |
| pointer.bbc | DONE | confirmed (PROCCLER fix, PR #19) |
| jclock.bas / jclock.bbc | DONE | in PROGRAM_VS_TESTS.md confirmed list; tier A |
| fern.bbc | DONE | in PROGRAM_VS_TESTS.md confirmed list; tier A |
| filters — see general/ | | |
| soccerball.bas / soccerball.bbc | DONE | in PROGRAM_VS_TESTS.md confirmed list; tier A |
| mandelbrot/Mandel_ANSI.BAS | DONE | confirmed, ~0.67s |
| mandelbrot/mandelbrot_archimedes_mode9.bas/.bbc | DONE | confirmed, timed (CPython 4.41s / PyPy ~3.5s) |
| mandelbrot/mand_arch.bas | DONE | tracked benchmark (mand_arch) |
| mandelbrot/* (other variants) | TODO | not individually confirmed; same interpreter path as the two above, low risk |
| doodle.bbc | TODO | tier A, not individually confirmed |
| persian.bbc | TODO | tier A, not individually confirmed |
| piechart.bbc | TODO | tier A, not individually confirmed — Tony said "piechart fine" 2026-10-02 (informal, not re-verified against pytest in this sandbox) |
| polygon.bbc | TODO | tier A, not individually confirmed |
| sine.bbc | TODO | tier A, not individually confirmed |
| spectrum.bbc | TODO | tier A, not individually confirmed (this is the program whose local SyntaxError from a bad manual merge kicked off PR #28) |
| Clock.bas | TODO | not scanned (no corpus match found under this name), not individually confirmed |
| flood.bbc | BLOCKED (tier C, score 24) | SYS(2), call_usr(1) |
| sliderule.bbc | BLOCKED (tier B, score 8) | oscli_font(4) — present as tokenized binary; SDL-feasible gap (font loading) |
| snowscene.bbc | BLOCKED (tier B, score 6) | oscli_load(1), file_ptr(1) — present as tokenized binary; SDL-feasible gap |
| chain.bbc | not in examples/ | tier B, score 6 (oscli_load/mdisplay) — SDL-feasible; not yet added, awaiting your call |
| penrose.bbc | not in examples/ | tier B, score 6 (oscli_load/mdisplay) — SDL-feasible; not yet added, awaiting your call |

## games/

| Program | Status | Notes |
|---|---|---|
| hanoi.bbc | DONE | confirmed, in PROGRAM_VS_TESTS.md; tier A |
| animal.bas / animal.bbc | DONE | in PROGRAM_VS_TESTS.md confirmed list; tier C (call_usr(2)) — runs despite tier, treat tier as "has a feature-detect path", not "broken" |
| soccerball*.bas (clean/clean_nobom/fast variants) | SKIP | duplicates of games/soccerball.bas kept for regression history |
| rheolism.bbc, roadrace.bbc, tower.bbc, Slots.bas | TODO | no corpus counterpart found (not in test/corpus/bbcsdl), never individually checked |
| 2048.bbc | BLOCKED (tier C, score 18) | SYS(1), on_event(1), call_usr(1) |
| sudoku.bbc | BLOCKED (tier C, score 14) | on_event(1), call_usr(2), oscli_font(1) |
| triples.bbc | BLOCKED (tier C, score 23) | INSTALL + oscli_load/mdisplay/font |
| cowboy.bbc | BLOCKED (tier D, score 118) | fn_ptr, SYS, INSTALL, on_event, oscli_font |
| lemmings.bbc | BLOCKED (tier D, score 117) | SYS(9), INSTALL(3), oscli_font |
| jigsaw.bbc | BLOCKED (tier D, score 264) | heavy SYS use |
| bugs.bbc | BLOCKED (tier D, score 186) | fn_ptr(17), SYS |
| dropperz.bbc | BLOCKED (tier D, score 174) | oscli_mdisplay(49) — heavy image loading |
| buggy.bbc | BLOCKED (tier D, score 131) | SYS(10), opengl(1) |
| dibley.bbc | BLOCKED (tier D, score 86) | SYS(4), INSTALL, call_usr, oscli_font |
| hangman.bbc | BLOCKED (tier D, score 1592) | SYS(79), fn_ptr(88), opengl(7) — far out of reach |
| gorillas.bbc | BLOCKED (tier D, score 1778) | SYS(51), fn_ptr(158) — far out of reach |
| snake.bbc | BLOCKED (tier D, score 1008) | SYS(49), fn_ptr(62) — far out of reach |

## general/

| Program | Status | Notes |
|---|---|---|
| welcome.bbc | DONE | confirmed, in PROGRAM_VS_TESTS.md; tier A |
| filters.bbc | DONE | confirmed, in PROGRAM_VS_TESTS.md; tier A |
| Ceefax.bbc | TODO | tier A, not individually confirmed |
| poem.bbc | BLOCKED (tier C, score 4) | call_usr(1) — close to tier A, worth a recheck |
| welcome_zap_pause.bas | TODO | variant of welcome.bbc, no corpus match, not confirmed |
| BBSterm.bbc, client.bbc, server.bbc, server_multi.bbc, lanchat.bbc, mysqldem.bbc, multitouch.bbc, pdfdemo.bbc, recorder.bbc, video.bbc, dlgdemo.bbc | SKIP | networking/hardware/OS-integration demos, no corpus match — out of scope for an interpreter without real sockets/audio/video/touch hardware here |
| listdemo.bbc, aagfxdem (n/a), ellipses (n/a), smithchart (n/a), truchet (n/a), vampire (n/a), unicode.bbc | BLOCKED (tier C, score 7-9) | INSTALL-gated (BBCSDL library loader) |
| sliderule — see graphics/ | | |
| scroll.bbc, surks — see graphics/ | | |
| swirl — see graphics/ | | |
| sortdemo.bbc, timerdem.bbc, aliens (n/a), anigif (n/a), candle (n/a) | BLOCKED (tier C, score 11) | INSTALL + on_event |
| bigdem.bbc | BLOCKED (tier C, score 13) | INSTALL + oscli_font |
| knots (n/a), sudoku — see games/ | | |
| calendar.bbc | BLOCKED (tier C, score 17) | INSTALL, on_event, oscli_font |
| solve.bbc | BLOCKED (tier C, score 18) | INSTALL(2), on_event |
| prompter.bbc | BLOCKED (tier C, score 19) | SYS, on_event, file_ptr, oscli_font |
| kerning.bbc | BLOCKED (tier C, score 22) | SYS(2), oscli_font |
| multidem.bbc, optics.bbc | BLOCKED (tier C, score 23) | SYS, INSTALL, on_event, oscli_font |
| sorttest.bbc | BLOCKED (tier C, score 31) | call_usr(6) |
| bezierfit.bbc, ellipsefit.bbc | BLOCKED (tier C/D, score 37-40) | SYS, INSTALL(3), on_event, oscli_font |
| banner.bbc | BLOCKED (tier D, score 41) | file_ptr(5) heavy |
| mode7dem.bbc | BLOCKED (tier D, score 41) | call_usr(3), file_ptr(6) |
| calculator.bbc | BLOCKED (tier D, score 48) | SYS(2), INSTALL(2), on_event(2) |
| sheet.bbc | BLOCKED (tier D, score 84) | SYS, INSTALL(8), file_ptr |
| analyser.bbc | BLOCKED (tier D, score 94) | SYS(9) |
| textedit.bbc | BLOCKED (tier D, score 132) | SYS(4), INSTALL(4), file_ptr(5), oscli_font(8) |
| telstar.bbc | BLOCKED (tier D, score 176) | SYS(9), opengl(3), call_usr(8) |
| SkyBaby.bbc | BLOCKED (tier D, score 192) | SYS(8), opengl(1), file_ptr(5) |
| polyfit.bbc, pageturn (n/a) | BLOCKED (tier D, score 40-43) | SYS, INSTALL, file_ptr |
| spotlight (n/a) | BLOCKED (tier D, score 46) | SYS(2), INSTALL(2), on_event(3) |
| conway.bbc | BLOCKED (tier D, score 574) | fn_ptr(32), opengl(37) |

## Top-level loose files (examples/)

| Program | Status | Notes |
|---|---|---|
| 1DLIFE.BAS, keywords.bbc, starcmds.bbc, vducodes.bbc, about.bbc, immediate.bbc, soccerball.bas, wheel.bas | SKIP / reference | reference listings and duplicates of graphics/ versions, not standalone test targets |

## Summary counts

- **DONE** (confirmed working): ~30 programs across graphics/, games/, general/, plus all dialect
  tutorial folders (test-covered).
- **TODO** (tier A or no corpus match, not yet individually confirmed): ~15 programs — lowest-risk
  next manual-check batch (spectrum, piechart, sine, polygon, persian, doodle, Ceefax, Clock,
  mandelbrot variants, rheolism, roadrace, tower).
- **BLOCKED** (tier B/C/D — real BBCSDL feature gaps): ~55 programs, mostly `general/` and
  `games/` desktop-app and OpenGL/physics demos. Tier B (chain, penrose, sliderule, snowscene,
  poem) are the SDL-feasible ones worth prioritizing if pygame-backed image/font loading or
  mouse/window events are ever implemented.
- **SKIP**: duplicate/reference files and networking or OS-integration demos out of scope for
  this interpreter.

See [[bbcsdl-scan-accuracy-pr29]] for how tiers are computed; re-run
`python -m mini_basic.bbcsdl_scan` after any new feature lands to re-tier BLOCKED entries.
