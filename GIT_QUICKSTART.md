# Git Quick Start: Independent Fixes (mini_basic)

Follow the **exact same agent/LLM process** you already use (`AGENT_POLICY.txt` + `DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md`), but **always on a git branch**.

This replaces the old habit of creating loose `runtime_fixed_*.py` files. Git history becomes your clean version record.

## 5-Minute Workflow

```powershell
# 1. Start here (dev tree)
cd C:\Users\Tony\Programming\mini_basic
git checkout master
git pull 2>$null

# 2. Read the rules (do this every session)
Get-Content AGENT_POLICY.txt -TotalCount 80
Get-Content DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md -TotalCount 30
```

```powershell
# 3. Create a focused branch for ONE thing
git checkout -b fix/rem-clean-handling
# Examples: fix/bare-numbered-lines, fix/goto-unwind, fix/modulo
```

```powershell
# 4. Work the normal way
# - Single focus only
# - Run tests: python test/run_regression.py -v
# - Update status files + call update_project_status()
# - Use verify scripts for agent checks
# - Wait for real user run + approval
```

```powershell
# 5. Commit often
git add mini_basic/runtime.py CURRENT_TASK.txt DEBUG_STEP.txt
git commit -m "fix: clean REM handling for whole-line comments

- Early return for REM-only lines
- Passes regression
- Single focus (see AGENT_POLICY)
- Refs: DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md"
```

```powershell
# 6. After user final approval
git checkout master
git pull
git merge --no-ff fix/rem-clean-handling -m "merge: fix/rem-clean-handling (user approved)"
git tag fix-rem-clean-2026-07-09
git branch -d fix/rem-clean-handling
```

## Golden Rules

- **Never** commit directly to `master` during a fix.
- One branch = one focused TODO item.
- Merge only after user explicitly approves the whole program.
- Use the dev tree (`Programming/mini_basic`) for daily work.
- After important changes, copy key files to the OneDrive source and commit there too.

## Next Steps (Advanced)

See the full instructions and examples in the `docs/git/` subdirectory:

- `docs/git/INDEPENDENT_FIXES.md` — complete process with examples
- `docs/git/BRANCHING.md` — recommended branch naming and merge strategy
- `DEVELOPMENT_GIT_USAGE.md` — full git guide for the project

Start every session by creating a branch. Git will keep the clean history automatically.

For questions on the autonomous process, re-read `DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md`.