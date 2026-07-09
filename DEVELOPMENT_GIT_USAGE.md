# Git Usage for mini_basic Development

This document explains how to use git in the mini_basic development workflow, especially in the context of the local dev tree vs. the OneDrive-synced full source.

## Repository Setup

There are typically two related git repositories:

1. **Full OneDrive Source** (`C:\Users\Tony\mini_basic`)
   - This is the rich, complete development tree (with full history, all examples, test corpus, scripts, status files, etc.).
   - Often synced via OneDrive.
   - Contains the "source of truth" for the full project.
   - Git is initialized here for tracking all changes.

2. **Local Dev Tree** (`C:\Users\Tony\Programming\mini_basic`)
   - This is a "local install" or working copy of the mini_tree.
   - Used for focused development work, LLM/agent sessions, and lighter experimentation.
   - May have its own `.git` for local commits (as seen in initial setup: `0491d6d feat: initial clean project`).
   - Changes made here (e.g., during agent work, new docs) should be mirrored back to the OneDrive source.

The `dev_install.ps1` + text parts mechanism allows reproducing either a minimal end-user tree or a full dev tree (including extras like `examples/`, `test/`, `scripts/`, `lib/`, `utils/`, and all status/pipeline docs).

## Key Git Workflows

### 1. Basic Commit Workflow (in Dev Tree)

```powershell
cd C:\Users\Tony\Programming\mini_basic

# See what has changed (new docs, status updates, code fixes)
git status

# Stage specific changes (recommended over `git add .` to avoid noise from large dirs like test/ or examples/)
git add DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md
git add DEVELOPMENT_GIT_USAGE.md
git add CURRENT_TASK.txt USER_APPROVAL.txt FEATURES_DONE.txt
git add dev_install.ps1   # if you copied it here or are tracking it
# For code changes:
git add mini_basic/runtime.py mini_basic/expr/patterns.py

# Commit with clear message
git commit -m "docs: add DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md and DEVELOPMENT_GIT_USAGE.md

- Document status implementation and autonomous TODO pipeline
- Document git usage for local dev vs OneDrive source
- Update pending user checks in CURRENT_TASK and USER_APPROVAL
- Include dev_install.ps1 and generated dev text part for reproducible dev setup"

# Push if remote exists
git push
```

### 2. Syncing New Files to OneDrive Source

Newly produced files (guides, install scripts, text archives) created in the local dev tree must be copied to the OneDrive source:

```powershell
# From dev tree to OneDrive source
Copy-Item Programming\mini_basic\DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md C:\Users\Tony\mini_basic\ -Force
Copy-Item Programming\dev_install.ps1 C:\Users\Tony\mini_basic\ -Force
Copy-Item Programming\mini_basic_dev_text_part01.txt C:\Users\Tony\mini_basic\ -Force

# Then in the OneDrive source repo:
cd C:\Users\Tony\mini_basic
git add DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md dev_install.ps1 mini_basic_dev_text_part01.txt
git commit -m "docs: add pipeline guide and git usage doc to OneDrive source"
git push
```

This ensures the full source (used for text archive generation, full corpus work, etc.) always has the latest docs.

### 3. Working with Large Directories

- `test/`, `examples/`, `scripts/`, `lib/` can be very large.
- Use `.gitignore` (already present from initial setup) to avoid committing generated files (`.coverage`, `__pycache__`, logs, etc.).
- For commits, prefer explicit paths: `git add test/run_regression.py` instead of broad adds.
- When using dev_install or text archives, the large dirs are reconstructed from text parts rather than stored in git (or selectively).

### 4. Using Git with the Text Archive / Install System

- The end-user and dev installs use `tools/create_text_archive.py` and `tools/reconstruct_from_text.py` (or the pure-PS equivalent in `install.ps1` / `dev_install.ps1`).
- These produce/consume the `*_text_part*.txt` files.
- Do **not** commit the generated text parts to git unless they are the canonical distribution artifacts.
- After generating new dev text parts (e.g. for the pipeline docs), commit the generator changes + the part if appropriate.
- Example:
  ```powershell
  python tools/create_text_archive.py --outdir dist   # for minimal
  # Manually or via script generate dev_text parts for extras
  git add tools/create_text_archive.py
  git commit -m "build: improve text archive for dev docs"
  ```

### 5. Branching and Collaboration

- Use feature branches for major work:
  ```powershell
  git checkout -b feature/bbcsdl-parity-extension
  # work...
  git commit ...
  git push -u origin feature/bbcsdl-parity-extension
  ```
- For agent/LLM sessions: keep commits small and focused on one TODO item (aligns with Single Focus Rule in AGENT_POLICY).
- Merge to main after user final approval for whole programs (see pipeline guide).

### 6. Handling the Two Trees

- **Rule of thumb**: Do primary development in `Programming/mini_basic`.
- After significant progress (new docs, status pipeline improvements, code fixes), copy key files to `mini_basic` and commit there too.
- The OneDrive source is used when you need the full corpus, real BBCSDL comparison, or to regenerate text parts for distribution.
- Keep `.gitignore` in sync between the two if they diverge.

### 7. Useful Commands

```powershell
# See untracked new docs/status files
git status --porcelain | Select-String "?? .*txt|?? .*md"

# Diff only the pipeline docs
git diff DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md DEVELOPMENT_GIT_USAGE.md

# Amend last commit (if you forgot a file)
git add DEVELOPMENT_GIT_USAGE.md
git commit --amend --no-edit

# View history of the pipeline doc
git log --oneline -- DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md
```

## Recommended .gitignore Entries (ensure present)

