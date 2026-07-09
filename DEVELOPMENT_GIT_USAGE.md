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

## When to Commit

- New documentation (pipeline guides, git usage, feature matrices updates)
- Status file improvements that affect the autonomous pipeline
- Code fixes that pass regression + user approval steps
- New or updated dev_install / builder scripts
- After user final checks are recorded (update USER_APPROVAL, FEATURES_DONE, etc.)

Always reference the `DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md` in commit messages when touching the status/agent system.

This setup allows both local lightweight work and full OneDrive-synced development while keeping documentation (including this git guide and the pipeline guide) in sync across both locations.
