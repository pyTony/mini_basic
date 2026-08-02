# mini_basic 1.00 — Language features & ship qualification

**Status:** Ready to ship as **1.00** under the scope locked below  
**Version line:** `mini_basic 1.00-dev` → tag **1.00** when this document is accepted  
**Date:** 2026-08-03  
**Related:** [`PLAN_1.00_AND_VDU.md`](PLAN_1.00_AND_VDU.md) · [`FEATURES_DONE.txt`](../FEATURES_DONE.txt) · [`CORPUS_AUDIT.txt`](../CORPUS_AUDIT.txt) · [`USER_APPROVAL.txt`](../USER_APPROVAL.txt)

This is the **language and graphics baseline** for 1.00. It states what is in, what is out, and **why the product qualifies** without claiming full BBCSDL / RISC OS parity.

---

## 1. Why 1.00 is justified

1.00 is not “every BBC BASIC feature ever.” It is a **complete, honest interpreter release** that:

| Criterion | Evidence |
|-----------|----------|
| **Multi-dialect core language works** | Dialects `mini`, `mits`, `commodore`, `tiny`, `bbc` — control flow, expressions, files, I/O (see §2–3). |
| **BBC graphics tier A is usable** | MODE, GCOL, MOVE/DRAW/PLOT, CIRCLE, COLOUR, ORIGIN, *REFRESH, VDU phases A–C (see §4). |
| **BBCSDL corpus is green or explicitly deferred** | `CORPUS_AUDIT`: **22 OK**, **2 DEFER** (polly sound, poem interactive MODE7) — not silent failures. |
| **Major demos match user expectation** | User-approved: welcome, squares, saucer, flier, soccerball, wheel, jclock, filters, hanoi, animal, … |
| **Ship hygiene** | `--version` / `-V`, Russell `.bbc` detokenize, text-only sessions skip auto-pygame, phase0+phase1 regression suite. |
| **Non-goals are written down** | Sound synthesis, WIMP, SYS FFI, Box2D, full SAA5050 — see §6 and `features/deferred.py`. |

**Qualification rule:** If a feature is required for a **user-approved** or **audit OK** program, it is either implemented or the program is documented DEFER. There is no “mystery FAIL.”

**What 1.00 is not:** a compiler, a RISC OS desktop, full SOUND/ENVELOPE hardware, or pixel-perfect SAA5050 teletext.

---

## 2. Dialects

| Dialect | Role | Language posture |
|---------|------|------------------|
| **mini** | Default / superset | Unnumbered + numbered; modern BBC control flow; mini extensions (BREAK/CONTINUE, ANSI helpers). |
| **bbc** | BBCSDL / BB4W-oriented | PROC/FN, CASE, WHILE, REPEAT, MODE/VDU/graphics; glued keywords; tokenized `.bbc` load. |
| **mits** | Classic Dartmouth-style | Numbered lines, GOTO/GOSUB, ON ERROR, strict classic control. |
| **commodore** | C64-flavoured | Numbered lines, classic flow, dialect keyword set. |
| **tiny** | Minimal 1975-style | Smallest statement set for teaching / tiny programs. |

Dialect selection: CLI / config / `MINI_BASIC_DIALECT` · `MINIBASIC_DIALECT`.

---

## 3. Core language (all ship dialects, with dialect gates)

### 3.1 Program structure

- Numbered and/or unnumbered lines (dialect-dependent).
- Colon multi-statement lines; `REM` / `'` comments.
- `LOAD` / `SAVE` / `CHAIN` / `RUN` / `LIST` / `NEW` / `END` / `STOP`.
- Tokenized BBCSDL/Beeb **`.bbc` detokenize** on load (Russell formats).

### 3.2 Control flow

| Feature | Notes |
|---------|--------|
| `GOTO` / `GOSUB` / `RETURN` | Classic. |
| `IF` … `THEN` / bare `IF` colon body | BBC bare `IF cond: stmt` supported. |
| `IF` / `ELSE` / `ELSEIF` / `ENDIF` | Structured. |
| `ON` … `GOTO` / `GOSUB` | |
| `ON ERROR` / `RESUME` | ERR/ERL available in handlers. |
| `FOR` / `NEXT` (int and float) | Nested; pure-delay and nested-int fast paths where safe. |
| `WHILE` / `WEND` (or `ENDWHILE`) | |
| `REPEAT` / `UNTIL` | |
| `EXIT FOR` / `WHILE` / `REPEAT` | |
| `CASE` / `WHEN` / `OTHERWISE` / `ENDCASE` | BBC family. |
| `DEF PROC` / `ENDPROC`, `DEF FN` / `END DEF` | Glued `PROCname` / `FNname` (BBC rule). |
| `BREAK` / `CONTINUE` | **mini** extension. |

