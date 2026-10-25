# Source editor and Listener

These instructions describe the current `dev` branch, including merged PRs
#142, #144 and #145. The tkinter editor is a checkout tool, not part of the pip
wheel. `EDIT NEW` also exists on `main`; the Listener and PRETTY changes described
here are on `dev`.

## Open and run a program

From a `dev` checkout with Python and tkinter available:

```powershell
python tools/editor.py
python tools/editor.py showcase/mandelbrot_archimedes_mode9.bas
```

Use **Open** (Ctrl+O), **Save** (Ctrl+S), or **Save As** for source files.
Opening a `.bbc` file automatically decodes tokenized BBC source through the
interpreter, including files named on the editor command line. The decoded
buffer is untitled: use **Save As** with `.bas` to keep editable text. `.bbc` is
reserved for tokenized programs; editor saves and the BASIC `SAVE` command
refuse text output to that extension.
Choose the dialect in the toolbar; BBC keywords must be uppercase, while mini
accepts keywords in either case and keeps identifiers case-sensitive.

**▶ Run…** opens a launcher dialog, lispy_machine-style: two icon buttons choose
how to run the saved buffer.

- **Python mini_basic** starts the whole program in a separate interpreter
  process, the same as running it from a shell. Console output uses its
  terminal; pygame graphics use their own window. The dialog's **Use pygame
  display** checkbox requests that display, and **Wait for Esc at end of run**
  (off by default) passes `--hold`/`--no-hold`, controlling the final pygame
  window wait for Escape/close; it does not interrupt a running loop.
- **Real BBC BASIC for SDL** runs the saved buffer with the real BBCSDL
  executable in its own window, instead of this project's Python interpreter.
  One-time setup: open `tools/bbcsdl-basrun.bas` in BBCSDL and save it in
  native, tokenised format as `basrun.bbc` (Richard Russell's text loader,
  CC BY-SA 4.0; renaming the extension alone is not enough). Then, in the Run
  dialog, Browse to the BBCSDL executable and that saved helper; both paths
  are remembered across editor runs (`~/.mini_basic_editor.json`). BBCSDL
  tokenises the buffer itself; this editor never reimplements that.

## Try statements in the Listener

The resizable lower pane holds a persistent immediate-mode interpreter, separate
from the whole-program Run process. Type `PRINT 6*7` in its input field and press
Enter to see `42`. Variables and definitions persist between evaluations.

| Action | Shortcut | Behavior |
|--------|----------|----------|
| Eval Line | F5 | Evaluate the source line at the cursor; a leading line number is removed |
| Eval Selection | Shift+F5 | Evaluate selected source lines |
| Focus Listener input | Ctrl+L | Move focus to the input field |
| Previous/next input | Up/Down in input | Browse Listener command history |
| Reset | Listener Reset button | Start a fresh interpreter and clear output |

F5 evaluates a line; use **▶ Run…** to execute the whole program. Changing the dialect
selector does not rebuild an existing Listener session: use **Reset** to apply it.

To define a procedure, select the complete block and press Shift+F5:

```basic
DEF PROCgreet(name$)
PRINT "Hello "; name$
ENDPROC
```

Then enter `PROCgreet("Tony")` in the Listener. Select a complete multiline
`DEF FN` block through `END DEF` in the same way. Ordinary multiline selections
execute one line at a time; they do not load the entire buffer as a program.
`AUTO` and bare `EDIT` require a terminal prompt loop and are blocked here.
Type statements directly or select complete definitions instead.

## Format source and comments

**Pretty (no numbers)** uses the interpreter's PRETTY formatter; **Renumber**
assigns line numbers and updates jump targets through the interpreter.

In mini, `LIST PRETTY` and `SAVE PRETTY "out.bas"` convert `REM` comments to
apostrophe comments. For example, `REM PROC and FN notes` becomes
`' PROC and FN notes`; the comment words remain intact. Plain LIST/SAVE and
SAVE NUMBERED retain REM. BBC and MITS PRETTY output retain REM for portability.

## Start a fresh program with EDIT NEW

At the terminal REPL, `EDIT` opens the current program in the configured external
editor, while `EDIT NEW` opens an empty buffer without first clearing the current
program. Closing an unchanged blank buffer leaves the program intact. Saving
changed source back applies it to the interpreter and offers the usual save
prompt. This command uses the configured external editor, which may differ from
`tools/editor.py`; it is not the Listener Reset action.

## Verification and remaining checks

Feature regressions are in `test/test_editor_smoke.py` and
`test/test_mini_basic.py`; comment formatting coverage also lives in
`test/test_save_case.py` and `test/test_list_glue_proc.py`.
Tk-dependent tests skip when Tk cannot initialize. Automated checks do not replace
checking keyboard focus, window layout and pygame window lifetime on a desktop.

```powershell
python -m pytest test/test_editor_smoke.py test/test_save_case.py test/test_list_glue_proc.py test/test_mini_basic.py -q -p no:cacheprovider
```

Documentation refresh validation: 456 targeted tests and 19 subtests passed on
2026-10-20, including the editor smoke tests (no Tk skips in that run).
