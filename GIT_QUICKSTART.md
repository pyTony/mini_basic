# Git Quick Start (mini_basic)

## Where the repo lives

**Project root:** `C:\Users\Tony\mini_basic`

Remote: [https://github.com/pyTony/mini_basic](https://github.com/pyTony/mini_basic)  
(`git clone https://github.com/pyTony/mini_basic.git`)

| Path | What it is |
|------|------------|
| `C:\Users\Tony\mini_basic` | **Git working tree** (use this) |
| `C:\Users\Tony\Programming\mini_basic` | Optional install / run copy (often **not** a git repo) |

```powershell
cd C:\Users\Tony\mini_basic
git status
git rev-parse --show-toplevel
```

Do **not** treat `Programming\mini_basic` as a second source of truth unless you intentionally put a clone there.

## Daily rules

1. **One repo** — work in `C:\Users\Tony\mini_basic` only.
2. **Branch for work** — never commit feature work straight to `main` during a fix.
3. **Small commits** — one focus; `git add` only the files you changed. Never `git add -f` agent/status files (they are in `.gitignore`).
4. **Ignore noise** — probes, `__pycache__`, coverage (see `.gitignore`).
5. **Track the package** — almost all of `mini_basic/` must be versioned (mixins, util, tests). Untracked runtime = broken history.

## 5-minute fix workflow

```powershell
cd C:\Users\Tony\mini_basic
git checkout main
git pull 2>$null   # if remote configured

git checkout -b fix/short-description

# work… then:
python -m pytest -q -m "phase1 and not slow" --timeout=45

git status -sb
git add mini_basic/ test/test_relevant.py
# also stage docs/ if this job touched them
git status   # review: no _probe_*, no .coverage, no world_debug*
git commit -m "fix: short description

- What changed
- Tests: pytest -m phase1 …"
```

After user approval of a whole program/feature:

```powershell
git checkout main
git merge --no-ff fix/short-description -m "merge: fix/short-description"
git branch -d fix/short-description
```

## What to commit vs ignore

| Commit | Ignore |
|--------|--------|
| `mini_basic/**/*.py` (package) | `test/_probe_*.py`, `test/_debug_*.py` |
| Focused `test/test_*.py` | `.coverage`, `test/logs/`, `__pycache__` |
| Focused docs under `docs/` | `.resource_*.json`, `RESOURCE_CHECK.txt` |
| Small examples under `examples/` (demos) | Huge game asset trees |
| `pytest.ini`, `.gitignore` | Generated `dist/` text parts unless shipping |

## MINIBASIC_DIR vs git

- **`MINIBASIC_DIR`** = where launchers/install point (`C:\Users\Tony\mini_basic`).
- **Git toplevel** = `C:\Users\Tony\mini_basic`.
- `python -m mini_basic --version` shows both package path and `MINIBASIC_DIR`.

## Rescue: “I can’t find my changes”

```powershell
cd C:\Users\Tony\mini_basic
git status
git branch -vv
# Untracked package files?
git status -u --short -- mini_basic/
```

## More detail

- `DEVELOPMENT_GIT_USAGE.md` — full guide
- `docs/LLM.md` — language / test notes
