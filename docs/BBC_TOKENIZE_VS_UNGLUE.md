# BBC BASIC tokenization vs mini_basic unglue

**Status:** Phase 1 **implemented** (entry canonicalize + dual runtime unglue)  
**Date:** 2026-08-09 (updated)  
**Related:** case-sensitive trig unglue (P0), dual LIST/SAVE formatters, `BASIC_VARIANTS.md`

This records a discussion of how **real BBC BASIC** treats glued forms, and whether mini_basic should **normalize once at entry** instead of **re-ungluing on every eval**.

---

## 1. What real BBC BASIC allows (editor tokenize model)

Classic Acorn / RISC OS BBC BASIC **tokenizes as you enter a line** (and when loading tokenized programs). Keywords become single-byte tokens with **longest-match** alphabetic recognition. Digits and many punctuation characters **end** a keyword match cleanly.

### Numbers glued to keywords — idiomatic and expected

Examples you see constantly in listings:

| Form | Notes |
|------|--------|
| `GOTO100` | keyword then number |
| `10MOD3` | number / keyword / number |
| `FOR I%=1TO10STEP2` | glued `TO` / `STEP` after digits |
| `WAIT0` / `INKEY1` | common compact style |

At **tokenize-time** there is little ambiguity: a digit cannot continue a keyword token, so the editor emits keyword token + numeric literal.

### Parentheses

| Form | Usual rule |
|------|------------|
| `PROCfoo` | no args → parens **optional** / often omitted |
| `PROCfoo(a,b)` | args → parens required |
| `FNfoo()` | FN typically **keeps** parens even with no args |
| `GOTO` / `GOSUB` / `THEN` / `PRINT` | not function-call parens |

mini_basic already models much of this (glued PROC/FN names, bare INKEY digits, SINa, etc.) via **text rewrites**, not a true token store.

### Letter vs digit boundary (shared gotcha)

Real tokenizers avoid splitting `TOTAL` at `TO` by requiring that a keyword match is **not** immediately followed by another **letter**. The boundary is often “not letter,” not “not alphanumeric,” so constructs like digit-then-keyword-like substrings can still be sharp edges. Treat exact A0OR0 behaviour as **implementation-dependent**; the category of bug is real for any system that re-derives keywords from plain text.

---

## 2. What mini_basic does today

| Stage | Behaviour |
|-------|-----------|
| **Storage** | Mostly **raw source text** per line number (`self.program[n]`) |
| **LOAD** | Detokenize BBC binary → text, or read UTF-8; may strip dialect hint; unnumbered → auto line numbers |
| **RUN / PRINT / expr** | Repeated **regex unglue / normalize** (`_unglue_trig_idents`, `_expand_numeric_builtin_calls`, FOR TO/STEP spacing, save_case LIST, …) |
| **LIST / SAVE** | May reformat again (pretty/refs/standard); dual paths: `runtime_parts/io.py` vs `format/save_case.py` |

So: **token stream is reconstructed at eval time**, not fixed once at entry. That is why:

- Boundary bugs appear as “path A fixed, path B still broken” (e.g. trig unglue in two places).
- Case mode must be applied **consistently** (mini/bbc: uppercase keywords only for SINa glue; fold: case-insensitive).
- Performance pays normalize cost **per evaluation**, not once per line.

### Case sensitivity (current mini_basic policy)

| Mode | SINa / SINRADT | tana / sina |
|------|----------------|-------------|
| **Case-sensitive** (mini/bbc default) | Glue (keyword form) | **Identifier** |
| **Fold** (mits-style / case off) | Glue case-insensitively | Glue case-insensitively |

That matches “keywords upper-only when case-sensitive,” not “always treat any SIN prefix as function.”

---

## 3. Should unglue happen at LOAD / line entry?

### Advisable as an architecture direction — **yes**

Real BBC BASIC never re-decides keyword boundaries at runtime. Normalizing **once** when text becomes program would:

1. **Centralize** letter/digit/case boundary rules (one fixer, not N formatters).
2. Make **LIST/SAVE/RUN** consumers of the same stored text (LIST ≈ print store; SAVE PRETTY may still re-indent).
3. Cut repeated regex on hot paths (Mandelbrot / eval_expr pressure).
4. Align fidelity with “BBC-like entry,” even while staying a **text-store** interpreter (not necessarily a full Wilson/Russell token VM).

### What it does **not** auto-fix

- Digit-boundary and keyword-vs-name rules still need a **correct** single implementation.
- **Two entry points** must share it: **LOAD** (files) and **REPL/EDIT** (`set_program_line`). Missing one reintroduces path A/B drift.
- Dialect-hint lines, REM/strings, and detokenized binary output need careful “do not mangle comments” rules.
- Unnumbered LOAD → auto-number is separate from unglue; both are “entry transforms.”

