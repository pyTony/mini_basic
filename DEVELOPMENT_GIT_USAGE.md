# Git Usage for mini_basic Development

**Quick start:** `GIT_QUICKSTART.md`  
**LLM notes:** `docs/LLM.md`

---

## 1. Layout

**Project root:** `C:\Users\Tony\mini_basic`

| Path | Role |
|------|------|
| `C:\Users\Tony\mini_basic` | **Git working tree** (use this) |
| `C:\Users\Tony\Programming\mini_basic` | Optional **install / run** copy (often **not** a git repo) |

**Do not** maintain two divergent git histories with manual `Copy-Item` as the primary workflow.

```powershell
cd C:\Users\Tony\mini_basic
git rev-parse --show-toplevel
```

---

## 2. What must be in git

The modular package is the product. **Track**:

- `mini_basic/**/*.py` including `runtime_parts/`, `util/`, `repl/`, `features/`, `expr/`, `format/`
- `mini_basic/version.py`, `__init__.py`, `__main__.py`
- Focused tests: `test/test_*.py` (not probe scripts)
- `pytest.ini`, `.gitignore`, `README.md`, `HOWTO.md`
- Curated demos: `examples/vdu/`, `examples/teletext/`, small bas files

**Ignore** (see `.gitignore`): probes, coverage, `__pycache__`, resource JSON churn, most generated `dist/` archives.

If `git status -u --short -- mini_basic/` shows many `??` package files, the history is incomplete — add them on the next feature commit.

---

## 3. Daily workflow

```powershell
cd C:\Users\Tony\mini_basic

# Branch per focus
git checkout main
git checkout -b fix/topic-name

# Work + tests
python -m pytest -q -m "phase1 and not slow" --timeout=45

# Stage deliberately (avoid git add . when status is huge)
git add mini_basic/display.py mini_basic/version.py
git add test/test_rgb_dirty_coords.py
git add .gitignore GIT_QUICKSTART.md DEVELOPMENT_GIT_USAGE.md

git status   # confirm no _probe_*, no .coverage
git commit -m "fix: short description"
```

Merge to `main` only after user approval of the focused work (same as before).

---

## 4. MINIBASIC_DIR

| Variable | Meaning |
|----------|---------|
| `MINIBASIC_DIR` | Install/launcher tree (`C:\Users\Tony\mini_basic`) |
| Git toplevel | `C:\Users\Tony\mini_basic` |

```powershell
python -m mini_basic --version   # package path + MINIBASIC_DIR
```

Install scripts (`tools/install.ps1`, `tools/dev_install.ps1`) set `MINIBASIC_DIR`; they do not replace git.

---

## 5. Text archives / distribution

- `tools/create_text_archive.py` / reconstruct scripts produce `*_text_part*.txt`.
- Those parts are **distribution artifacts** — usually ignored by `.gitignore`.
- Ship process: generate parts → distribute → do not treat them as primary code history.

---

## 6. Branching (unchanged principles)

```powershell
git checkout -b fix/soccerball-green-screen
# … fix + tests …
git commit -m "fix: blank text cells must not overpaint graphics after COLOR 130"
# after approval:
git checkout main
git merge --no-ff fix/soccerball-green-screen
git branch -d fix/soccerball-green-screen
```

Naming: `fix/…`, `feat/…`, `docs/…`, `test/…`.

---

## 7. Checklist

1. `cd C:\Users\Tony\mini_basic`; confirm `git rev-parse --show-toplevel`.
2. Create/switch to a **branch** for the single focus.
3. Prefer explicit `git add` paths; never commit probe dumps.
4. Run `pytest -m "phase1 and not slow"` (includes phase0).
5. **Do not** invent a second repo under `Programming/` unless the user asks.

---

## 8. Useful commands

```powershell
# Package still untracked?
git status -u --short -- mini_basic/ | Select-String "^\?\?"

# Noise only?
git status --porcelain | Select-String "test/_probe|__pycache__|\.coverage"

# Diff code only
git diff --stat -- mini_basic/

# Recent branch commits
git log --oneline -15
git branch -vv
```

---

## 9. Optional: seed a full package commit

If the package was never fully added after modularization:

```powershell
cd C:\Users\Tony\mini_basic
git checkout -b chore/track-modular-package
git add mini_basic/
git add test/test_*.py test/conftest.py pytest.ini
git add .gitignore GIT_QUICKSTART.md DEVELOPMENT_GIT_USAGE.md
git status   # review size; drop accidental binaries
# commit only when you intend to snapshot the package:
# git commit -m "chore: track modular mini_basic package and phase tests"
```

Do this as its own chore branch so feature history stays readable.