### 3.3 Variables & expressions

| Feature | Notes |
|---------|--------|
| Float, integer `%`, string `$` | Optional bigint for `%` where enabled. |
| Arrays `DIM` | Numeric/string; some PRINT-subscript expansion still a known gap. |
| Operators | `+ - * /`, `DIV`, `MOD`, `^`, shifts `<<` `>>`. |
| Bitwise | `AND` `OR` `EOR`/`XOR` `NOT` (integer bitwise path; pure bitwise can compile). |
| Relations / logic | `=` `<>` `<` `>` … ; BBC TRUE = **-1**. |
| Hex / binary forms | BBC-style literals where implemented. |
| Built-ins | `SIN` `COS` `TAN` `ASN` `ACS` `ATN` `SQR` `ABS` `INT` `SGN` `RND` `LOG` `EXP` `RAD` `DEG` … |
| Strings | `LEFT$` `RIGHT$` `MID$` `STR$` `VAL` `ASC` `CHR$` `LEN` `INSTR` `STRING$` … |
| Time | `TIME`, `TIME$` (where provided). |
| System stubs | `@%`, `@vdu%!n`, `@lib$` / `@dir$` partial, `@ispal%` stub, etc. |

### 3.4 I/O

| Feature | Notes |
|---------|--------|
| `PRINT` / `?` | TAB, SPC, commas/semicolons; VDU embedded sequences. |
| `INPUT` / `LINE INPUT` | |
| `GET` / `GET$` / `INKEY` / `INKEY$` | Positive timeout present for graphics; glued `INKEY1`. |
| Files | `OPENIN` / `OPENOUT` / `OPENUP`, `PRINT#` / `INPUT#` / `BGET#` / `BPUT#`, `EOF#`, `CLOSE#`. |
| `OSCLI` / `*` commands | Subset (e.g. display/path helpers); not full RISC OS SYS. |
| `MOUSE` | Desktop backends. |
| `ON CLOSE` | Window close trap (pygame). |

### 3.5 Data

- `DATA` / `READ` / `RESTORE` (classic and multi-statement forms as tested).

---

## 4. BBC graphics language (bbc / mini graphics path)

### 4.1 Statements

| Statement | 1.00 status |
|-----------|-------------|
| `MODE` n | Modes 0–7 + BB4W/SDL extended (e.g. 8+); MODE 7 teletext **partial**. |
| `GCOL` action, colour | Modes 0–7 including XOR/invert. |
| `COLOUR` / `COLOR` | Text fg/bg; multi-arg RGB palette; `COLOR n+128` bg index kept (piechart sky). |
| `MOVE` / `DRAW` / `PLOT` | PLOT codes subset + BB4W extras; absolute/relative. |
| `CIRCLE` / `CIRCLE FILL` | Outline and disc; disc clip vs false pie bulge fixed. |
| `RECTANGLE` / `RECTANGLE FILL` | |
| `CLG` / `CLS` | CLG respects graphics viewport where set. |
| `ORIGIN` / `VDU 29` | Bottom-left OS origin model. |
| `OFF` / cursor | VDU 23,1 |
| `*REFRESH` / present | Rate-limited present; dirty-rect path. |
| `WAIT` | |
| VDU 5 text at graphics cursor | Top-left cell; palette colour 7 = white. |

### 4.2 VDU (1.00 phases A–C)

| Codes | Role |
|-------|------|
| **4 / 5** | Text vs graphics print |
| **7** | Bell (soft) |
| **8–11, 13** | Cursor motion / CR |
| **12 / 16** | CLS / CLG |
| **17** | Text colour (= COLOUR) |
| **18** | GCOL |
| **20** | Reset colours |
| **24** | Graphics viewport (store; soft clip) |
| **25** | PLOT |
| **26** | Reset viewports |
| **28** | Text viewport (store + cursor clamp) |
| **29** | ORIGIN |
| **30 / 31** | Cursor home / TAB(x,y) |
| **23,1** | Cursor visible |
| **23,22** | User mode: width;height;charx,chary,ncols,charset |
| **23,n redefine char** | 8×8 user glyphs (welcome solid block) |
| **23,*** other | Consume operands, **no error** (Phase C) |

### 4.3 Performance note (language-visible)