### Scope / blast radius

Do **not** treat this as a drive-by patch. Every raw `self.program[n]` reader must either:

- trust pre-normalized text, or  
- document that it still does display-only rewrite (e.g. PRETTY indent).

**Near-term step (already on the queue):** unify dual LIST/SAVE formatters so spacing/keyword glue lives in **one** module. That is a prerequisite or pilot for “normalize once at entry.”

**Later step (deliberate design item):** entry-time canonicalize (LOAD + `set_program_line`), then shrink runtime unglue to a thin safety net or remove it.

Suggested rollout:

1. Inventory call sites that read raw program text.  
2. Single `canonicalize_line(text, *, case_sensitive, dialect)` API.  
3. Wire REPL entry + LOAD behind phase1 suite.  
4. Only then strip duplicate eval-time unglue.

---

## 4. Relation to detokenize

Tokenized `.bbc` load already converts binary → text **once**. That path is closer to “entry normalize” than RUN-time unglue. Expanding that philosophy to **all** text loads (and REPL) is consistent; it is **not** the same as running a token VM.

---

## 5. Decision for mini_basic (2026-08-09)

| Item | Decision |
|------|----------|
| Full load-time unglue store | **Phase 1 done** — `canonicalize_program_line` on `set_program_line` (LOAD + REPL/EDIT) |
| Unify LIST/SAVE formatters | **Done** (`format/save_case.py`) |
| Case-sensitive trig glue | **Done** (P0) — model upper keywords vs lower idents |
| True tokenized in-memory RUN | **Out of scope** (detokenize on load only) |
| Strip runtime unglue | **Phase 2 started** — monadic family uses fast-reject on eval |

### Phase 1 contract (2026-08-09)

| | |
|--|--|
| **API** | `BASICInterpreter.canonicalize_program_line(statement)` |
| **Wired at** | `set_program_line` → all LOAD paths that use it, REPL AUTO/EDIT numbered entry |
| **Does** | Sanitize C0; glue `$`/`!`/`#` suffixes; BBC dialect line glue (`PRINTTAB`, `DEFPROC`, `1TO10`, `MODE5`, …); monadic unglue outside strings (`TAN10`, `INKEY1`, …) |
| **Skips monadic on** | Full-line `REM` / `'` / `DATA` |
| **Runtime unglue** | **Still active** (dual-normalize until Phase 2 peels paths) |
| **LIST prints** | Stored text after entry canonicalize (PRETTY may still re-indent) |
| **Tests** | `test/test_entry_canonicalize.py` (idempotence, LOAD, REM, strings) |

### Phase 2a — monadic family (2026-08-09)

| | |
|--|--|
| **Hot path** | `_unglue_monadic_expr` → no-op unless `_expr_may_need_monadic_unglue` |
| **Skips when** | Already parenthesized monadic form (`TAN(10)`), pure comparisons, etc. |
| **Still unglues when** | Residual glue remains (`TAN10`, `NOT0`, `INKEY1`, `ASC"…"`) |
| **Immediate mode** | `execute_immediate` runs `canonicalize_program_line` per colon segment |
| **Next peels** | ~~operator normalize~~ (2c); remaining runtime rewrites |

### Phase 2c — operator normalize at eval (2026-08-14)

| | |
|--|--|
| **Hot path** | `_normalize_operators` → no-op unless `_expr_may_need_operator_normalize` |
| **Skips when** | Pure arithmetic after sub (`ZX*ZX+ZY*ZY<4`, `I%+1`) |
| **Still rewrites when** | `AND`/`OR`/`MOD`/`DIV`/`^`/`<<` glue or keywords (`10MOD3`, `A%AND1`) |
| **Still always** | `_RE_BAD_PERCENT_MOD` check (illegal `%` modulo) |
| **Tests** | `test_entry_canonicalize.test_phase2c_operator_normalize_fast_reject` |

### Phase 2b — BBC dialect line glue at `_parse_command` (2026-08-09)

| | |
|--|--|
| **Hot path** | `_parse_command` (bbc) → `_normalize_bbc_dialect_line` only if `_line_may_need_bbc_dialect_normalize` |
| **Skips when** | No residual glued forms (`PRINT TAB…`, `FOR I% = … TO …`, `MODE 5`, …) |
| **Still normalizes when** | `PRINTTAB`, `MODE5`, `FORI%=1TO10`, `DEFPROC4`, `END IF`, etc. |
| **Tests** | `test_entry_canonicalize.test_phase2b_bbc_dialect_fast_reject` |
