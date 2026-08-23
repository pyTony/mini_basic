"""Structured HELP topics for the interactive REPL (HELP INDEX, HELP FUNCTIONS, ...)."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from mini_basic.bbc_modes import BB4W_MODE_SPECS, BBCModeSpec, BBC_MODE_SPECS, bbc_os_scales
from mini_basic.repl.cli_help import print_cli_help

HELP_MENU_ITEMS: List[Tuple[str, str]] = [
    ('OVERVIEW', 'quick tour of the interpreter'),
    ('CLI', 'full command-line --help (flags, session files, -i)'),
    ('FUNCTIONS', 'numeric/math builtins (SIN, RND, CVI, ...)'),
    ('STRINGS', 'string functions (MID$, STR$, MKI$, colours, ...)'),
    ('OPERATORS', 'comparisons, logic, arithmetic'),
    ('STATEMENTS', 'IF, loops, PROC, ON ERROR, DEF FN, ...'),
    ('FILES', 'channels, PRINT#, random files, OPENIN/OUT'),
    ('GRAPHICS', 'MODE, VDU, GCOL, PLOT, sprites, pygame'),
    ('MODES', 'BBC 0-7 and SDL 8-31 — resolution and implementation status'),
    ('REPL', 'LIST, RUN, LOAD, EDIT, abbreviations, Tab completion'),
    ('PROGRAM', 'LOAD / SAVE / LIST / AUTO / EDIT — program file commands'),
    ('SYSTEM', '_argc, _optimization_level, TIME, ERR, ERL'),
    ('DEBUG', '--debug / --debug-filter tags (IF, DIM, VDU, …)'),
    ('DIALECTS', 'mits / commodore / tiny / bbc / mini (same as MATRIX)'),
]

_HELP_ALIASES = {
    'INDEX': 'INDEX',
    'TOPICS': 'INDEX',
    'TOPIC': 'INDEX',
    'MENU': 'INDEX',
    'INTERACTIVE': 'INDEX',
    'OVERVIEW': 'OVERVIEW',
    'STARTUP': 'OVERVIEW',
    'ALL': 'OVERVIEW',
    'CLI': 'CLI',
    'USAGE': 'CLI',
    'OPTIONS': 'CLI',
    'OPTION': 'CLI',
    'FLAGS': 'CLI',
    'COMMANDLINE': 'CLI',
    'CMDLINE': 'CLI',
    'ARGS': 'CLI',
    'ARGV': 'CLI',
    'SHELL': 'CLI',
    'FUNCTIONS': 'FUNCTIONS',
    'FUNCTION': 'FUNCTIONS',
    'FUNCS': 'FUNCTIONS',
    'MATH': 'FUNCTIONS',
    'MATHS': 'FUNCTIONS',
    'STRINGS': 'STRINGS',
    'STRING': 'STRINGS',
    'FILES': 'FILES',
    'FILE': 'FILES',
    'IO': 'FILES',
    'REPL': 'REPL',
    'COMMANDS': 'REPL',
    'PROGRAM': 'PROGRAM',
    'PROG': 'PROGRAM',
    'LOAD': 'PROGRAM',
    'SAVE': 'PROGRAM',
    'LIST': 'PROGRAM',
    'AUTO': 'PROGRAM',
    'EDIT': 'PROGRAM',
    'TRACE': 'STATEMENTS',
    'LVAR': 'STATEMENTS',
    'GRAPHICS': 'GRAPHICS',
    'GFX': 'GRAPHICS',
    'DISPLAY': 'GRAPHICS',
    'MODES': 'MODES',
    'MODE': 'MODES',
    'OPERATORS': 'OPERATORS',
    'OPS': 'OPERATORS',
    'STATEMENTS': 'STATEMENTS',
    'STMTS': 'STATEMENTS',
    'SYSTEM': 'SYSTEM',
    'SYS': 'SYSTEM',
    'DEBUG': 'DEBUG',
    'DPRINT': 'DEBUG',
    'FILTER': 'DEBUG',
    'DIALECTS': 'DIALECTS',
    'DIALECT': 'DIALECTS',
    'MATRIX': 'DIALECTS',
    'COMPAT': 'DIALECTS',
}


def _section(title: str, lines: List[str]) -> None:
    print(title)
    for line in lines:
        print(f'  {line}')


def _print_help_index() -> None:
    print('=== HELP INDEX ===')
    print('  HELP              HELP> menu (empty line returns to >)')
    print('  HELP topic        open at topic (e.g. HELP FUNCTIONS)')
    print()
    for index, (name, summary) in enumerate(HELP_MENU_ITEMS, start=1):
        print(f'  {index:2} {name:<12} {summary}')
    print()
    print('  Abbrev: H.=HELP   MA.=MATRIX')


def _print_help_overview() -> None:
    sections = [
        ('=== mini-BASIC overview ===', [
            'Five dialects: mits  commodore  tiny  bbc (BBC SDL 2.0)  mini (default)',
            'HELP INDEX lists topics; HELP FUNCTIONS lists every builtin.',
        ]),
        ('Quick start', [
            'mini_basic file.bas [args]    load and RUN (then exit unless -i)',
            'mini_basic -i                 open > REPL (no file)',
            'mini_basic file.bas -i        RUN then stay at >',
            'mini_basic INPUT.TXT          session script (numbered lines + RUN/Q)',
            'mini_basic --pretty file.bas  LIST structured, exit',
            '--dialect mits|commodore|tiny|bbc|mini   --strict-dialect   --pygame',
            'Program file: #!bbc  or  1 REM dialect: bbc  (prefer numbered REM; not line 0)',
            'Full shell flags: HELP CLI  (same text as mini_basic --help)',
        ]),
        ('At the > prompt', [
            '123 PRINT X          store a program line',
            'PRINT 1+2            immediate statement',
            'RUN  LIST  LOAD  SAVE  NEW  EDIT  MATRIX',
            'HELP CLI             full command-line options (same as --help)',
            'HELP PROGRAM         LOAD/SAVE/LIST/AUTO options',
            'HELP DEBUG           --debug and filter tags',
            'bye / quit / exit    leave REPL',
        ]),
    ]
    for index, (title, lines) in enumerate(sections):
        if index:
            print()
        _section(title, lines)


def _print_help_cli() -> None:
    """Same detailed text as ``mini_basic --help`` / ``-h``."""
    print('=== Command line (same as mini_basic --help) ===')
    print()
    print_cli_help()


def _print_help_functions() -> None:
    _section('=== Numeric / math functions ===', [
        'PI()                 pi (no arguments)',
        'RND                  32-bit random integer (0 to &FFFFFFFF)',
        'RND(1)               real in 0.0 to 0.99999999',
        'RND(n)               integer 1 to n (n>1)',
        'RND(0)               last random, as RND(1)',
        'RND(-n)              seed PRNG from n; returns n',
        '                     BBC has no RANDOMIZE: X=RND(-TIME)',
        'RANDOMIZE [seed]     mini/MS only; same seed as RND(-seed)',
        '',
        'SIN(x)  COS(x)  TAN(x)',
        'ASN(x)  ACS(x)  ATN(x)     aliases: ASIN  ACOS  ATAN',
        'LOG(x)  EXP(x)              natural log and e^x',
        'INT(x)  FIX(x)  CINT(x)     floor / trunc toward 0 / round',
        'CSNG(x)  CDBL(x)            single / double conversion',
        'SQR(x)  SQRT(x)             square root (aliases)',
        'ABS(x)  INT(x)  SGN(x)      floor for INT',
        '',
        'VAL(s$)              string to number',
        'NEAR(x,y [,t])       nearly equal (-1 true, 0 false); optional abs tolerance t',
        'NEARSIG(x,y,n)       match to n significant figures',
        'LEN(s$)              string length (numeric result)',
        'INSTR(hay$, needle$ [, start])   1-based position, 0 if missing',
        '',
        'ARG(n)               n-th program CLI arg as number (mini)',
        'POS                  text cursor column (0-based)',
        'VPOS                 text cursor row (0-based)',
        'POINT(x, y)          graphics pixel colour index',
        '',
        'CVI(s$)  CVS(s$)  CVD(s$)   unpack binary from FIELD buffer',
        'LOC(#n)  LOF(#n)            random/sequential file position/size',
    ])
    print()
    _section('Bitwise operators', [
        'XOR  EOR  EQV  IMP   32-bit integer bitwise ops',
        'DIV                 integer division (like \\\\)',
        'REPORT / REPORT$    last error message text',
        '@dir$  @lib$  @usr$  BBCSDL-style path strings',
        'SWAP a, b           exchange two variables or array elements',
    ])


def _print_help_strings() -> None:
    _section('=== String functions ===', [
        'CHR$(n)              character from ASCII code',
        'ASC(s$)              code of first character',
        'MID$(s$, start [, len])',
        'LEFT$(s$, n)  RIGHT$(s$, n)',
        'UCASE$(s$)  LCASE$(s$)',
        'STR$(n)              number formatted as string',
        'STR$~(n)             BBC hex string (uppercase, no 0x)',
        'HEX$(n [, w])        MS/QB64 hex string; optional zero-pad width',
        'OCT$(n)              MS octal string',
        'BIN$(n [, w])        Locomotive/QB64 binary string; optional pad',
        'STRING$(n [, char])  repeat char n times',
        'SPACE$(n)            n spaces',
        'INKEY$ / INKEY$(n)   key as string; n=0 poll ("" if none); n>0 wait n cs',
        'ARG$(n)              n-th CLI argument string (mini)',
        '',
        'MKI$(n)  MKS$(n)  MKD$(n)   pack int/single/double for FIELD',
        '',
        'OPENIN(path$)        channel for sequential read',
        'OPENOUT(path$)       channel for sequential write',
    ])
    print()
    _section('ANSI colour (mini, terminal only — not the pygame window)', [
        'FG$(n)  BG$(n)         BBC/Agon palette 0-15, or 256-colour index',
        'RGB$(r,g,b)  BGRGB$(r,g,b)   true-colour foreground/background',
        'ANSI$(codes...)  RESET$()',
        'Requires dialect mini. --pygame is ignored for these programs.',
    ])


def _print_help_operators() -> None:
    _section('=== Operators ===', [
        '+  -  *  /  ^  MOD',
        '=  <>  <  >  <=  >=',
        'AND  OR  NOT          TRUE=-1  FALSE=0  (MBASIC style)',
        '? expr                PRINT shorthand',
        'PRINT ~n              BBC hex (same digits as STR$~n)',
    ])


def _print_help_statements() -> None:
    _section('=== Program statements ===', [
        'REM  \'comment',
        'LET v = expr   (LET optional)',
        'DIM A(10)  DIM M(5,5)   OPTION BASE 0|1   ERASE A [, B$]',
        'DEFINT/DEFSNG/DEFDBL/DEFSTR letter ranges',
        '',
        'IF ... THEN ... [ELSE ...] ENDIF',
        'WHILE ... ENDWHILE   REPEAT ... UNTIL   FOR ... NEXT',
        'EXIT FOR|WHILE|REPEAT   BREAK/CONTINUE [label] (mini)',
        '',
        'GOTO line  GOSUB line  RETURN',
        'ON expr GOTO a,b,...   ON expr GOSUB a,b,...',
        'DEF PROCname(...) ... ENDPROC   PROC name',
        'DEF FNname(x)=expr',
        'DEF FNname(x) ... =ret ... END DEF',
        '  In DEF FN, IF needs THEN:  IF n<2 THEN =1 ELSE =n*FNfact(n-1)',
        '  (THEN is not optional when the branch is a =return)',
        'Closers: ENDIF or END IF, ENDWHILE (WEND still runs), ENDPROC or END PROC',
        'DEF FN block ends with END DEF or END FN',
        '',
        'ON ERROR GOTO|GOSUB line   RESUME [0]   RESUME NEXT   ON ERROR OFF',
        'STOP   END   CONT (after STOP)   LIST / PRINT / LVAR while stopped',
        'TRACE ON|OFF        [line] numbers to stderr (also CLI --trace)',
        'TRACE n             only lines numbered below n (BBC)',
        'TRACE PROC          PROC/FN names as they are called',
        'TRACE STEP [n|PROC] wait for a key after each traced line (Esc = STOP)',
        'TRACE TO file       log the path to a file; TRACE CLOSE  back to stderr',
        'LVAR                list variables, arrays, FN/PROC (immediate or program)',
        'DATA ...   READ   RESTORE [line]',
        'RANDOMIZE [seed]   mini/MS; BBC uses X=RND(-TIME)',
        'WAIT n             (n centiseconds)',
        'TIME   TIME=0   TIME=n   TIME=TIME+n   centisecond clock (persists across RUN)',
    ])


def _print_help_files() -> None:
    _section('=== File I/O ===', [
        'OPENIN(path$)  OPENOUT(path$)   sequential via channel number',
        'PRINT#ch, ...   INPUT#ch, vars   WRITE#ch, ...   CLOSE#ch',
        'BPUT#ch, byte   write low 8 bits (BBC); BGET#ch is the read function',
        'LINE INPUT#ch, var$',
        '',
        'OPEN "R", #n, "file" [,reclen]   random access',
        'FIELD #n, w AS var$ [, ...]   GET #n [,rec]   PUT #n [,rec]',
        'LSET field$ = s$   RSET field$ = s$',
        'LOC(#n)  LOF(#n)   MKI$/MKS$/MKD$  CVI/CVS/CVD',
        'KILL "file"          delete a file   ERASE a [, b]   undim arrays',
        'CHAIN "file" [, line] [, ALL]   load and run; ALL keeps variables',
        '',
        'ERR   ERL   error code and line after ON ERROR trap',
        'INPUT reads the line as data (standard BASIC)',
        '--input-exit (CLI)   optional bye/quit/exit at INPUT',
    ])


def _print_help_graphics() -> None:
    _section('=== Graphics (bbc + mini, pygame or terminal) ===', [
        'MODE n               text/graphics mode (see HELP MODES)',
        'VDU codes            CLS, CLG, COLOUR/COLOR, cursor positioning',
        'GCOL f,c   MOVE x,y   DRAW x,y   ORIGIN x,y',
        'PLOT code,x,y        BBC/Agon plot codes (156=circle fill, ...)',
        'SPRITEDEF / SPRITE   hardware-style sprites (pygame)',
        'POINT(x,y)           read pixel colour',
        'OSCLI / *            REFRESH, GSAVE, DISPLAY, ERASE; SYS not implemented',
        '',
        'CLI: --pygame  --display pygame|terminal|none',
        'Text-only (no DISPLAY / MINIBASIC_NO_GRAPHICS=1): no auto pygame window',
        'During RUN: Ctrl+C or ESC in the terminal stops the program',
        '     --scale N  --cols/--rows  --gfx-width/--gfx-height',
        '     --hold / --no-hold',
        '     --slow [ms]   pause after each line (default 50); or _slow=N in program',
    ])


_MODE_STATUS_OVERRIDES: Dict[int, Tuple[str, str]] = {
    7: (
        'partial',
        'alpha/gfx colours, mosaics, flash/hold/separated/bg; '
        'double-height/conceal/full SAA5050 still open',
    ),
}

_MODE_COLOURS: Dict[int, str] = {
    0: '2',
    1: '4',
    2: '8',
    3: '16 (text)',
    4: '2',
    5: '4',
    6: '16 (text)',
    7: '8 (teletext)',
}

_MODE_PLATFORM: Dict[int, str] = {
    0: 'Model B',
    1: 'Model B',
    2: 'Model B',
    3: 'Model B',
    4: 'Model A',
    5: 'Model A',
    6: 'Model A',
    7: 'Teletext',
}


def _mode_implementation_status(mode: int, spec: BBCModeSpec) -> Tuple[str, str]:
    override = _MODE_STATUS_OVERRIDES.get(mode)
    if override is not None:
        return override
    if spec.teletext:
        return (
            'partial',
            'teletext renderer (colours + mosaics); not full SAA5050',
        )
    if not spec.plot_enabled:
        return 'implemented', 'text only — PLOT/CLG disabled (like Model B)'
    return 'implemented', 'graphics + text'


def _mode_colours(mode: int, spec: BBCModeSpec) -> str:
    if mode in _MODE_COLOURS:
        return _MODE_COLOURS[mode]
    if spec.plot_enabled:
        return '256'
    if spec.teletext:
        return '8 (teletext)'
    return '16 (text)'


def _mode_platform(mode: int, spec: BBCModeSpec) -> str:
    if mode in _MODE_PLATFORM:
        return _MODE_PLATFORM[mode]
    if mode >= 8:
        return 'SDL / VGA'
    return '—'


def _mode_graphics_kind(spec: BBCModeSpec) -> str:
    if spec.teletext:
        return 'teletext'
    if spec.plot_enabled and spec.gfx_width > 0:
        return 'graphics'
    return 'text'


def _format_mode_resolution(spec: BBCModeSpec) -> str:
    if spec.teletext:
        return 'teletext'
    if spec.plot_enabled and spec.gfx_width > 0:
        return f'{spec.gfx_width}x{spec.gfx_height}'
    return '—'


def _format_mode_par(spec: BBCModeSpec) -> str:
    return f'{spec.par_w}:{spec.par_h}'


def _format_mode_os_scale(spec: BBCModeSpec) -> str:
    if not spec.plot_enabled or spec.gfx_width <= 0:
        return '—'
    x_scale, y_scale = bbc_os_scales(spec.gfx_width, spec.gfx_height)
    return f'{x_scale}x{y_scale}'


def _format_mode_cell(spec: BBCModeSpec) -> str:
    return f'{spec.cell_width}x{spec.cell_height}'


def _format_mode_line(mode: int, spec: BBCModeSpec) -> str:
    status, note = _mode_implementation_status(mode, spec)
    gfx = _format_mode_resolution(spec)
    text = f'{spec.text_cols}x{spec.text_rows}'
    cell = _format_mode_cell(spec)
    colours = _mode_colours(mode, spec)
    par = _format_mode_par(spec)
    os_scale = _format_mode_os_scale(spec)
    platform = _mode_platform(mode, spec)
    kind = _mode_graphics_kind(spec)
    return (
        f'MODE {mode:<2}  {gfx:<11}  {text:<7}  {cell:<5}  {colours:<12}  '
        f'{par:<4}  {os_scale:<5}  {platform:<10}  {kind:<9}  {status:<18}  {note}'
    )


def _print_mode_group(title: str, modes: Dict[int, BBCModeSpec]) -> None:
    print(title)
    print(
        '  MODE  resolution   text     cell   colours       PAR   OS     platform    kind       status              notes'
    )
    for mode in sorted(modes):
        print(f'  {_format_mode_line(mode, modes[mode])}')


def _print_help_modes() -> None:
    _section('=== BBC MODE n (bbc dialect, pygame display) ===', [
        'MODE n sets the text grid and graphics framebuffer.',
        'Default on pygame startup: MODE 8 (640x512).',
        'Unknown mode numbers: not implemented (ignored).',
        '',
        'Status key:',
        '  implemented          MODE switch, text, and graphics (where applicable)',
        '  under construction   partial support — behaviour may change',
        '  not implemented      no spec / not accepted',
    ])
    print()
    _print_mode_group('BBC Model B / Model A (modes 0-7)', BBC_MODE_SPECS)
    print()
    _print_mode_group('BBC BASIC for Windows / SDL extended (modes 8-31)', BB4W_MODE_SPECS)
    print()
    _section('Column guide', [
        'resolution   graphics framebuffer pixels (— if text/teletext only)',
        'text         character grid (cols x rows)',
        'cell         font matrix width x height in pixels',
        'colours      logical palette size on real BBC hardware (256 on SDL modes)',
        'PAR          pixel aspect ratio (window corrects non-square pixels)',
        'OS           MOS graphics units per pixel (1280 x 1024 OS space)',
        'platform     Model B / Model A / Teletext / SDL-VGA extended modes',
        'kind         graphics | text | teletext',
    ])
    print()
    _section('Notes', [
        'Modes 3 and 6 are text-only on real hardware; PLOT and CLG are ignored.',
        'Modes 0 and 2 use non-square pixels (PAR 1:2 or 2:1); window corrects aspect.',
        'Modes 8+ use square pixels (PAR 1:1); default interpreter framebuffer is MODE 8.',
        'MODE 7: VDU teletext control codes (129-135 fg, 145-151 gfx, 160-191 mosaic).',
        'CLI --gfx-width/--gfx-height overrides framebuffer without changing MODE table.',
        'CLI --scale N zooms the pygame window (set before first graphics command).',
    ])


def _print_help_repl() -> None:
    _section('=== REPL commands ===', [
        'HELP CLI       full command-line --help (flags, -i, session files)',
        'HELP PROGRAM   full LOAD / SAVE / LIST / AUTO / EDIT reference',
        'LIST [PRETTY|REFS] [start[-end]]',
        'RUN  CONT  NEW   (after STOP: LIST, PRINT, LVAR, then CONT)',
        'SAVE [PRETTY|REFS] [file]   LOAD file   DIR [path|pattern]   CD [path]',
        '  DIR test / DIR test\\  list folder contents; DIR *.bas  name filter',
        'REN|RENUMBER [start[,step]]   AUTO [start[,step]]',
        'EDIT n      edit one line (Ctrl+C / empty Enter cancels)',
        'EDIT        open the program in $EDITOR / Notepad, then reload',
        'HELP [topic]   MATRIX (= HELP DIALECTS)',
        'DIALECT [mini|mits|commodore|tiny|bbc] [strict|loose]   CASE [on|off|auto]',
        '  bare DIALECT reports dialect, strict on/off, and case mode',
        'bye | quit | exit | goodbye | q',
        '',
        'Entering the REPL from the shell:',
        '  mini_basic              or  mini_basic -i     open > prompt',
        '  mini_basic file.bas -i  RUN program, then stay at >',
        '  mini_basic file.bas     RUN then exit (no > unless -i)',
        '  mini_basic INPUT.TXT    session script then exit (use -i to stay)',
        '',
        'Tab completes filenames after LOAD, SAVE (*.bas/.bbc + backups), RUN, CD',
        'Windows: pip install -r requirements-repl.txt  (pyreadline3 line editing)',
        '',
        'Abbreviations (BBC/VAX style):',
        'H.=HELP   L.=LIST   LO.=LOAD   R.=RUN   N.=NEW',
        'SA.=SAVE   MA.=MATRIX',
    ])


def _print_help_program() -> None:
    """LOAD / SAVE / LIST / AUTO / EDIT — how programs enter and leave the REPL."""
    sections = [
        ('=== Program files (LOAD / SAVE / LIST / AUTO) ===', [
            'See also HELP FILES for OPENIN/PRINT# channel I/O (different topic).',
        ]),
        ('LOAD', [
            'LOAD filename',
            '  Load text .bas/.bbc or tokenized BBC (Wilson / Russell) binary.',
            '  Bare name without extension: try exact path, then .bas, then .bbc',
            '    e.g. LOAD demo  →  demo.bas or demo.bbc if present',
            '  Quoted paths allowed: LOAD "my program.bas"',
            '  Leading #!dialect or 1 REM dialect: … sets dialect (unless locked).',
            'CHAIN "file" uses the same path rules as LOAD.',
        ]),
        ('SAVE', [
            'SAVE [filename]              default form for this program (see below)',
            'SAVE PRETTY [filename]       structural indent, unnumbered (reloadable)',
            'SAVE REFS [filename]         like LIST REFS (jump targets numbered)',
            'SAVE NUMBERED [filename]     force classic line numbers on disk',
            '  If the program was LOADed from unnumbered text, bare SAVE uses PRETTY',
            '  so LOAD → EDIT n → SAVE keeps an unnumbered file (memory stays numbered).',
            '  Numbered loads / REPL-typed programs: bare SAVE writes line numbers.',
            '  Omit filename → reuse last LOADed/SAVEd name when known.',
            '  Non-mini dialect: prepends  N REM dialect: …  (N>=1 free line).',
            '  Extension is not invented on SAVE — type demo.bas if you want .bas.',
            '  Tokenized SAVE is not implemented (text only).',
        ]),
        ('LIST', [
            'LIST                         full program, numbered as stored',
            'LIST PRETTY                  structural indent; may split multi-stmt lines',
            'LIST REFS                    PRETTY-like; numbers mainly on GOTO targets',
            'LIST 100                     single line',
            'LIST 100-200   LIST 100,200  range (either punctuation)',
            'LIST 100-      LIST ,200     open-ended range',
            'LIST PRETTY 100-200          mode + range combined',
            '  CLI: mini_basic --pretty file.bas   (list structured and exit)',
        ]),
        ('AUTO', [
            'AUTO                         start 10, step 10',
            'AUTO start                   e.g. AUTO 100',
            'AUTO start,step              e.g. AUTO 100,5',
            '  Prompts with the next line number; empty line ends AUTO.',
            '  Type a full line number to jump; empty statement deletes that line.',
            '  For multi-line DEF PROC/FN: enter the DEF header at > (block entry).',
            '',
            '  No unnumbered AUTO: author structured text in an external editor, LOAD',
            '  (auto-numbers for EDIT), then bare SAVE → PRETTY if source was unnumbered.',
            '  REPL line editing remains single-line (EDIT n / AUTO).',
        ]),
        ('EDIT', [
            'EDIT n                       edit one stored line (prefilled buffer)',
            '  Empty Enter or Ctrl+C cancels (line unchanged).',
            '  Enter keeps the prefilled (or edited) text.',
            '  Arrow / Home / End keys move in the text (Windows, WSL, Linux, Termux).',
            '  To delete: bare line number at > (e.g. 15).',
            'EDIT                         open current program in the system editor.',
            '  Uses VISUAL or EDITOR, else Notepad (Windows) or nano/vim/vi.',
            '  Reloads memory when the editor exits. If you changed the text:',
            '    real LOAD/SAVE file → Save changes to file? (Y/N)',
            '    memory/tmp only     → Save as (filename, or Enter to keep in memory).',
            '  Type 10 PRINT "hi" at the > prompt to store/replace a line anytime.',
            '  Bare 10 at > deletes line 10.',
        ]),
        ('Related', [
            'DIR [pattern]   CD [path]   NEW   RENUMBER [start[,step]]',
            'HELP REPL for abbreviations and Tab completion.',
        ]),
    ]
    for index, (title, lines) in enumerate(sections):
        if index:
            print()
        _section(title, lines)


def _print_help_system() -> None:
    _section('=== System variables & pseudo-variables ===', [
        '_argc                 program argument count (mini)',
        'ARG(n)  ARG$(n)        nth argument (mini)',
        '',
        'TIME                  read: centiseconds since last TIME=...',
        'TIME = 0              start a stopwatch (benchmarks)',
        'TIME = n              set clock to n centiseconds',
        'TIME = TIME + n       bump clock by n (same as any TIME = <expr>)',
        '  persists across RUN/NEW; seconds = TIME / 100',
        'ERR  ERL               last error code / line',
        '',
        '_print_line_buffering   0|1',
        '_print_file_echo        0|1',
        '_tee_terminal           0|1  mirror pygame text/input to terminal',
        '_optimization_level     0|1|2  (parse cache / compiled expr)',
        '_print_field_width      PRINT comma zone width (default 10; 0 = tight, one space)',
        '  classic: PRINT 1,2 → right-justified zones of 10; use ; for no pad',
        '  resizable terminal: _print_field_width=0 or PRINT A; " text"',
        '_cols                   screen width (live terminal size when TTY + text display)',
        '_rows                   screen height (live terminal size when TTY + text display)',
        '',
        '_epsilon                machine epsilon (smallest step in 1+eps)',
        '_float_digits           safe decimal digits (~15 on IEEE double)',
        '_float_mantissa         mantissa bits in float storage (~53)',
        '_float_radix            number base of float (2 = binary)',
        '_ieee754                1 if float matches IEEE 754 binary64',
        '_save_case              0=UPPER 1=lower LIST/SAVE (mits/bbc only)',
        '_case_sensitive         0=fold  1=on  2=auto (dialect default)',
        '_bigint                 1=arbitrary % ints (default)  0=IEEE float',
        '  PRINT _epsilon, _float_digits, _ieee754',
        '  examples/mini/find_epsilon.bas   discover epsilon in BASIC',
        '  examples/mini/near_float.bas     NEAR / NEARSIG comparisons',
        '',
        'Debug: HELP DEBUG   (CLI --debug / --debug-filter)',
    ])


def _print_help_debug() -> None:
    """CLI and REPL help for interpreter debug output (dprint / --debug-filter)."""
    sections = [
        ('=== Debug output (--debug) ===', [
            'When debugging the interpreter (not your BASIC PRINT), turn on a quiet',
            'side channel that writes to the terminal (stderr) and mini_basic.log.',
            'Normal program output on stdout is unchanged.',
            '',
            'Turn on (from the shell, before starting mini_basic):',
            '  mini_basic --debug file.bas',
            '  mini_basic --debug --debug-filter IF file.bas',
            '  mini_basic --debug --debug-filter [VDU] -i',
            '',
            'Environment (same idea, no CLI flags):',
            '  set MINI_BASIC_DEBUG=1',
            '  set MINI_BASIC_DEBUG_FILTER=DIM',
            '',
            'Filter is a simple substring: a line is shown only if the filter text',
            'appears in that debug line. Tags below are the usual filter keys.',
        ]),
        ('Filter tags (first word of each debug line)', [
            'Tag          What it marks',
            '----------   -----------------------------------------------',
            '[EXEC]       each BASIC line about to run (very chatty)',
            '[CMD]        command word + rest after parse',
            '[IF]         IF / THEN / condition evaluation',
            '[DIM]        DIM array declaration and store',
            '[ARRAY]      array reference substitution problems',
            '[BOOL]       boolean expression parse (AND/OR trees)',
            '[CMP]        comparison operands (string vs number path)',
            '[AND]        steps inside a boolean AND chain',
            '[ASSIGN]     LET / assignment parse',
            '[COMPOUND]   +=  -=  *=  /= recognition',
            '[VDU]        text written with embedded VDU/colour codes',
            '[MOVE]       MOVE graphics (if enabled at that site)',
            '',
            'Examples:',
            '  --debug-filter IF      only IF-related lines (matches [IF])',
            '  --debug-filter [DIM]   only DIM lines (brackets optional)',
            '  --debug-filter VDU     colour / VDU write path',
            '  --debug-filter ASSIGN  assignment parse only',
            '',
            'Without --debug-filter, --debug prints every tagged line (noisy).',
            'Prefer a filter while tracking one bug.',
        ]),
        ('From Python (developers)', [
            'from mini_basic import dprint',
            'dprint("[IF]", "enter")     # same tags; needs --debug or active config',
            'On the interpreter object:  interp.dprint("[DIM]", "store", name)',
            'See mini_basic/util/debug.py for the full API.',
        ]),
    ]
    for index, (title, lines) in enumerate(sections):
        if index:
            print()
        _section(title, lines)


_HELP_PRINTERS: Dict[str, Callable[[], None]] = {
    'INDEX': _print_help_index,
    'OVERVIEW': _print_help_overview,
    'CLI': _print_help_cli,
    'FUNCTIONS': _print_help_functions,
    'STRINGS': _print_help_strings,
    'OPERATORS': _print_help_operators,
    'STATEMENTS': _print_help_statements,
    'FILES': _print_help_files,
    'GRAPHICS': _print_help_graphics,
    'MODES': _print_help_modes,
    'REPL': _print_help_repl,
    'PROGRAM': _print_help_program,
    'SYSTEM': _print_help_system,
    'DEBUG': _print_help_debug,
}


def normalize_help_topic(topic: str) -> Optional[str]:
    """Return canonical topic name, or None if unknown."""
    key = topic.strip().upper()
    if not key:
        return 'INDEX'
    return _HELP_ALIASES.get(key)


def print_help_topic(
    topic: str,
    *,
    print_dialects: Optional[Callable[[], None]] = None,
) -> None:
    """Print one HELP topic by canonical name."""
    if topic == 'DIALECTS':
        if print_dialects is not None:
            print_dialects()
        else:
            print('? HELP DIALECTS requires dialect printer')
        return
    _HELP_PRINTERS[topic]()


def print_help(
    topic: str = '',
    *,
    print_dialects: Optional[Callable[[], None]] = None,
) -> None:
    """Print HELP INDEX or a specific topic. Unknown topics list the index."""
    canonical = normalize_help_topic(topic)
    if canonical is None:
        print('? Unknown HELP topic')
        print()
        _print_help_index()
        return
    if canonical == 'INDEX':
        _print_help_index()
        return
    print_help_topic(canonical, print_dialects=print_dialects)


__all__ = [
    'HELP_MENU_ITEMS',
    'normalize_help_topic',
    'print_help',
    'print_help_topic',
]

