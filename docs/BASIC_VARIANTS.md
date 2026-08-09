# BASIC variants and mini_basic

This document maps historical and modern BASIC dialects to **mini_basic**, and
shows how that mapping is recorded in the project **feature grids**.

| | |
|--|--|
| **Canonical grids (generated)** | [`documentation/feature_matrices/`](../documentation/feature_matrices/) |
| **Combined dump** | [`ALL_MATRICES.txt`](../documentation/feature_matrices/ALL_MATRICES.txt) |
| **Python source of truth** | [`mini_basic/features/`](../mini_basic/features/) |
| **Ship language baseline** | [`LANGUAGE_FEATURES_1.00.md`](LANGUAGE_FEATURES_1.00.md) |
| **REPL** | `MATRIX` / `HELP DIALECTS` (structure grid) · `HELP PROGRAM` (LOAD/SAVE) |

Regenerate text matrices from the package:

```bash
python -m mini_basic.features
# or: python -m mini_basic.feature_matrices
```

Legend used in grids: **`+`** supported · **`-`** absent / rejected in strict mode · **`~`** partial or different semantics.

---

## 1. Two axes of comparison

mini_basic needs **two** grids, not one:

| Axis | Columns | File | Question it answers |
|------|---------|------|---------------------|
| **A. Interpreter dialects** | `mits` · `commodore` · `tiny` · `bbc` · `mini` | [`01_dialect_structure.txt`](../documentation/feature_matrices/01_dialect_structure.txt) | What does *this* dialect mode allow or reject? |
| **B. BBC family products** | Beeb · ROS · BB4W · SDL · mini(bbc) | [`01b_bbc_family.txt`](../documentation/feature_matrices/01b_bbc_family.txt) | How does mini’s **bbc** mode relate to real BBC BASICs? |

Topic grids (trig, graphics, arrays, DATA, implementation status, deferred) sit under the same folder and measure **bb** / mini capability depth against BB4W/SDL-style specs—not MITS vs C64.

```text
                    historical BASIC family
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    Dartmouth/MITS        8-bit home           Acorn BBC line
    (numbered, GOTO)     (C64 MS BASIC)      Beeb → ROS V/VI
         │                    │              → BB4W → BBCSDL
         ▼                    ▼                    ▼
      dialect mits       dialect commodore     dialect bbc
         │                    │                    │
         └────────────────────┴──────────┬─────────┘
                                         │
                              dialect mini (superset default)
```

---

## 2. mini_basic dialects (axis A)

Selected with `--dialect …`, env `MINI_BASIC_DIALECT` / `MINIBASIC_DIALECT`,
file hint (`#!bbc` or `1 REM dialect: bbc`), or REPL `DIALECT`.

| Dialect | Intent | Typical programs | Line form (strict) |
|---------|--------|------------------|--------------------|
| **mini** | Default superset | Modern + museum mixed | Numbered **and** unnumbered |
| **bbc** | BBCSDL / BB4W oriented | `examples/`, corpus `.bbc` | Unnumbered preferred; numbered OK |
| **mits** | Dartmouth / early micro style | ELIZA, classic numbered | Numbered only |
| **commodore** | C64 / MS BASIC V2 flavour | Numbered IF/GOTO style | Numbered only |
| **tiny** | Minimal 1975 Tiny BASIC | Teaching / tiny listings | Numbered only |

### Structure grid (excerpt)

Source of truth: `dialect_structure_rows()` → `01_dialect_structure.txt` · REPL **`MATRIX`**.

| Feature | mits | com | tiny | bbc | mini |
|---------|:----:|:---:|:----:|:---:|:----:|
| Numbered lines | + | + | + | −* | + |
| Unnumbered lines | − | − | − | + | + |
| GOTO / GOSUB / RETURN | + | + | + | + | + |
| IF … GOTO *nn* | + | + | − | − | + |
| IF … THEN *nn* | + | + | − | + | + |
| IF/ENDIF / ELSEIF | − | − | − | + | + |
| WHILE / WEND | − | − | − | + | + |
| REPEAT / UNTIL | − | − | − | + | + |
| PROC / DEF PROC | − | − | − | + | + |
| BREAK / CONTINUE | − | − | − | − | + |
| ARG / CLI args | − | − | − | − | + |
| FG$ / BG$ ANSI | − | − | − | − | + |

