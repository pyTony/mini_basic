# mini_basic 1.00 — regular (BASICS) release

**Status:** Public repo default is **`main`**. Package version on `main` stays **1.0.0.dev0** until you tag.  
**Language baseline:** [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md)

This is the **regular 1.00** product: a multi-dialect BASIC interpreter for the terminal.
It is not a packaging/build toolkit, not pygame, and not full BBCSDL.

---

## What’s in regular 1.00

### Dialects
| Dialect | Role |
|---------|------|
| **mini** | Default superset (numbered + unnumbered) |
| **bbc** | BBCSDL/BB4W-oriented language (text programs; not Beeb-only) |
| **mits** | Classic numbered/GOTO (ELIZA, M6502 C-port tutorials) |
| **commodore** / **tiny** | Teaching / museum subsets |

Case-on (default mini/bbc): **keywords uppercase**; names case-sensitive. `CASE OFF` folds keywords.

### Language / REPL
- Numbered + unnumbered programs; `LOAD`/`SAVE`/`LIST`/`EDIT`/`AUTO`; session scripts (`INPUT.TXT`, `-c`, stdin)
- Control: `FOR`/`NEXT`, `WHILE`, `REPEAT`, `IF`/`THEN`/`ELSE`/`ENDIF`, compact IF, `CASE`, `PROC`/`FN`, `ON ERROR`
- Files: `OPENIN`/`OPENOUT`, `PRINT#`/`INPUT#`/`CLOSE#`, MS `OPEN "O",#n,"file"`
- Arrays: `PRINT a(i)`, whole-array ops (`Colour&()`, `OR=`, `SUM`)
- Floats: IEEE double; `%` bigint by default (`_bigint`)
- `HELP` including **HELP CLI** (= `--help`)

### Not in regular 1.00
- pygame / `--pygame` / graphical MODE (optional extra only — see below)
- `build/`, `dist/`, embed Python, corpus installer trees
- SOUND/ENVELOPE (silent stubs), WIMP, SYS FFI, Box2D
- C-port `OPEN ch,"file","OUTPUT"` spelling

---

## How to run

Interpreter only (pip from GitHub):

```text
python -m pip install "mini-basic[repl] @ git+https://github.com/pyTony/mini_basic.git"
mini-basic --version
python -m mini_basic -c "PRINT 6*7"
```

From a source checkout (examples + HTML docs at `docs/site/index.html`):

```text
git clone https://github.com/pyTony/mini_basic.git
cd mini_basic
python -m pip install -e ".[repl]"
python -m mini_basic file.bas
python -m mini_basic --dialect bbc piechart…
python -m mini_basic --dialect mits examples\m6502-cport\01_hello.bas
python -m mini_basic --version
python -m mini_basic -h
```

Env: `MINIBASIC_DIR`, `MINI_BASIC_DIALECT`. Text sessions stay text.

Examples and developer files live in the **git tree**, not in a pip wheel:

- Repo: [https://github.com/pyTony/mini_basic](https://github.com/pyTony/mini_basic)
- Examples: [examples/](https://github.com/pyTony/mini_basic/tree/main/examples)
- Developer git notes: [GIT_QUICKSTART.md](https://github.com/pyTony/mini_basic/blob/main/GIT_QUICKSTART.md)

```text
git clone https://github.com/pyTony/mini_basic.git
```

Third-party sources: [M6502 C-port](https://github.com/garyexplains/BASIC-M6502-CPORT) · [BBCSDL examples](https://github.com/rtrussell/BBCSDL/tree/master/examples)

---

## Optional flavor (not regular 1.00)

Graphics (`MODE`, pygame window) stay in the tree for people who want them:

```text
pip install "mini-basic[display]"
python -m mini_basic --pygame examples\mini\bbc_graphics_demo.bas
```

Regular users never need this.

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
