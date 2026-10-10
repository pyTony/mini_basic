# Clean start — 2026-08-09

**Branch tip at clean start:** `cf06f59` (full: `cf06f59e3b9b1eaf3733ee3fd7dbf337c4243d4e`)
**Branch:** `wip/snapshot-20260805`

Working tree was **clean** (no pending product diffs). From this point:

## Going forward

1. **One focus branch per job:** `git checkout -b fix/<short-name>` from a clean tip.
2. **Stage explicit paths** — not probes, not `*.prof`, not `world_debug*`.
3. **Do not delete** packaging/docs (`LICENSE`, `MANIFEST.in`, `docs/PACKAGING.md`, manuals) without user request.

## What this baseline includes (high level)

- Modular `mini_basic` package + tests + corpus menus
- 1.00 language / packaging docs
- Tree hygiene (`.gitignore` debug dumps)

## Tag

`git tag clean-start-2026-08-09` → points at this commit.

After user approves a whole feature stack, merge focus branches to `master` per GIT_QUICKSTART.