\*In the structure matrix, **bbc** marks “numbered lines” as rejected in the **strict unnumbered** sense used for that column’s classic BETH-style posture; in practice mini’s **bbc** mode still **loads and runs** numbered files (GOTO targets, renumber, etc.). Prefer the matrix + `HELP DIALECTS` for the strict gate list.

**Relation summary**

- **mits / commodore / tiny** ≈ classic **line-number + GOTO** teaching/museum dialects.  
- **bbc** ≈ structured BBC family language (PROC, CASE, WHILE, …) without mini-only extras.  
- **mini** = **bbc-like core + numbered programs + mini extensions** (BREAK/CONTINUE, ARG, ANSI helpers).
  **Keywords** accept any case (`for`/`FOR`); **variable names** stay case-sensitive by default.

---

## 3. BBC product family (axis B)

These are **external systems**; mini’s column is **`bbc` dialect mode**, not a claim of full product parity.

| Product | Era / platform | Relation to mini_basic |
|---------|----------------|------------------------|
| **Beeb** (BBC Micro / Master, MOS BASIC II/IV) | 1980s 6502 | Tokenized **Wilson** load; smaller language (no CASE/WHILE as on ROS); MODE 0–7 + teletext 7 |
| **ROS** (RISC OS BASIC **V / VI**) | Archimedes / RPi | Structured BBC; in-memory programs still **line-numbered**; Edit/TEXTLOAD assign numbers to text; SYS/WIMP largely **deferred** in mini |
| **BB4W** (BBC BASIC for Windows) | Desktop (Russell) | Language + MODE 8+ / CIRCLE-style graphics target for many matrices |
| **SDL** (BBC BASIC for SDL 2.0) | Cross-platform (Russell) | Primary **corpus** target (`test/corpus`, many `examples/*.bbc`); tokenized **Russell** load |
| **mini (bbc)** | This interpreter | Detokenize Beeb/SDL files → text → run; graphics tier A; sound/SYS/WIMP not full |

### Family grid (excerpt)

Source: `bbc_family_rows()` → `01b_bbc_family.txt`.

| Feature | Beeb | ROS | BB4W | SDL | mini | Notes |
|---------|:----:|:---:|:----:|:---:|:----:|-------|
| PROC/FN glued to name | + | + | + | + | + | `PROCfoo` not `PROC foo` |
| CASE / WHEN | − | + | + | + | + | Not classic Beeb MOS |
| WHILE / ENDWHILE | − | + | + | + | + | Beeb: REPEAT mainly |
| MODE 0–7 | + | ~ | + | + | + | ROS MODE 7 ≠ Beeb teletext |
| MODE 8+ PC/SDL | − | − | + | + | + | mini default gfx ~ MODE 8 |
| CIRCLE / ELLIPSE keywords | − | ~ | + | + | + | Beeb: PLOT codes |
| Tokenized program files | + | + | + | + | + | Formats differ; mini **detokenizes** only |
| Line numbers required | + | − | − | − | ~ | Beeb classic; ROS/BB4W text unnumbered OK |
| SOUND / ENVELOPE | + | ~ | + | + | ~ | mini: stubs (silent / wait) |
| SYS / rich OS | ~ | + | + | + | ~ | mini: OSCLI subset, not full FFI |
| INSTALL libraries | − | ~ | + | + | ~ | Deferred depth |

Full table and notes: always prefer the generated file over this excerpt.

### Program form (same spirit as BASIC V/VI)

| Form | On disk | In mini_basic after LOAD |
|------|---------|---------------------------|
| Numbered text | `10 PRINT` | Stored as line 10… |
| Unnumbered / PRETTY text | structured indent | **Auto-numbered** (10, 20, 30…) |
| Tokenized `.bbc` | Wilson or Russell binary | Detokenize → then same as text |
| After LOAD | — | Always a **numbered** program map |

Unnumbered is a **file / editor** convenience (like RISC OS Edit / TEXTLOAD renumbering), not a second in-memory program model.