```
# Generated / temp
__pycache__/
*.pyc
.coverage
*.log
*.json   # resource peaks, etc. (selective)
dist/
archives/
mini_basic_text_part*.txt   # or keep if you want them versioned
dev_text_part*.txt

# OneDrive / Windows noise
*.tmp
Thumbs.db
```

## Independent Fixes with Git (Following the Same Agent/LLM Process)

In the past, fixes were often done by creating loose files like `runtime_fixed_xxx.py`, `runtime_final_yyy.py`, or `runtime_problem_zzz.py`. This created noisy back-and-forth history that was hard to follow (as seen in the runtime backup analysis).

**Going forward, always use git branches for independent fixes.** This keeps a clean, queryable record in `git log`, replaces the old loose-file habit, and works perfectly with the existing autonomous process in `AGENT_POLICY.txt` and `DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md`.

### Recommended Workflow for an Independent Fix

1. **Start fresh and read the rules** (mandatory at the beginning of every session):
   ```powershell
   cd C:\Users\Tony\Programming\mini_basic
   git checkout master
   git pull origin master 2>$null   # if remote exists
   git status

   # Read the operating rules
   Get-Content AGENT_POLICY.txt -TotalCount 80
   Get-Content DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md -TotalCount 50
   ```

2. **Identify the single focus** (from `CURRENT_TASK.txt`, `FEATURES_DONE.txt` lines starting with `--`, or `CORPUS_AUDIT.txt`).

3. **Create a focused branch** (use a short, descriptive name):
   ```powershell
   git checkout -b fix/rem-clean-handling
   # or
   git checkout -b fix/bare-numbered-lines
   # or
   git checkout -b fix/goto-unwind
   ```

4. **Do the work following the exact same process**:
   - Single focus only (never touch another program until this one is user-approved).
   - Run targeted tests: `python test/run_regression.py -v`, `test/verify_*.py`, etc.
   - Before heavy work: `python scripts/verify_resources.py`
   - After meaningful progress: update status files and call `update_project_status()`
   - Record work: update `CURRENT_TASK.txt`, `DEBUG_STEP.txt`, `WORK_LOG.txt`, `FEATURES_DONE.txt` as appropriate.
   - For programs: use `verify_program.py` (agent-only) then wait for user to run via `run_program.py` and confirm.

5. **Commit frequently with clear messages** (aligns with pipeline):
   ```powershell
   git add mini_basic/runtime.py
   git add CURRENT_TASK.txt DEBUG_STEP.txt FEATURES_DONE.txt
   git commit -m "fix: clean REM handling for whole-line comments and colon statements

   - Adopt explicit early return for REM-only lines (from July 6 final_clean_rem)
   - Update _split_colon_statements and _is_rem_only_statement
   - Passes regression and targeted REM tests
   - Single focus: rem-clean-handling (see AGENT_POLICY)
   - Refs: DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md"
   ```

6. **When the fix is ready for user final check**:
   - Push the branch if you have a remote (for visibility):
     ```powershell
     git push -u origin fix/rem-clean-handling
     ```
   - Update `USER_APPROVAL_AGENT.txt` (via the helper scripts).
   - Tell the user the branch name and the exact command to test (`python run_program.py ...`).

7. **After user final approval**:
   - Merge cleanly to master:
     ```powershell
     git checkout master
     git pull
     git merge --no-ff fix/rem-clean-handling -m "merge: fix/rem-clean-handling (user approved)"
     git tag fix-rem-clean-handling-2026-07-09   # optional but recommended for history
     git branch -d fix/rem-clean-handling
     git push origin master --tags
     ```
   - Delete the local branch.
   - Update `RUNTIME_VERSION_HISTORY.md` (or let it be derived from `git log` in future).

### Benefits of This Process

- Git history **becomes** the version record (no more loose `runtime_fixed_*.py` files).
- Easy to see what was changed for each focused fix (`git log --oneline --graph`).
- Bisecting and reverting become possible.
- Multiple independent fixes can be worked on in parallel (different branches) without polluting master.
- Fully compatible with the existing single-focus rule, status heartbeat, and user-approval gate.
- The `RUNTIME_VERSION_HISTORY.md` can be kept as a human-readable summary, but the real source of truth is `git log`.

### For LLM / Agent Sessions (Autonomous Mode)

At the very start of every session:
```powershell
git branch --show-current
if ((git branch --show-current) -eq "master") {
    $focus = (Get-Content CURRENT_TASK.txt | Select-String -NotMatch '^#').Trim() -replace '\s+', '-'
    git checkout -b "fix/$focus"
}
```

Never commit directly to master during a fix session. Only merge after user approval.

### Future Record Keeping

- Use `git log --since="2026-07-01" -- mini_basic/runtime.py` instead of grepping dozens of backup files.
- Tag important states: `git tag before-rem-fix`, `git tag after-bare-numbers`.
- The July 6 "fix sprint" style work should now live as a short-lived branch with multiple small commits.
- When generating text archives or dev installs, the git history travels with the code.

This process replaces the old loose-file backup habit while preserving (and improving) the autonomous agent workflow.

## When to Commit

- New documentation (pipeline guides, git usage, feature matrices updates)
- Status file improvements that affect the autonomous pipeline
- Code fixes that pass regression + user approval steps
- New or updated dev_install / builder scripts
- After user final checks are recorded (update USER_APPROVAL, FEATURES_DONE, etc.)

Always reference the `DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md` in commit messages when touching the status/agent system.

This setup allows both local lightweight work and full OneDrive-synced development while keeping documentation (including this git guide and the pipeline guide) in sync across both locations.
