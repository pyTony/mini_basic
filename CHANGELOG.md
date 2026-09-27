# Changelog

Format: one line per merged PR, newest first. See [GitHub Issues](https://github.com/pyTony/mini_basic/issues) for open work.

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
