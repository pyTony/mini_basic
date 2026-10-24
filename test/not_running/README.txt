Programs that do not run in mini_basic (yet)
============================================

Moved here from examples/ so that everything left under examples/, basics/ and
showcase/ (and on the main branch) runs. Paths below this folder mirror the
old location, e.g. examples/general/sheet.bbc -> test/not_running/examples/general/sheet.bbc.

Reasons seen when they were moved:
  - LIBRARY file not found (BBCSDL libraries such as stringlib, socklib, dlglib
    are not shipped here)
  - SYS "SDL_..." calls (out of scope)
  - parse/runtime errors in unusual BBCSDL syntax (DEF FN headers, *commands
    after THEN, ON CLOSE, ...)
  - files with a UTF-8 BOM (soccerball_clean.bas, soccerball_fast.bas)

When one starts to work, move it back to its old folder.
Check which programs run: python scripts/check_examples.py
