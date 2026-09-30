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

Case-on (default mini/bbc): names case-sensitive. **bbc** keywords uppercase only; **mini** accepts any keyword case. `CASE OFF` folds keywords.

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

Run on the release machine, in this order. Tag name is `1.0.0` (no `v`).

1. [ ] Accept this file + [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md); add the PR number to the newest [CHANGELOG.md](../CHANGELOG.md) section header.
2. [ ] Full suite green: `python -m pytest -q` (last run: 1283 passed, 4 skipped, 1 xfailed, Windows / PyPy 3.11).
3. [ ] Merge the release branch into `main`.
4. [ ] Bump `1.0.0.dev0` → `1.0.0` in **all** of these (the version currently lives in six places):
   - `mini_basic/version.py` (`__version__`)
   - `pyproject.toml` (`version =`; keep in sync with `version.py`)
   - `README.md` (line "Version: … pre-release `1.0.0.dev0` until tagged")
   - `docs/LANGUAGE_FEATURES_1.00.md` (**Version line**)
   - `docs/RELEASE_1.00.md` (Status line, top of this file)
   - `documentation/build_minibasic_manual.py` (fallback version string)
   
   Then `python scripts/build_user_docs.py` to rebuild `docs/site/`, and check with `grep -rn "dev0" --include=*.py --include=*.toml --include=*.md .` that only history (CHANGELOG, PACKAGING wording) is left.
5. [ ] `python -m mini_basic --version` prints `1.0.0`; commit `release: 1.0.0` on `main`.
6. [ ] `git tag 1.0.0` and `git push origin 1.0.0`.
7. [ ] Fresh-clone check (a temporary folder, not the dev checkout):
   ```text
   python -m pip install "mini-basic[repl] @ git+https://github.com/pyTony/mini_basic.git"
   mini-basic --version
   python -m mini_basic -c "PRINT 6*7"
   ```

---

## After 1.00 (light)

- poem MODE 7 audit path (graphics flavor)
- Teletext remainder / SYS only if demanded