- Nested **integer** `FOR` bodies of simple plot/colour form can use a native fast path (e.g. **squares.bbc** munching pattern).
- Float geometry loops (**saucer.bbc**) remain interpreter-paced; shape is user-approved; speed is not a 1.00 blocker.

---

## 5. Validation evidence (why not “0.9”)

### 5.1 Automated / audit

| Gate | Result |
|------|--------|
| Corpus `ALL` runnable | **22 OK** |
| Explicit DEFER only | **polly** (sound/OSCLI DISPLAY), **poem** (interactive MODE7) |
| Phase 0 / 1 pytest | Large green regression (phase0 + phase1 markers; see FEATURES_DONE) |
| Focused graphics tests | piechart sectors/labels, welcome chars/envelope, VDU A–C, squares speed, soccerball, etc. |

### 5.2 User visual approval (graphics language exercised)

Approved programs (non-exhaustive): **welcome**, **squares**, **saucer**, **flier**, **soccerball**, **wheel**, **jclock**, **filters**, **hanoi**, **animal**.

These exercise MODE/VDU, PLOT/GCOL, CIRCLE, COLOUR RGB, MOUSE/TIME, text-on-graphics, nested FORs, PROC/FN, ON ERROR, and real BBCSDL `.bbc` loads.

### 5.3 Plan checklist (from PLAN_1.00)

| Item | 1.00 |
|------|------|
| VDU A–C | Done |
| Corpus FAIL empty **or** explicit DEFER | Done |
| Version report | Done (`--version`) |
| Language + graphics baseline written | **This document** |
| Full sound / WIMP / SYS | Out of scope |

---

## 6. Explicit non-goals (do not block 1.00)

From `mini_basic/features/deferred.py` and project policy:

| Area | Examples |
|------|----------|
| Sound | Full `SOUND` / `ENVELOPE` / multi-channel audio (**polly** deferred) |
| Desktop | RISC OS WIMP, MENU, WINDOW, rich `ON MOUSE` UI |
| OS FFI | `SYS` Windows API, `INSTALL` token libraries |
| Low-level | Inline assembler, `CALL`/`USR` machine code |
| Structures | Full `DIM struct{}` / TYPE as in BB4W |
| Teletext remainder | Double-height, conceal, boxed, full SAA5050 |
| Physics / net | Box2D bindings, Ceefax HTTP fetch |
| Compiler | Crunch / compile-to-native |

**Also not blocking:** PRINT of bare array subscripts `PRINT a(i)` without expansion (known gap; use `;` or separate expressions); saucer draw time; piechart optional visual re-confirm if desired (audit already OK).

---

## 7. Environment & CLI (ship surface)

| Item | Purpose |
|------|---------|
| `python -m mini_basic …` | Run programs |
| `--dialect` | mini / mits / commodore / tiny / bbc |
| `--display` | pygame / terminal / none |
| `--version` / `-V` | Version + implementation snapshot + `MINIBASIC_DIR` |
| `--slow [ms]` | Per-line pause + present (debug) |
| `MINIBASIC_DIR` | Install / launcher tree |
| `MINIBASIC_NO_GRAPHICS` / `MINIBASIC_DISPLAY` | Headless / backend control |
| `SDL_VIDEODRIVER=dummy` | CI / agents |

---

## 8. Ship decision statement

**mini_basic qualifies for 1.00** because:

1. The **language product** is multi-dialect, structured-BASIC complete for teaching and classic programs, and BBC-family complete for control flow + files + expressions needed by the corpus.  
2. The **BBC graphics language** (MODE/VDU/PLOT/GCOL/COLOUR/CIRCLE/ORIGIN) is implemented through the VDU A–C plan and validated by user-approved demos.  
3. **Quality gates** are closed: corpus audit OK-or-DEFER, regression phases green, version/reportability in place.  
4. **Scope is honest:** deferred rows are listed; 1.00 does not pretend to be BBCSDL-with-sound or RISC OS.

**To tag 1.00:** accept this document, set `__version__ = '1.00'`, add a one-page `RELEASE_1.00.md` changelog pointer to this file if desired, and keep polly/poem on the post-1.00 backlog.

---

## 9. Post-1.00 backlog (ordered lightly)

1. polly — SOUND/ENVELOPE + OSCLI DISPLAY/FONT  
2. poem — interactive MODE7 audit path  
3. Saucer float-loop performance (optional)  
4. PRINT array subscript expansion  
5. Teletext remainder / structures / SYS as demand appears  

---

*End of 1.00 language features baseline.*
