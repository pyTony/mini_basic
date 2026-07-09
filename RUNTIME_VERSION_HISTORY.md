# mini_basic Runtime.py Version History (Cleaned)

**Note on agent resource improvements:** To keep repeated agent work light on memory (avoiding ~283MB peaks and 296MB alloc crashes recorded in .resource_crash.json), shift comparisons and history to **git diffs/versions** instead of loading full files. See DEVELOPMENT_GIT_USAGE.md for details and commands like `git diff`, `git show`, `git log`.

**Focus:** Successful progression only. Back-and-forth unsuccessful experiments (files named with "problem", "failed", "bad", "try", "implied_failed", "plusequalbad", "counter_try", "next problem", "window_flash", "phone", etc.) have been ignored as requested.

**Source:** Timestamped backup files in `C:\Users\Tony\mini_basic` (future: derive from git).

**Current Production Version:** `mini_basic\runtime.py` (500,154 bytes, 2026-07-09 00:34:07)

This is a cleaned "version history" showing the meaningful lineage of changes.

## Clean Successful Lineage

| Date/Time          | File                                      | Size   | Notes / Key Changes |
|--------------------|-------------------------------------------|--------|---------------------|
| 2026-06-25 02:50  | backup\mini_basic\runtime.py             | 445k  | Early base version |
| 2026-06-25 10:41  | backup\runtime.bak.py                    | 440k  | Backup of early state |
| 2026-06-29 20:56  | backup\runtime.backup.py                 | 438k  | Working backup |
| 2026-06-30 12:11  | backup\runtime_bak_25.6.py               | 446k  | Later June state |
| 2026-06-30 23:55  | backup\runtime_working.py                | 438k  | "Working" milestone |
| 2026-07-04 13:16  | backup\runtime_3.7.2026.py               | 471k  | **Growth phase** – significant expansion |
| 2026-07-06 11:34  | backup\runtime_2026-07-06.py             | 474k  | Base for July 6 fix day |
| 2026-07-06 12:54  | backup\runtime_fixed_goto_unwind.py      | 474k  | Fix: GOTO / loop control flow unwind |
| 2026-07-06 13:12  | backup\runtime_fixed_rem_lines.py        | 474k  | Fix: REM line handling |
| 2026-07-06 13:16  | backup\runtime_fixed_bare_number_lines.py| 474k  | Fix: Bare numbered lines (number-only lines) |
| 2026-07-06 13:40  | backup\runtime_final_rem_fix.py          | 474k  | Final REM fixes |
| 2026-07-06 13:43  | backup\runtime_final_clean_rem.py        | 474k  | Clean REM stripping (explicit comment-only early return) |
| 2026-07-06 21:42  | backup\runtime_final_early_numbered.py   | 474k  | Final early numbered line handling |
| 2026-07-06 21:58  | backup\runtime_minimal_safe.py           | 474k  | Minimal safe state after fixes |
| 2026-07-06 22:10  | backup\runtime_with_debug.py             | 474k  | With debug support |
| 2026-07-06 22:34  | backup\runtime_rem_fix.py                | 473k  | Additional REM refinement |
| 2026-07-08 12:00  | test_reconstruct\mini_basic\runtime.py   | 509k  | Reconstruct snapshot (post-fix + features) |
| 2026-07-08 16:53  | mini_basic_test_bom\mini_basic\runtime.py| 497k  | BOM/test snapshot |
| 2026-07-09 00:34  | mini_basic\runtime.py                    | 500k  | **Current main** – feature growth on top of July 6 fixes |

## Summary of Successful Progression

**June 25 – June 30:** Base implementation and stabilization. Incremental improvements leading to a "working" state.

**July 4:** Major growth/refactor. Size increases substantially as new capabilities are added.

**July 6 Fix Sprint (most critical for correctness):**
This day produced a clear sequence of targeted, successful fixes on top of the 2026-07-06 base:
- GOTO/unwind control flow
- REM handling (multiple iterations, culminating in clean stripping)
- Bare numbered lines support
- General cleanup toward "minimal safe"

These fixes addressed core parsing and execution issues for classic BASIC programs (numbered lines, REM comments, control structures).

**July 8–9:** 
- Snapshots for reconstruction and testing.
- Current main `runtime.py` (500k) adds significant new features (structs, improved dialect handling, case-sensitive BBC support, etc.) while building on the July 6 fixes.
- Four smaller variants created same day (`option_a`, `both_fixes`, `modulo_fixed`, `cursor_fix`) appear to be experimental branches.

## Comparison to Current Version

The current `mini_basic\runtime.py` (July 9, 500k) is the result of:
- All the successful July 6 parsing fixes (REM, bare numbers, GOTO unwind)
- Plus later feature additions that increased size by ~25–30k bytes.

**Evidence of July 6 fixes being present (but evolved):**
- `_parse_bare_line_number` and handling for number-only lines
- `_split_colon_statements` + `_is_rem_only_statement`
- Gosub stack and control flow logic
- Modulo vs % suffix handling

**Key differences from July 6 "final" versions:**
- Current has more advanced `dialect_hint` integration (`parse_comment_dialect_line`)
- Struct support added
- Refined normalization (more careful with % for modulo)
- Some early "return [] for pure REM" patterns from `final_clean_rem.py` have been generalized

The main line successfully carried forward the critical July 6 fixes while adding substantial new functionality.

## Notes

- July 6 represents the most concentrated successful debugging effort visible in the backup history.
- Later development focused on features rather than re-opening the core parsing fixes.
- The side variants on July 9 were not folded into the main 500k file (they remain smaller and separate).

This document reflects the clean successful progression only.