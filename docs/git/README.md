# Git Documentation

This subdirectory contains advanced Git documentation for the mini_basic project.

## Files

- `INDEPENDENT_FIXES.md` — Full guide for performing independent fixes using git branches while following the agent/LLM process (single focus, status updates, user approval gate).
- See also the root-level `GIT_QUICKSTART.md` for a 5-minute overview.

## Related Root Documents

- `GIT_QUICKSTART.md`
- `DEVELOPMENT_GIT_USAGE.md`
- `DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md`
- `AGENT_POLICY.txt`
- `RUNTIME_VERSION_HISTORY.md`

## Philosophy

Use git branches + frequent, well-described commits instead of loose backup files. This keeps a clean, queryable history that replaces the old `runtime_fixed_*.py` / `runtime_final_*.py` pattern.