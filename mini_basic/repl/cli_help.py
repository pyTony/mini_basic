"""CLI usage text shared by ``--help`` / ``-h`` and REPL ``HELP CLI``."""
from __future__ import annotations

from typing import List


def cli_help_lines() -> List[str]:
    """Return the full command-line help (same body as ``mini_basic --help``)."""
    return [
        'Usage: mini_basic [options] [file | -c cmd ...] [program args...]',
        '',
        '  file.bas   load and RUN the program',
        '  file.mbs   run REPL commands (LOAD, RUN, ...)',
        '  file.txt   program or session script (sniffed; numbered+RUN → session)',
        '  -c CMD     run REPL session text (like python -c); may repeat -c',
        '  --command  same as -c',
        '  -          read REPL commands from stdin',
        '  (stdin)    if not a TTY, same as -: piped session script',
        '',
        'Session input (prefer file/pipe in PowerShell — quoting is hard):',
        '  mini_basic INPUT.TXT',
        '  Get-Content INPUT.TXT | python -m mini_basic -q',
        '  cmd /c "python -m mini_basic -q < INPUT.TXT"',
        '  python -m mini_basic -q -c "PRINT 1+2" -c Q',
        '  python -m mini_basic -q -c "10 A=1" -c "20 PRINT A" -c RUN -c Q',
        '',
        '  -V, --version  version, implementation status, MINIBASIC_DIR',
        '  -p, --pretty   with a .bas file: LIST PRETTY and exit; without: REPL',
        '  --list         with a .bas file: LIST and exit; without: REPL',
        '  --refs         with a .bas file: LIST REFS and exit; without: REPL',
        '  -i, --interactive  stay in REPL after RUN, -c, session file, or list modes',
        '                 (without -i: run the file/session then exit — no > prompt)',
        '  -q         suppress startup banner and load messages',
        '  -d, --dialect mini|mits|commodore|tiny|bbc',
        '             mini = full superset (default)',
        '             mits = numbered/GOTO era (ELIZA.BAS)',
        '             commodore = C64/VIC-20 MS BASIC V2 (IF GOTO, numbered)',
        '             tiny = Tiny BASIC 1975 (IF THEN stmt only, numbered)',
        '             bbc  = BBC-style structured (BETH.BAS); GOTO allowed',
        '  File hint: #!bbc  or  1 REM dialect: bbc  (unless --dialect set)',
        '  --strict-dialect  treat dialect violations as load errors',
        '  --input-exit      mini dialect only: bye/quit/exit at INPUT ends RUN',
        '  --pygame          SDL/pygame window (same as --display pygame)',
        '  --display pygame|terminal|none',
        '                    bbc/mini: graphics programs auto-enable pygame when a GUI is available',
        '                    (text-only Linux/SSH without DISPLAY: stay terminal; use --display pygame to force)',
        '  --fps N           cap pygame frame rate (0 = unlimited; default 60)',
        '  --scale N         pixel scale for pygame (exact; default: largest that fits)',
        '  --cols N --rows N text grid size for pygame',
        '  --gfx-width N --gfx-height N graphics framebuffer size',
        '  --hold / --no-hold keep or close pygame window after END',
        '  --slow [ms]         pause after each BASIC line (default 50 ms); shows graphics frames',
        '  --tee-terminal      mirror pygame PRINT/INPUT to the terminal',
        '                      (or set _tee_terminal = 1 in the program)',
        '  --debug             interpreter debug to stderr + mini_basic.log',
        '  --debug-filter TAG  only lines containing TAG (HELP DEBUG lists tags)',
        '',
        'Environment: MINIBASIC_DIR=path   install/launcher tree (see --version)',
        '             MINI_BASIC_DIALECT=mini|mits|commodore|tiny|bbc',
        '             MINIBASIC_SLOW=ms    same as --slow (milliseconds per line)',
        '             MINIBASIC_NO_GRAPHICS=1 or MINIBASIC_DISPLAY=terminal',
        '             MINI_BASIC_DEBUG=1 / MINI_BASIC_DEBUG_FILTER=TAG',
        '             (never auto-open pygame; Ctrl+C / ESC in the terminal stops RUN)',
        '',
        'Program args are available as _argc, ARG$(n), and ARG(n).',
        '',
        'Examples:',
        '  mini_basic --dialect mits ELIZA.BAS',
        '  mini_basic --dialect bbc BETH.BAS',
        '  mini_basic --pygame examples/mini/sprites_demo.bas',
        '  mini_basic --display pygame --scale 2 examples/mini/bbc_graphics_demo.bas',
        '  mini_basic --pretty --dialect bbc BETH.BAS',
        '  mini_basic --pretty -i BETH.BAS',
        '  mini_basic mandelbrot_color_only.bas 32',
        '  mini_basic beth.mbs',
        '  mini_basic INPUT.TXT',
        '  mini_basic -c "PRINT 2+2" -c Q',
        '  mini_basic -i                  enter > prompt (no file)',
        '  mini_basic file.bas -i         RUN then stay in REPL',
        '',
        'REPL: bye/quit/exit at > prompt. INPUT is standard unless --input-exit.',
        'In-session: HELP CLI  (this text)   HELP INDEX   HELP PROGRAM   HELP DEBUG',
    ]


def print_cli_help() -> None:
    """Print full CLI help (used by ``--help`` and ``HELP CLI``)."""
    for line in cli_help_lines():
        print(line)


__all__ = ['cli_help_lines', 'print_cli_help']
