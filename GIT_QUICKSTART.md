# Git Quick Start (mini_basic)

## Where the repo lives

| Path | What it is |
|------|------------|
| `C:\Users\Tony\mini_basic` | **Junction** → OneDrive tree |
| `D:\1\OneDrive - FFWPU-Fin\mini_basic` | **Real folder + `.git`** (source of truth) |

They are the **same working tree**. Edit either path; one `git status`, one history.

```powershell
cd C:\Users\Tony\mini_basic   # or the OneDrive path — same repo
git status
git rev-parse --show-toplevel   # shows OneDrive path
```

`C:\Users\Tony\Programming\mini_basic` may be a **separate install copy** (not necessarily a git repo). Do **not** treat it as a second source of truth unless you intentionally put a clone there.

## Daily rules

1. **One repo** — the OneDrive junction tree only.
2. **Branch for work** — never commit feature work straight to `master` during a fix.
3. **Small commits** — one focus (AGENT_POLICY); prefer explicit `git add paths`.
4. **Ignore noise** — probes, `__pycache__`, coverage, OneDrive junk (see `.gitignore`).
5. **Track the package** — almost all of `mini_basic/` must be versioned (mixins, util, tests). Untracked runtime = broken history.

## 5-minute fix workflow

```powershell
cd C:\Users\Tony\mini_basic
git checkout master
git pull 2>$null   # if remote configured

git checkout -b fix/short-description

# work… then:
python -m pytest -q -m "phase1 and not slow" --timeout=45

git add mini_basic/ test/test_relevant.py FEATURES_DONE.txt CURRENT_TASK.txt
git status   # review: no _probe_*, no .coverage, no huge PDFs unless intended
git commit -m "fix: short description

- What changed
- Tests: pytest -m phase1 …"
```

After user approval of a whole program/feature:

```powershell
git checkout master
git merge --no-ff fix/short-description -m "merge: fix/short-description"
git branch -d fix/short-description
```

## What to commit vs ignore

| Commit | Ignore |
|--------|--------|
| `mini_basic/**/*.py` (package) | `test/_probe_*.py`, `test/_debug_*.py` |
| Focused `test/test_*.py` | `.coverage`, `test/logs/`, `__pycache__` |
| `FEATURES_DONE.txt`, `CURRENT_TASK.txt`, policy docs | `.resource_*.json`, `RESOURCE_CHECK.txt` |
| Small examples under `examples/` (demos) | Huge game asset trees if thrashing OneDrive |
| `pytest.ini`, `.gitignore` | Generated `dist/` text parts unless shipping |

## MINIBASIC_DIR vs git

- **`MINIBASIC_DIR`** = where launchers/install point (may be `C:\Users\Tony\mini_basic`).
- **Git toplevel** = always the OneDrive path (junction target).
- `python -m mini_basic --version` shows both package path and `MINIBASIC_DIR`.

## Rescue: “I can’t find my changes”

```powershell
cd C:\Users\Tony\mini_basic
(Get-Item .).Target          # should show OneDrive path
git status
git branch -vv
# Untracked package files?
git status -u --short -- mini_basic/
```

## More detail

- `DEVELOPMENT_GIT_USAGE.md` — full guide (updated for junction layout)
- `docs/git/INDEPENDENT_FIXES.md` — branch naming / agent checklist
- `AGENT_POLICY.txt` — single focus, status BEGIN/END
