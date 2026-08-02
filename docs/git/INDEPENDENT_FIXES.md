# Independent Fixes with Git

This is the advanced guide for performing independent fixes while following the project's autonomous agent/LLM process.

It builds on:
- `AGENT_POLICY.txt` (single focus rule, resource awareness, user approval gate)
- `DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md` (full workflow)
- `GIT_QUICKSTART.md` (5-minute version)

## Why This Process?

Previous development created many loose backup files (`runtime_fixed_*.py`, `runtime_final_*.py`, `runtime_problem_*.py` etc.). This led to noisy history that was difficult to analyze later (see `RUNTIME_VERSION_HISTORY.md`).

**Solution**: Every independent fix happens on its own git branch. The git log becomes the authoritative, queryable record.

## Prerequisites

Before starting any fix session:

1. Be in the **git tree** (OneDrive via junction):
   ```powershell
   cd C:\Users\Tony\mini_basic
   git rev-parse --show-toplevel   # OneDrive path
   # C:\Users\Tony\Programming\mini_basic is often an install copy — not the git home
   ```
2. Read the policy documents (every session):
   ```powershell
   Get-Content AGENT_POLICY.txt -TotalCount 80
   Get-Content DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md -TotalCount 50
   ```
3. Ensure you are on a clean `master` (or create a branch from it):
   ```powershell
   git checkout master
   git status
   ```

## Step-by-Step: Starting an Independent Fix

### 1. Create a Focused Branch

Use a descriptive name that matches the current TODO item.

```powershell
# Good examples
git checkout -b fix/rem-clean-handling
git checkout -b fix/bare-numbered-lines
git checkout -b fix/goto-unwind-control
git checkout -b fix/modulo-vs-suffix

# Bad: too vague
git checkout -b fix-stuff
```

**Rule**: One branch = one focused item from `CURRENT_TASK.txt` or a `-- ` line in `FEATURES_DONE.txt`.

### 2. Do the Work (Same Process as Before)

- Strictly follow **Single Focus Rule** — do not touch another program until the current one has user final approval.
- Run tests only for the current focus (`run_regression.py`, specific `verify_*.py`, etc.).
- Before heavy work: `python scripts/verify_resources.py`
- After meaningful changes:
  - Update status files
  - Run `update_project_status()`
- Use `verify_program.py` for agent-only checks.
- User must run the real program via `run_program.py` and confirm before marking `[x]`.

### 3. Commit Frequently and Clearly

Prefer explicit staging over broad `git add .` (especially with large `test/` and `examples/` directories).

```powershell
git add mini_basic/runtime.py
git add CURRENT_TASK.txt DEBUG_STEP.txt FEATURES_DONE.txt
git commit -m "fix: clean REM handling for whole-line comments and colon statements

- Adopt early return [] for pure REM lines (pattern from July 6 final_clean_rem)
- Improve _split_colon_statements and _is_rem_only_statement
- Regression + targeted REM tests pass
- Single focus only (see AGENT_POLICY)
- Refs: DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md"
```

**Commit message guidelines**:
- Start with `fix:`, `docs:`, or `chore:`
- Mention the single focus
- Reference the pipeline guide
- Keep the first line under 72 characters

### 4. When the Fix Is Ready for User Approval

```powershell
# Optional: push for visibility
git push -u origin fix/rem-clean-handling

# Update agent results so status.html shows it is ready
python -c "
from utils.user_approval import write_agent_results
write_agent_results(['OK rem-clean-handling :: all snippet checks passed'])
"
```

Tell the user:
- The branch name
- The exact command: `python run_program.py <program>`
- Ask them to confirm in chat when done

### 5. Merge After User Final Approval

```powershell
git checkout master
git pull origin master 2>$null

git merge --no-ff fix/rem-clean-handling -m "merge: fix/rem-clean-handling (user approved)"

# Create a tag for easy historical reference
git tag fix-rem-clean-handling-2026-07-09

git branch -d fix/rem-clean-handling
git push origin master --tags
```

Using `--no-ff` keeps the branch history visible in the log.

## Advanced Topics

### OneDrive junction (single tree)

- Work in `C:\Users\Tony\mini_basic` (junction → OneDrive). **One git repo only.**
- `Programming\mini_basic` may be an install snapshot without `.git` — do not treat it as a second history to “port” into.
- Details: `DEVELOPMENT_GIT_USAGE.md` §1.

### Large Directories & .gitignore

Large directories (`test/`, `examples/`, `scripts/`) are noisy. Prefer explicit paths:

```powershell
git add mini_basic/ test/test_rgb_dirty_coords.py pytest.ini
```

Probes (`test/_probe_*.py`), coverage, and resource JSON are ignored (see root `.gitignore`).

### Using Git with Text Archives & dev_install

- Do **not** commit generated `*_text_part*.txt` files unless they are canonical distribution artifacts.
- After improving `tools/create_text_archive.py` or `dev_install.ps1`, commit the tools.
- The git history travels with the source when people use the dev install.

### Reconstructing History

Instead of grepping dozens of old `runtime_*.py` files:

```powershell
git log --oneline -- mini_basic/runtime.py
git log --since="2026-07-01" --grep="rem" -- mini_basic/runtime.py
git show <commit>:mini_basic/runtime.py | grep -A 5 "_is_rem_only"
```

You can also generate updated `RUNTIME_VERSION_HISTORY.md` from git in the future.

### Tagging Important States

```powershell
git tag before-rem-clean
# ... do the fix ...
git tag after-rem-clean
```

Tags make it easy to compare states or create release snapshots.

## LLM / Agent Session Checklist

At the very start of every autonomous session:

```powershell
git branch --show-current
if ((git branch --show-current) -eq 'master') {
    $focus = (Get-Content CURRENT_TASK.txt | Where {$_ -notmatch '^#'} | Select -First 1).Trim() -replace '\s+', '-'
    git checkout -b "fix/$focus"
}
```

Never work directly on `master`. Never start a new focus until the current branch has been merged after user approval.

## Common Mistakes to Avoid

- Committing directly to `master` during a fix.
- Creating a new branch for every tiny change (one focused branch per TODO item).
- Forgetting to update status files as part of the commit.
- Merging before user has explicitly approved the whole program.
- Leaving old loose `runtime_fixed_*.py` files around — delete or ignore them; git is the record now.

## Related Documents

- `GIT_QUICKSTART.md` (root) — 5-minute version
- `DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md` — full autonomous process
- `AGENT_POLICY.txt` — core rules (must read every session)
- `RUNTIME_VERSION_HISTORY.md` — example of clean history (generated from git)
- `DEVELOPMENT_GIT_USAGE.md` — broader git usage for the project

Use git branches. Keep the focus single. Let git keep the record.