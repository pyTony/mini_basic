# mini_basic Runtime.py Version History

**Source:** Analysis of all `runtime*.py` backup and variant files in the full source tree (`C:\Users\Tony\mini_basic`).

**Current Production Version:** `mini_basic\runtime.py` (500,154 bytes, modified 2026-07-09 00:34:07)

This document provides a chronological "version history" reconstructed from timestamped backup files. These files were created during active development and debugging, often by different LLM/agent sessions.

## Timeline Overview

| Phase | Dates          | Approx. Size | Key Files / Events |
|-------|----------------|--------------|--------------------|
| Early Debugging | 2026-06-25 to 06-30 | 435k–445k | Many "problem", "working", "xxx_bad" variants |
| Growth | 2026-07-04 | 471k–472k | First major size increase |
| Fix Sprint | 2026-07-06 | 473k–474k | Intensive "fixed_" and "final_" series |
| Modern | 2026-07-08 to 07-09 | 496k–509k / 500k | Reconstructs + current main + side variants |

---

## Phase 1: Early Debugging (June 25–30, 2026)

**Files (sorted by time):**
- `backup\mini_basic\runtime.py` (2026-06-25 02:50, 445k)
- `backup\runtime.bak.py` (2026-06-25 10:41)
- `backup\Running problems\mini_basic\runtime_bak.py` (06-26)
- `backup\Running problems\mini_basic\runtime (1).py` (06-27 19:12)
- `backup\Running problems\mini_basic\runtime.py` (06-27 23:38)
- `backup\runtime_phone.py` (06-28)
- `backup\runtime_window_flash.py` (06-29 17:54)
- `backup\runtime_problem.py` (06-29)
- `backup\runtime_steady.py`
- `backup\runtime_variables.py` / `runtime_plusequalbad.py`
- `backup\runtime OK Slow.py` / `runtime.backup.py`
- `backup\runtime_counter_try.py`
- `backup\runtime_next problem.py`
- `backup\runtime_bak_25.6.py` (06-30 12:11, 445k)
- `backup\runtime_working.py`
- `backup\runtime_implied_failed.py` (07-01)

**Characteristics:**
- High frequency of new files, often named after the bug being chased.
- Focus areas (inferred from names and context):
  - `plusequalbad` → Compound assignment (`+= -= *= /=`)
  - `implied_failed` → Implied LET / bare assignments
  - `window_flash`, `phone` → Display / cursor / OneDrive-related issues
  - `counter_try` → TIME / counter variables
  - General stability and parsing crashes

**State of code:** Relatively smaller, more "raw" versions of the interpreter. Lots of iterative patching.

---

## Phase 2: Growth & Refactoring (July 4, 2026)

- `backup\runtime_3.7.2026.py` (471k)
- `backup\runtime_problem_4.7.2026.py` (472k)

**Change:** Noticeable size increase (~25–35k bytes). Suggests addition of new features, better error handling, or significant refactoring rather than pure bug fixes.

---

## Phase 3: The Great Fix Sprint (July 6, 2026)

This is the most important phase for understanding current robustness.

**Sequence (by time):**
1. `backup\runtime_2026-07-06.py` (11:34, 474k) – Base for the day
2. `backup\runtime_fixed_goto_unwind.py` (12:54)
3. `backup\runtime_fixed_rem_lines.py` (13:12)
4. `backup\runtime_fixed_bare_number_lines.py` (13:16)
5. `backup\runtime_final_rem_fix.py` (13:40)
6. `backup\runtime_final_clean_rem.py` (13:43)
7. `backup\runtime_final_early_numbered.py` (21:42)
8. `backup\runtime_minimal_safe.py` (21:58)
9. `backup\runtime_with_debug.py` (22:10)
10. `backup\runtime_rem_fix.py` (22:34)