**Round-trip:** `LOAD` unnumbered → edit with `EDIT n` → bare `SAVE` defaults to **PRETTY** (keeps the file unnumbered).  
`SAVE NUMBERED` forces classic line numbers. Numbered loads still bare-`SAVE` as numbered.  
Details: `HELP PROGRAM`.

---

## 4. Other BASIC names (outside the grids)

| Name | Relation |
|------|----------|
| **Dartmouth BASIC** | Ancestor of numbered interactive BASIC; closest dialect: **mits** |
| **Microsoft 6502 / GW-BASIC / QBasic** | Not a first-class dialect; **commodore** only approximates MS-BASIC V2 *flavour* |
| **Tiny BASIC (1975)** | Closest dialect: **tiny** (minimal statement set) |
| **BBCSDL physics / Box2D** | Corpus tier; bindings listed under **deferred** |
| **Compilers / Crunch** | Out of scope (interpreter only) |

Tokenization support is **BBC-family only** (Wilson + Russell). No MITS/Commodore/GW binary tokens.

---

## 5. Topic grids (how deep bbc/mini go)

These compare **BB4W/SDL-style specs** to mini implementation status. Paths under `documentation/feature_matrices/`:

| File | Topic |
|------|--------|
| [`02_trigonometry.txt`](../documentation/feature_matrices/02_trigonometry.txt) | Degrees vs radians, DEG/RAD, SINRAD… |
| [`03_graphics.txt`](../documentation/feature_matrices/03_graphics.txt) | CIRCLE, RECTANGLE, GCOL, MODE scaling… |
| [`04_arrays_matrix.txt`](../documentation/feature_matrices/04_arrays_matrix.txt) | Array fill, multiply, SUM, slices… |
| [`05_data_read.txt`](../documentation/feature_matrices/05_data_read.txt) | DATA / READ / RESTORE |
| [`06_implementation_status.txt`](../documentation/feature_matrices/06_implementation_status.txt) | User-verify implementation checklist |
| [`07_deferred.txt`](../documentation/feature_matrices/07_deferred.txt) | WIMP, ASM, SYS FFI, real sound, INSTALL, structs… |

Deferred rows are intentional non-goals until core language + corpus stay stable—not silent gaps.

---

## 6. Practical mapping for users

| You have… | Do this in mini_basic |
|-----------|------------------------|
| BBCSDL / BB4W listing or tokenized `.bbc` | `--dialect bbc` (or file hint); `LOAD` (auto `.bas`/`.bbc`) |
| Classic numbered museum (ELIZA-style) | `--dialect mits` or **mini** |
| C64-style numbered IF GOTO | `--dialect commodore` |
| Want every extension | `--dialect mini` (default) |
| Unnumbered structured source from editor | `LOAD` → auto numbers; `SAVE PRETTY` to write unnumbered back |
| Paste into RISC OS BASIC | `LIST` with `--dialect bbc` so **PROC names stay glued** |
| Feature question | `MATRIX` + open the matching `0x_*.txt` grid |

---

## 7. Tokenize once vs unglue at eval

Real BBC BASIC **tokenizes at line entry**; mini_basic stores **text** and often
**re-derives** keyword boundaries at run/LIST time. Glue rules (GOTO100, SINa,
case-sensitive `tana` vs `SINa`) and a possible **entry-time canonicalize**
roadmap are written up in [`BBC_TOKENIZE_VS_UNGLUE.md`](BBC_TOKENIZE_VS_UNGLUE.md).

---

## 8. Maintaining the grids

1. Edit rows in `mini_basic/features/*.py` (e.g. `dialect_structure.py`, `bbc_family.py`).  
2. Run `python -m mini_basic.features` to refresh `documentation/feature_matrices/`.  
3. Keep this overview in sync only when **dialect roles** or **axis definitions** change—not for every `+`/`-` flip (those belong in the generated files).

Ship-facing language promises: [`LANGUAGE_FEATURES_1.00.md`](LANGUAGE_FEATURES_1.00.md).  
User-facing matrix notes: [`documentation/FEATURE_TESTS_FOR_USER.txt`](../documentation/FEATURE_TESTS_FOR_USER.txt).
