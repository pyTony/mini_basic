# mini_basic 1.00 — regular (BASICS) release

**Status:** Public repo default is **`main`**. Package version on `main` stays **1.0.0.dev0** until you tag.  
**Language baseline:** [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md)

This is the **regular 1.00** product: a multi-dialect BASIC interpreter, text
and graphical (pygame window) alike. Graphics is the normal way most programs
run — it's just one more pip extra, since pygame is a native dependency. A
**text-only** CLI install (no pygame) is also available for people who can't
or don't want a graphics dependency. 1.00 is not a packaging/build toolkit
and not full BBCSDL.

---

## What’s in regular 1.00

### Dialects
| Dialect | Role |
|---------|------|
| **mini** | Default superset (numbered + unnumbered) |
| **bbc** | BBCSDL/BB4W-oriented language (text programs; not Beeb-only) |
| **mits** | Classic numbered/GOTO (ELIZA, M6502 C-port tutorials) |
| **commodore** / **tiny** | Teaching / museum subsets |

Case-on (default mini/bbc): names case-sensitive. **bbc** keywords uppercase only; **mini** accepts any keyword case. `CASE OFF` folds keywords.

### Language / REPL
- Numbered + unnumbered programs; `LOAD`/`SAVE`/`LIST`/`EDIT`/`AUTO`; session scripts (`INPUT.TXT`, `-c`, stdin)
- Control: `FOR`/`NEXT`, `WHILE`, `REPEAT`, `IF`/`THEN`/`ELSE`/`ENDIF`, compact IF, `CASE`, `PROC`/`FN`, `ON ERROR`
- Files: `OPENIN`/`OPENOUT`, `PRINT#`/`INPUT#`/`CLOSE#`, MS `OPEN "O",#n,"file"`
- Arrays: `PRINT a(i)`, whole-array ops (`Colour&()`, `OR=`, `SUM`)
- Floats: IEEE double; `%` bigint by default (`_bigint`)
- `HELP` including **HELP CLI** (= `--help`)

### Graphics
`MODE`, `--pygame`, the pygame display window — this is how most of the
showcase demos run. It's a separate pip extra (`[display]`) only because
pygame is a native dependency, not because it's a niche feature; see
[How to run](#how-to-run) below.

### Not in regular 1.00
- `build/`, `dist/`, embed Python, corpus installer trees
- SOUND/ENVELOPE (silent stubs), WIMP, SYS FFI, Box2D
- C-port `OPEN ch,"file","OUTPUT"` spelling

---

## How to run

With graphics (pip from GitHub) — the normal install, for `MODE`/pygame demos
like the showcase reel:

```text
python -m pip install "mini-basic[display] @ git+https://github.com/pyTony/mini_basic.git"
mini-basic --version
python -m mini_basic --pygame examples\mini\bbc_graphics_demo.bas
```

From a source checkout (examples + HTML docs at `docs/site/index.html`):

```text
git clone https://github.com/pyTony/mini_basic.git
cd mini_basic
python -m pip install -e ".[display]"
python -m mini_basic --pygame file.bas
python -m mini_basic --dialect bbc piechart…
python -m mini_basic --dialect mits examples\m6502-cport\01_hello.bas
python -m mini_basic --version
python -m mini_basic -h
```

Env: `MINIBASIC_DIR`, `MINI_BASIC_DIALECT`. Text sessions stay text.

Examples and developer files live on the **`dev` branch**, not in a pip wheel
and not on `main`:

- Repo: [https://github.com/pyTony/mini_basic](https://github.com/pyTony/mini_basic)
- Examples: [examples/](https://github.com/pyTony/mini_basic/tree/dev/examples)
- Developer git notes: [GIT_QUICKSTART.md](https://github.com/pyTony/mini_basic/blob/dev/GIT_QUICKSTART.md)

```text
git clone -b dev https://github.com/pyTony/mini_basic.git
```

Third-party sources: [M6502 C-port](https://github.com/garyexplains/BASIC-M6502-CPORT) · [BBCSDL examples](https://github.com/rtrussell/BBCSDL/tree/master/examples)

---

## Text-only install (no pygame)

For people who can't or don't want the pygame dependency — a restricted CLI
environment, a headless box, or just a preference for text programs — the
interpreter runs fine without it:

```text
pip install "mini-basic[repl]"
python -m mini_basic basics/ELIZA.BAS
```

`MODE`/`--pygame` programs won't run without the `[display]` extra, but
everything else (REPL, file I/O, the non-graphical dialects/demos) works.

### Known limitations (graphics)

- **Flicker / jerky motion in some real-time demos** (e.g. `swirl.bbc` on the
  `dev` branch, [#12](https://github.com/pyTony/mini_basic/issues/12)).
  These programs pace their animation off a wall-clock tick count
  (`TIME`/`SYS "timeGetTime"`) so the *math* always reflects true elapsed
  time, but mini_basic is a tree-walking Python interpreter: how long each
  animation frame takes to *compute* varies, and the display only presents
  at a capped rate (~20 Hz, dropping to ~10 Hz during heavy `PLOT` bursts —
  see `_flush_display` / `_present_min_interval` in
  `mini_basic/runtime_parts/io.py`). The result is uneven, sometimes-jerky
  real-time presentation even though each frame's computed position is
  correct. This is a performance characteristic of the interpreter, not a
  logic bug; no fix is planned for 1.0.
- **`CALL &FFF1` / `OSWORD 10`** (cursor-position readback) is unsupported —
  tracked as [#11](https://github.com/pyTony/mini_basic/issues/11),
  deprioritized; not needed for 1.0.

### Known limitations (graphics flavor)

- **Flicker / jerky motion in some real-time demos** (e.g. `examples/graphics/swirl.bbc`,
  [#12](https://github.com/pyTony/mini_basic/issues/12)). These programs pace
  their animation off a wall-clock tick count (`TIME`/`SYS "timeGetTime"`) so
  the *math* always reflects true elapsed time, but mini_basic is a
  tree-walking Python interpreter: how long each animation frame takes to
  *compute* varies, and the display only presents at a capped rate (~20 Hz,
  dropping to ~10 Hz during heavy `PLOT` bursts — see `_flush_display` /
  `_present_min_interval` in `mini_basic/runtime_parts/io.py`). The result is
  uneven, sometimes-jerky real-time presentation even though each frame's
  computed position is correct. This is a performance characteristic of the
  interpreter, not a logic bug; no fix is planned for 1.0.
- **`CALL &FFF1` / `OSWORD 10`** (cursor-position readback) is unsupported —
  tracked as [#11](https://github.com/pyTony/mini_basic/issues/11),
  deprioritized; not needed for 1.0.

---

## Tag checklist (user gate — do not auto-tag)

1. [ ] Accept this file + LANGUAGE_FEATURES_1.00  
2. [ ] `__version__` / `pyproject.toml` already `1.0.0`  
3. [ ] `pytest -q -m "phase1 and not slow"` green on the release machine  
4. [ ] `git tag 1.0.0` when you want it

---

## After 1.00 (light)

- poem MODE 7 audit path (graphics flavor)
- Teletext remainder / SYS only if demanded