**Key Fixes Introduced in This Phase:**
- **REM handling**: Multiple attempts to cleanly strip whole-line REMs and comments inside colon-separated statements. `final_clean_rem.py` had very explicit early returns for comment-only lines.
- **Bare numbered lines**: Dedicated logic so that a line containing *only* a number (no statement) is treated specially (especially important for LOAD to avoid polluting line 0).
- **GOTO / control flow**: Specific fixes for unwind behavior with FOR/NEXT, WHILE, GOSUB, etc.
- General push toward "minimal safe" and "final" states.

These files represent concentrated effort (likely multiple LLM sessions in one day) on classic BASIC program compatibility.

---

## Phase 4: Current Version (July 8–9, 2026)

- `test_reconstruct\mini_basic\runtime.py` (508k, July 8)
- `mini_basic_test_bom\mini_basic\runtime.py` (496k, July 8)
- **Current main**: `mini_basic\runtime.py` (500k, 2026-07-09 00:34)
- Side-by-side experiments (same minute):
  - `runtime_option_a.py`
  - `runtime_both_fixes.py`
  - `runtime_modulo_fixed.py`
  - `runtime_cursor_fix.py`

**What Changed vs July 6 Cluster:**
- Size increased by ~25–30k bytes.
- New features visible in code:
  - Full struct/record support (`struct_defs`, `struct_members`)
  - Improved dialect hint system (`parse_comment_dialect_line`)
  - Case-sensitive BBC keyword parsing (`_RE_PARSE_CMD_BBC`)
  - More sophisticated statement splitting and label extraction
- Some July 6 "clean" patterns appear altered or generalized.

**The July 9 Variants:**
These four files (~473k) were created at almost the exact same time as the main 500k file. They contain targeted fixes (modulo, cursor, "both") that differ from the main. This suggests parallel development branches that were not cleanly merged.

---

## Specific Technical Differences (Current vs July 6 Fixes)

### REM / Comment Handling
- **July 6 final versions** (e.g. `runtime_final_clean_rem.py`):
  ```python
  if stripped.startswith("'") or stripped.upper().startswith("REM"):
      return []   # whole line is a comment → produce no statements
  ```
- **Current main**:
  Uses `_is_rem_only_statement()` and tends to return `[stripped]` in some paths. More integrated with dialect hints but the explicit early "no statements" path for pure REM lines is less prominent.

### Bare Numbered Lines
- Dedicated fix files had clear comments and special return-None logic for "number only" lines during LOAD.
- Current has `_parse_bare_line_number`, but behavior is more REPL-oriented (delete line) than the strict LOAD protection seen in the fixes.

### Other Areas
- Glue/suffix normalization evolved (current is more careful with `%` because it is also the modulo operator).
- Significant new code for structs and advanced dialect support.

---

## Observations & Risks

1. **Feature Growth vs Robustness**: The current version is more capable but appears to have traded some of the ultra-defensive parsing logic developed on July 6 for new features.

2. **Fragmented Development**: The existence of multiple `runtime_*.py` files on July 9 is evidence of LLM/agent sessions working in parallel without strong merge discipline.

3. **Lost or Diluted Fixes**: 
   - Clean REM early-return behavior
   - Explicit bare-number LOAD handling
   - Some of the "both_fixes" / modulo / cursor work from the variants

4. **Reconstruct / BOM copies**: The July 8 larger files in `test_reconstruct` and `mini_basic_test_bom` suggest attempts to snapshot "known good" states for distribution/testing.

---

## Recommendation

When working on `runtime.py`, always cross-reference:
- `backup\runtime_final_clean_rem.py`
- `backup\runtime_fixed_bare_number_lines.py`
- `mini_basic\runtime_both_fixes.py`

These contain battle-tested fixes that may have been partially lost during feature addition.

**Current production runtime (as of 2026-07-09):**
`mini_basic\mini_basic\runtime.py` (500154 bytes)

This document was generated as part of ongoing maintenance of the development pipeline.
