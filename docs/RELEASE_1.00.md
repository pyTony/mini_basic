# mini_basic 1.00 — release notes (prep)

**Status:** Ready to tag when you say so  
**Packaging version today:** `1.0.0.dev0` (`mini_basic/version.py` + `pyproject.toml`)  
**Tag to apply:** `1.0.0` (also set both version files to `1.0.0`)  
**Language baseline:** [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md)

This is the **honest 1.00** product: multi-dialect interpreter + BBC graphics tier A + corpus OK-or-DEFER. It is not full BBCSDL, RISC OS, or period-accurate float.

---

## What’s in 1.00

### Dialects
| Dialect | Role |
|---------|------|
| **mini** | Default superset (numbered + unnumbered, BBC-like + extensions) |
| **bbc** | BBCSDL/BB4W-oriented (not Beeb-only; includes some Russell array/`&` forms) |
| **mits** | Classic numbered/GOTO (ELIZA, M6502 C-port tutorials) |
| **commodore** / **tiny** | Teaching / museum subsets |

Case-on (default mini/bbc): **keywords uppercase**; names case-sensitive. `CASE OFF` folds keywords.

### Language / REPL
- Numbered + unnumbered programs; `LOAD`/`SAVE`/`LIST`/`EDIT`/`AUTO`; session scripts (`INPUT.TXT`, `-c`, stdin)
- Control: `FOR`/`NEXT`, `WHILE`, `REPEAT`, `IF`/`THEN`/`ELSE`/`ENDIF`, compact IF, `CASE`, `PROC`/`FN`, `ON ERROR`
- Files: `OPENIN`/`OPENOUT`, `PRINT#`/`INPUT#`/`CLOSE#`, MS `OPEN "O",#n,"file"`
- Arrays: `PRINT a(i)`, whole-array ops used by piechart (`Colour&()`, `OR=`, `SUM`)
- Floats: IEEE double; `%` bigint by default (`_bigint`)
- `HELP` including **HELP CLI** (= `--help`)

### Graphics (tier A)
MODE, GCOL, MOVE/DRAW/PLOT, CIRCLE, COLOUR, ORIGIN, *REFRESH, VDU A–C (17/20/24/26/28/30/cursor/23 stubs). MODE 7 teletext partial.

User-approved demos: welcome, squares, saucer, flier, soccerball, wheel, jclock, filters, hanoi, animal, piechart.

### Corpus
Portable games/graphics/general only (no tools/physics/sounds trees).  
**DEFER:** poem (interactive MODE 7).

---

## What’s not in 1.00

SOUND/ENVELOPE (silent stubs), WIMP, SYS FFI, Box2D, full SAA5050, Beeb-pure dialect (`bbc classic` not shipped), C-port `OPEN ch,"file","OUTPUT"` spelling.

---

## How to run

```text
python -m mini_basic file.bas
python -m mini_basic --dialect bbc piechart…
python -m mini_basic --dialect mits examples\m6502-cport\01_hello.bas
python -m mini_basic --version
python -m mini_basic -h
```

Env: `MINIBASIC_DIR`, `MINI_BASIC_DIALECT`, `MINIBASIC_NO_GRAPHICS` / `MINIBASIC_DISPLAY`, `SDL_VIDEODRIVER=dummy` (CI).

---

## Tag checklist (user gate — do not auto-tag)

1. [ ] Accept this file + LANGUAGE_FEATURES_1.00  
2. [ ] Set `__version__` and `pyproject.toml` to `1.0.0`  
3. [ ] `pytest -q -m "phase1 and not slow"` green on the release machine  
4. [ ] `git tag 1.0.0` (and optional `1.00` alias)  
5. [ ] FEATURES_DONE: `-- 1.00 ship` → `OK 1.00 tagged …`

---

## After 1.00 (light)

- poem MODE 7 audit path  
- Optional saucer speed  
- Teletext remainder / SYS only if demanded  
