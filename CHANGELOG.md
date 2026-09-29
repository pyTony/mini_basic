# Changelog

Format: one line per merged PR, newest first. See [GitHub Issues](https://github.com/pyTony/mini_basic/issues) for open work.

## 2026-09-29 (branch fix/edge-case-bugs-ap0pn0, PR number when merged)

- perf: string expressions are parsed once and cached (string-heavy loops about 2x faster); `LEN/ASC/VAL/INSTR` of a string stay compiled
- fix: `PRINT LEN(A$)+1`, `PRINT ASC("A")+1`, `PRINT VAL("12")+1` raised "expected string value" in every dialect (the first operand now decides the type)
- perf: `AND (` / `OR (` in a compiled condition was mistaken for an array read, forcing the slow path every iteration (Mandelbrot `WHILE (I%<M%) AND (...)` 0.56s -> 0.10s per 20000 iterations)
- fix: mits / commodore / tiny uppercase lines at entry (strings, comments, DATA payloads untouched); `REM Note Tanx` was stored as `REM NOT e Tan(x)`, comments are now kept as typed in every dialect
- fix: `""` inside a string literal is one quote (checked on Archimedes BASIC V) in PRINT, EVAL and string expressions; `EVAL` of a string returned 0, `X$=EVAL("A$")` was a syntax error
- fix: `INKEY(-n)` is TRUE only while that BBC key is down (was: code of any pressed key, or -1 when idle); glued `INKEY-99` meant `INKEY - 99`
- fix: a bad expression in `IF` / `WHILE` / `REPEAT` / `FOR` is a BASIC error with a line number instead of a Python traceback
- fix: an error inside a `DEF FN` body now reaches the outer `ON ERROR` with its own message and line (was "DEF FN jump outside body")
- fix: `_split_bbc_juxtaposed_string_parts` looped forever on a top-level `+`
- feat: `VDU 23,23,t|` line thickness applies to `LINE` / `DRAW` / `PLOT` lines (snowscene.bbc tree)

## 2026-09-26

- #9 Scope COLOUR 136-143 flash to non-custom palette entries; skip Windows-only test
- #8 perf: fix Mandelbrot ANSI slowdown (WHILE guard fast path + IF parse cache) — Mandel_ANSI 1.9s -> 0.47s
- #7 Fill PLOT 112-119 parallelograms instead of drawing a line
- #6 BBC DIM p n memory blocks with ?/! reads and stores
- #5 Run swirl.bbc: SYS SDL calls, struct members in mini, ABSSIN, PLOT arcs
- #4 Stop the program when the pygame window is closed with X
- #3 disco.bbc: byte variables and RECTANGLE outline / SWAP / TO

## 2026-09-25

- #2 Edge-case fixes: == equality, INKEY(-256) platform id, negative INKEY in bbc
