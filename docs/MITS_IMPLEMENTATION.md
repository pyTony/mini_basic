# MITS dialect implementation (from M6502 C-port tests)

**Date:** 2026-08-09  
**Source suite:** `examples/m6502-cport/` ([garyexplains/BASIC-M6502-CPORT](https://github.com/garyexplains/BASIC-M6502-CPORT))  
**Runner:** `test/test_m6502_cport_mits.py`  
**Filters:** `pytest -q -m "mits and not slow"` or `-m m6502_cport`

## What `mits` is

| | |
|--|--|
| **Target** | Classic numbered-line / GOTO-era Microsoft-style BASIC (MITS 8K / MS lineage) |
| **Examples** | ELIZA.BAS, M6502 C-port tutorials 01–48 |
| **Not** | BBC PROC/CASE/WHILE, mini extensions, BB4W byte arrays |

**Default posture:** identifier **fold** (case-insensitive names); 2-letter significance for classic MS-style names when folded. Statement keywords: uppercase-only when `CASE ON`, any case when folded (mits default is fold).

## Coverage vs M6502 tutorials (01–48)

Run under `--dialect mits`, `display=none`, case fold.

| Band | Programs | mini_basic mits |
|------|----------|-----------------|
| **Core I/O & vars** | 01–03, 05–07 | **Pass** — PRINT, arithmetic, float/string vars, comparisons, IF/THEN |
| **Control** | 09–14 | **Pass** — FOR/NEXT/STEP, nested FOR, GOSUB/RETURN, ON GOTO/GOSUB |
| **Arrays & DATA** | 15–20 | **Pass** — 1D/2D numeric, string arrays, DATA/READ/RESTORE |
| **Math & strings** | 23–28, 31–48 | **Pass** — SIN/…, LEFT$/MID$, VAL/STR$, TAB/SPC, AND/OR/NOT, algorithms |
| **Integer `%`** | 04 | **Pass** — `C%=A%*B%` (int slots survive mits 2-letter fold) |
| **Implicit zero** | 08 | **Pass** — unset numeric is 0 (`N=N+1`) |
| **DEF FN spaced** | 21–22 | **Pass** — `DEF FN S(X)=…` and `FN S(I)` |
| **PEEK/POKE/WAIT** | 29–30 | **Fail** — `POKE` / memory WAIT not implemented |

**Score (non-interactive ladder):** **46 / 48 pass** under current mits.

### Not in the automated pass set

| Band | Notes |
|------|--------|
| **49–50** | Interactive INPUT/GET |
| **51–60** | Host file I/O: C-port `OPEN ch,"file","OUTPUT"`; mini has `PRINT#` + `OPEN "O",#n` / `OPENOUT` |
| **apps/**, **adv/** | Interactive / multi-file; manual |

## Built-in dialect gates (mits)

Forbidden when dialect is mits (and other numbered-goto dialects) under strict/feature checks:

- Structured: `WHILE`/`WEND`, `REPEAT`/`UNTIL`, multi-line `IF`/`ENDIF`, `ELSEIF`
- Procedures: `PROC`/`ENDPROC`, `EXIT` (BBC-style)
- mini-only: `BREAK`/`CONTINUE`, mini ANSI/`ARG` helpers

Allowed and exercised by C-port tests: numbered programs, `GOTO`/`GOSUB`, classic `FOR`/`NEXT`, `ON … GOTO/GOSUB`, `DATA`/`READ`, scalar `DEF FN` (glued form), DIM arrays, PRINT zones.

## Case mode

| Mode | Keywords | Variables (mits default) |
|------|----------|---------------------------|
| Fold (mits default) | `print` / `PRINT` | Folded (`A` ≡ `a`) |
| Case on (`CASE ON`) | Uppercase only | Significant case + full length |

## How to re-run

```powershell
# M6502 C-port regression only
python -m pytest -q -m "m6502_cport" --timeout=30

# All mits-tagged tests
python -m pytest -q -m "mits and not slow" --timeout=45

# Manual single example
python -m mini_basic -q --dialect mits examples\m6502-cport\01_hello.bas
```

## Gaps left (not regular 1.00)

1. `POKE` / `PEEK` / memory `WAIT` — host-memory stubs only if demanded  
2. C-port `OPEN ch,path,mode` alias for file examples 51–60 (out of regular 1.00)

## Related code

- Dialect gates: `mini_basic/runtime_parts/dialect.py`, `constants.MITS_FORBIDDEN_CMDS`  
- Compatibility matrix: REPL `MATRIX` / `HELP DIALECTS`  
- Examples + notes: `examples/m6502-cport/README.md`  
