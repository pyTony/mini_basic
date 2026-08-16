# Git Quick Start (mini_basic)

## Where the repo lives

**Project root:** the directory you cloned.

Remote: [https://github.com/pyTony/mini_basic](https://github.com/pyTony/mini_basic)

```powershell
cd path\to\mini_basic
git status
git rev-parse --show-toplevel
```

## Daily rules

1. **One working tree** — edit the clone you will commit from.
2. **Branch for work** — never commit feature work straight to `main` during a fix.
3. **Small commits** — one focus; `git add` only the files you changed. Do not force-add files listed in `.gitignore`.
4. **Ignore noise** — probes, `__pycache__`, coverage (see `.gitignore`).
5. **Track the package** — almost all of `mini_basic/` must be versioned (mixins, util, tests). Untracked runtime = broken history.

## 5-minute fix workflow

```powershell
cd path\to\mini_basic
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
| Focused docs under `docs/` | Coverage dumps, resource JSON |
| Small examples under `examples/` (demos) | Huge game asset trees |
| `pytest.ini`, `.gitignore` | Generated `dist/` text parts unless shipping |

## MINIBASIC_DIR vs git

- **`MINIBASIC_DIR`** = where launchers/install point (usually the clone root).
- **Git toplevel** = the same clone (`git rev-parse --show-toplevel`).
- `python -m mini_basic --version` shows both package path and `MINIBASIC_DIR`.

## Rescue: “I can’t find my changes”

```powershell
cd path\to\mini_basic
git status
git branch -vv
# Untracked package files?
git status -u --short -- mini_basic/
```

## More detail

- `DEVELOPMENT_GIT_USAGE.md` — full guide
- `docs/LLM.md` — language / test notes
