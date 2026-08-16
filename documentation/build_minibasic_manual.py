#!/usr/bin/env python3
"""Compile documentation/MINIBASIC_BBC_BASIC_Manual.html.

Takes the styling and structural idea of the included OCR HTML
(BBC_BASIC_Manual.html — RISC OS / classic BBC BASIC reference) and produces a
**mini_basic edition**: what this interpreter implements, how to run it, and
where it deliberately differs from full BBCSDL / RISC OS.

Regenerate:
  python documentation/build_minibasic_manual.py
"""
from __future__ import annotations

import html
import re
import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_OUT = Path(__file__).resolve().parent / "MINIBASIC_BBC_BASIC_Manual.html"
_SRC_HTML = Path(__file__).resolve().parent / "BBC_BASIC_Manual.html"
_FEATURES = _ROOT / "docs" / "LANGUAGE_FEATURES_1.00.md"
_FAMILY = Path(__file__).resolve().parent / "feature_matrices" / "01b_bbc_family.txt"


def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _css_from_source() -> str:
    if not _SRC_HTML.is_file():
        return _DEFAULT_CSS
    text = _SRC_HTML.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<style>(.*?)</style>", text, re.S | re.I)
    if not m:
        return _DEFAULT_CSS
    base = m.group(1)
    # mini_basic edition extras
    extra = """
    .banner {
        background: #1a3a5c;
        color: #f5f8fc;
        padding: 14px 18px;
        border-radius: 4px;
        margin: 1em 0 1.5em 0;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 0.95em;
        line-height: 1.45;
    }
    .banner strong { color: #fff; }
    .banner a { color: #9fd0ff; }
    .status-yes { color: #0a6b2d; font-weight: bold; }
    .status-partial { color: #8a5a00; font-weight: bold; }
    .status-no { color: #8b1a1a; font-weight: bold; }
    .note {
        background: #f7f4ea;
        border-left: 4px solid #c4a35a;
        padding: 8px 12px;
        margin: 0.8em 0;
        font-size: 0.95em;
    }
    nav.toc ul { list-style: none; padding-left: 0; }
    nav.toc li { margin: 4px 0; }
    nav.toc a { text-decoration: none; color: #1a3a5c; }
    nav.toc a:hover { text-decoration: underline; }
    footer.meta {
        margin-top: 3em;
        padding-top: 1em;
        border-top: 1px solid #ccc;
        font-size: 0.85em;
        color: #555;
        font-family: Arial, Helvetica, sans-serif;
    }
"""
    return base + extra


_DEFAULT_CSS = """
body { font-family: Georgia, serif; max-width: 800px; margin: 30px auto; padding: 0 20px; line-height: 1.5; }
h1, h2, h3 { font-family: Arial, sans-serif; }
pre { background: #f2f2f2; padding: 10px; overflow-x: auto; }
code { font-family: Consolas, monospace; background: #f2f2f2; padding: 2px 4px; }
table { border-collapse: collapse; width: 100%; margin: 0.6em 0; font-size: 0.9em; }
th, td { border: 1px solid #aaa; padding: 6px 10px; }
th { background: #e9e9e9; text-align: left; }
"""


def _version() -> str:
    try:
        sys.path.insert(0, str(_ROOT))
        from mini_basic.version import __version__

        return __version__
    except Exception:
        return "1.0.0.dev0"


def _h2_id(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug


def section(title: str, body_html: str, level: int = 2) -> str:
    tag = f"h{level}"
    if level == 2:
        return f'<{tag} id="{_esc(_h2_id(title))}">{_esc(title)}</{tag}>\n{body_html}\n'
    return f"<{tag}>{_esc(title)}</{tag}>\n{body_html}\n"


def p(*paragraphs: str) -> str:
    return "\n".join(f"<p>{html.escape(t)}</p>" for t in paragraphs)


def ul(items: list[str]) -> str:
    lis = "\n".join(f"<li>{html.escape(i)}</li>" for i in items)
    return f"<ul>\n{lis}\n</ul>"


def pre(code: str) -> str:
    return f"<pre><code>{html.escape(code)}</code></pre>"


def table(headers: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = []
    for row in rows:
        tds = "".join(f"<td>{c}</td>" for c in row)  # allow html in cells
        body.append(f"<tr>{tds}</tr>")
    return (
        f"<table>\n<thead><tr>{th}</tr></thead>\n"
        f"<tbody>\n{''.join(body)}\n</tbody>\n</table>"
    )


def status(s: str) -> str:
    s = s.strip().lower()
    if s in ("yes", "+", "ok", "full"):
        return '<span class="status-yes">yes</span>'
    if s in ("partial", "~", "partial / different"):
        return '<span class="status-partial">partial</span>'
    if s in ("no", "-", "deferred", "not"):
        return '<span class="status-no">no</span>'
    return html.escape(s)


def build() -> str:
    ver = _version()
    today = date.today().isoformat()
    css = _css_from_source()

    toc_titles = [
        "About this edition",
        "Running mini_basic",
        "Dialects",
        "Program structure",
        "Control flow",
        "Variables and expressions",
        "Strings and data",
        "Input and output",
        "Files",
        "OSCLI, star commands, and SYS",
        "Procedures and functions",
        "Graphics and MODE",
        "VDU control",
        "Sound (SOUND and ENVELOPE)",
        "Error handling",
        "BBC family compatibility matrix",
        "Keywords (quick reference)",
        "Not implemented (deferred)",
        "Relationship to the classic manual",
        "Examples",
    ]

    toc = '<nav class="toc"><h2>Contents</h2><ul>\n'
    for t in toc_titles:
        toc += f'<li><a href="#{_esc(_h2_id(t))}">{_esc(t)}</a></li>\n'
    toc += "</ul></nav>\n"

    parts: list[str] = []

    parts.append(
        section(
            "About this edition",
            p(
                "This document is the mini_basic edition of a BBC BASIC reference. "
                "It is compiled for users of the mini_basic interpreter (Python package mini_basic / mini-basic), "
                "not for RISC OS Desktop BASIC or a physical BBC Micro.",
                "The included file BBC_BASIC_Manual.html is the classic OCR reference (overview, techniques, keywords, appendices). "
                "Where classic behaviour and mini_basic agree, you may treat that text as background; "
                "where they diverge, this edition is authoritative for mini_basic.",
                f"Interpreter version described: {ver}. Language baseline: docs/LANGUAGE_FEATURES_1.00.md.",
            )
            + '<div class="note"><strong>Honesty rule.</strong> mini_basic aims for useful BBCSDL / BBC-family '
            "compatibility for real demos (welcome, squares, piechart, jclock, …). It does not claim full "
            "SOUND/ENVELOPE, WIMP, SYS, assembler, or complete MODE 7 SAA5050 teletext.</div>",
        )
    )

    parts.append(
        section(
            "Running mini_basic",
            p(
                "From a source tree or after pip install of the mini-basic wheel:",
            )
            + pre(
                "# Run a program (text / none / pygame)\n"
                "python -m mini_basic path/to/program.bas\n"
                "python -m mini_basic --dialect bbc --display pygame examples/graphics/squares.bbc\n"
                "mini-basic --version\n"
                "\n"
                "# Dialects: mini | bbc | mits | commodore | tiny\n"
                "# Display:  pygame | terminal | none\n"
            )
            + p(
                "Environment: MINIBASIC_DIR (install tree), MINIBASIC_DISPLAY / MINIBASIC_NO_GRAPHICS, "
                "MINI_BASIC_DIALECT. Optional: pip install \"mini-basic[display]\" for pygame-ce.",
            )
            + p(
                "Tokenized BBCSDL / Beeb .bbc files can be loaded; the detokenizer reconstructs text before RUN.",
            ),
        )
    )

    parts.append(
        section(
            "Dialects",
            table(
                ["Dialect", "Role", "Notes"],
                [
                    ["mini", "Default / superset", "Numbered or unnumbered; structured BBC flow; mini extensions (BREAK/CONTINUE)."],
                    ["bbc", "BBCSDL / BB4W-oriented", "PROC/FN glued names; CASE; WHILE; REPEAT; MODE/VDU/graphics."],
                    ["mits", "Classic Dartmouth-style", "Numbered lines; GOTO/GOSUB; ON ERROR."],
                    ["commodore", "C64-flavoured", "Numbered lines; classic control set."],
                    ["tiny", "Minimal 1975-style", "Smallest statement set for teaching."],
                ],
            )
            + p(
                "In bbc dialect, procedure and function calls must glue the name: PROCfoo not PROC foo. "
                "LIST re-glues names so listings paste cleanly into Archimedes-style environments.",
            ),
        )
    )

    parts.append(
        section(
            "Program structure",
            ul(
                [
                    "Lines may be numbered or unnumbered (dialect-dependent).",
                    "Multiple statements on a line: use colon (:).",
                    "Comments: REM or ' (BBC-style).",
                    "Commands: NEW, LOAD, SAVE, CHAIN, RUN, LIST, END, STOP.",
                    "Programs are text .bas/.bbc or detokenized Russell token streams.",
                ]
            )
            + pre(
                "10 REM hello\n"
                "20 PRINT \"Hello from mini_basic\"\n"
                "30 END\n"
            ),
        )
    )

    parts.append(
        section(
            "Control flow",
            table(
                ["Feature", "mini_basic"],
                [
                    ["GOTO / GOSUB / RETURN", status("yes")],
                    ["IF … THEN / bare IF : body", status("yes")],
                    ["IF / ELSE / ELSEIF / ENDIF", status("yes")],
                    ["ON … GOTO / GOSUB", status("yes")],
                    ["FOR / NEXT (int and float)", status("yes")],
                    ["WHILE / WEND (ENDWHILE)", status("yes")],
                    ["REPEAT / UNTIL", status("yes")],
                    ["EXIT FOR / WHILE / REPEAT", status("yes")],
                    ["CASE / WHEN / OTHERWISE / ENDCASE", status("yes")],
                    ["BREAK / CONTINUE", status("partial") + " (mini extension)"],
                ],
            )
            + p(
                "Nested integer FOR loops with simple LET/COLOUR/PLOT bodies may run on a native fast path "
                "(e.g. munching squares). Float geometry loops remain interpreter-paced.",
            ),
        )
    )

    parts.append(
        section(
            "Variables and expressions",
            ul(
                [
                    "Floats (default), integers with % suffix, strings with $.",
                    "Arrays: DIM (numeric and string).",
                    "Arithmetic: + - * / DIV MOD ^ and shifts << >>.",
                    "Bitwise: AND OR EOR/XOR NOT on integers (pure bitwise expressions can compile).",
                    "Relations: = <> < > <= >= ; BBC TRUE is -1, FALSE is 0.",
                    "Hex and binary forms where implemented (BBC-style).",
                    "Built-ins: SIN COS TAN ASN ACS ATN SQR ABS INT SGN RND LOG EXP RAD DEG …",
                    "Use MOD for modulo; bare % is the integer-variable suffix, not modulo.",
                    "SIN/COS/TAN use radians unless you convert with DEG/RAD helpers.",
                ]
            )
            + pre(
                "A% = 5\n"
                "B% = 3\n"
                "PRINT (A% EOR B%) AND 255   : REM 6\n"
                "PRINT 10 MOD 3             : REM 1\n"
            )
            + '<div class="note">Known gap: PRINT a(i) may not expand array subscripts in every form; '
            "use PRINT a(i); or a temporary assignment.</div>",
        )
    )

    parts.append(
        section(
            "Strings and data",
            ul(
                [
                    "LEFT$ RIGHT$ MID$ STR$ VAL ASC CHR$ LEN INSTR STRING$ …",
                    "Glued forms accepted where BBC does: ASC\"B\", INKEY1 → INKEY(1).",
                    "DATA / READ / RESTORE for embedded data.",
                    "TIME and TIME$ for timing (where provided).",
                ]
            ),
        )
    )

    parts.append(
        section(
            "Input and output",
            ul(
                [
                    "PRINT / ? with TAB, SPC, commas and semicolons; embedded VDU sequences.",
                    "INPUT / LINE INPUT.",
                    "GET / GET$ / INKEY / INKEY$ (positive INKEY timeout presents graphics).",
                    "MOUSE on desktop (pygame) backends.",
                    "COLOUR / COLOR for text and multi-arg RGB palette definitions.",
                ]
            ),
        )
    )

    parts.append(
        section(
            "Files",
            ul(
                [
                    "OPENIN / OPENOUT / OPENUP",
                    "PRINT# / INPUT# / BGET# / BPUT# / EOF# / CLOSE#",
                    "Paths relative to working directory / MINIBASIC_DIR conventions.",
                ]
            )
        )
    )

    parts.append(
        section(
            "OSCLI, star commands, and SYS",
            p(
                "OSCLI expression evaluates a string and runs the same handler as a * line "
                "(*REFRESH ON). This is not a host shell and it is not SYS.",
            )
            + table(
                ["Command", "Behaviour"],
                [
                    ["REFRESH / ON / OFF", "Present the back buffer, or set auto-refresh."],
                    ['GSAVE "file" x,y,w,h', "Save an OS-unit rectangle as a 24-bit BMP (piechart)."],
                    ['DISPLAY "file" x,y,w,h', "Blit or scale a BMP into that rectangle (pygame when a window is up)."],
                    ["FX, TV, KEY", "Accepted no-ops (welcome / MOS noise)."],
                    ["ERASE / DELETE", "Delete a file in the working directory."],
                ],
            )
            + p(
                "Anything else (LOAD, MDISPLAY, FONT, SPOOL, CAT, …) is ignored with no error. "
                "Russell clock.bbc needs DIM … EXT# plus OSCLI LOAD / MDISPLAY into a heap; "
                "that program is not a regular example. Use basics/Clock.bas or jclock.",
            )
            + p(
                'SYS "…", SYS `name`, and SYS used as a function report '
                "? Unimplemented: SYS (RISC OS / OS call). "
                "Same class as CALL, USR, and INSTALL. "
                "ON SYS is kept only so the colon tail is not split; the event is not delivered.",
            )
            + pre(
                'OSCLI "REFRESH OFF"\n'
                'OSCLI "GSAVE ""shot.bmp"" 0,0,200,200"\n'
                'OSCLI "DISPLAY ""shot.bmp"" 0,0,200,100"\n'
                '*REFRESH\n'
                "\n"
                'SYS "SDL_SetWindowTitle", @hwnd%, "Demo"   : REM ? Unimplemented\n'
            ),
        )
    )

    parts.append(
        section(
            "Procedures and functions",
            p(
                "DEF PROC / ENDPROC and DEF FN / END DEF. "
                "Call with glued names: PROCdraw, FNlen(x). "
                "Both DEFPROC and DEF PROC forms are accepted; the name after PROC/FN must still be glued.",
            )
            + pre(
                "DEF PROCgreet(n$)\n"
                "  PRINT \"Hello \"; n$\n"
                "ENDPROC\n"
                "\n"
                "PROCgreet(\"world\")\n"
            ),
        )
    )

    parts.append(
        section(
            "Graphics and MODE",
            p(
                "Graphics require a display backend that can plot (typically pygame via --display pygame "
                "or auto-enable when graphics keywords appear). Use --display none for headless runs.",
            )
            + table(
                ["Statement", "Status"],
                [
                    ["MODE n (0–7 + extended 8+)", status("yes")],
                    ["MODE 7 teletext", status("partial") + " (colours, mosaics, flash; not full SAA5050)"],
                    ["GCOL action, colour (0–7)", status("yes")],
                    ["COLOUR / COLOR (incl. RGB multi-arg)", status("yes")],
                    ["MOVE / DRAW / PLOT", status("yes") + " (subset of PLOT codes + BB4W extras)"],
                    ["CIRCLE / CIRCLE FILL", status("yes")],
                    ["RECTANGLE / RECTANGLE FILL", status("yes")],
                    ["CLS / CLG", status("yes")],
                    ["ORIGIN / VDU 29", status("yes") + " (bottom-left OS origin)"],
                    ["VDU 5 graphics text", status("yes") + " (top-left of character cell; colour 7 = white)"],
                    ["WAIT / *REFRESH", status("yes")],
                    ["OFF (cursor)", status("yes")],
                    ["SOUND / ENVELOPE", status("partial") + " (see Sound section — silent stubs)"],
                ],
            )
            + pre(
                "MODE 8\n"
                "GCOL 0, 7\n"
                "MOVE 0, 0\n"
                "DRAW 1280, 1024\n"
                "CIRCLE FILL 640, 512, 200\n"
            ),
        )
    )

    parts.append(
        section(
            "Sound (SOUND and ENVELOPE)",
            p(
                "There is no audio engine: speakers stay silent. SOUND and ENVELOPE exist so BBCSDL "
                "programs (especially welcome.bbc) parse cleanly and do not fall into ON ERROR traps.",
            )
            + table(
                ["Statement", "What works", "What does not"],
                [
                    [
                        "ENVELOPE …",
                        "Accepted; arguments evaluated (e.g. RND side effects); silent no-op",
                        "No ADSR/pitch envelope; does not shape SOUND",
                    ],
                    [
                        "SOUND ch, amp, pitch, dur",
                        "Four numeric args required; under a non-terminal (pygame) display, sleeps "
                        "for pacing using duration only",
                        "No tone; channel, amplitude and pitch ignored for audio",
                    ],
                    [
                        "SOUND OFF / *VOICE / *TEMPO / *STEREO / ADVAL queues",
                        "Not real audio control",
                        "No multi-channel synthesis (polly deferred)",
                    ],
                ],
            )
            + p(
                "Duration units are treated as classic BBC 1/20 second steps: wait ≈ dur × 0.05 s, "
                "capped at 1.0 s (so SOUND …,255 does not stall for many seconds of silence). "
                "With --display none or terminal, SOUND is still parsed but usually does not sleep.",
            )
            + pre(
                "10 ENVELOPE 1,1,-10,-10,-10,255,255,255,127,0,0,-127,127,0\n"
                "20 PRINT \"envelope ok\"   : REM no error, no sound\n"
                "30 MODE 8\n"
                "40 SOUND 1,-15,100,4     : REM ~0.2 s silent pause (pygame)\n"
                "50 PRINT \"after sound\"\n"
                "60 END\n"
            )
            + p(
                "Also accepted (silent / pacing only): SOUND 1,1,255,255 and SOUND &11,0,1,1 "
                "(welcome); SOUND 1,-15,50,2 (click-style delay in some games).",
            )
            + '<div class="note"><strong>Not 1.00:</strong> real beeps, music, or full SOUND/ENVELOPE '
            "hardware. That remains deferred (e.g. polly.txt).</div>",
        )
    )

    parts.append(
        section(
            "VDU control",
            p(
                "VDU sequences match the 1.00 phases A–C plan. Unknown VDU 23,n forms consume parameters "
                "and do not raise errors (Phase C).",
            )
            + table(
                ["Codes", "Meaning in mini_basic"],
                [
                    ["4 / 5", "Text vs graphics print mode"],
                    ["7", "Bell (soft)"],
                    ["8–11, 13", "Cursor motion / CR"],
                    ["12 / 16", "CLS / CLG"],
                    ["17", "Text colour (COLOUR)"],
                    ["18", "GCOL"],
                    ["20", "Reset colours"],
                    ["24", "Graphics viewport (store; soft clip)"],
                    ["25", "PLOT"],
                    ["26", "Reset viewports"],
                    ["28", "Text viewport (store + cursor clamp)"],
                    ["29", "ORIGIN"],
                    ["30 / 31", "Cursor home / TAB(x,y)"],
                    ["23,1", "Cursor visible"],
                    ["23,22,w;h;cx,cy,ncols,cs", "User mode (custom size + character cell)"],
                    ["23,n redefine char", "8×8 user glyphs"],
                    ["23,* other", "Consume; no error"],
                ],
            )
            + pre(
                "REM squares.bbc style custom screen\n"
                "W% = 512\n"
                "VDU 23,22,W%;W%;8,16,16,0\n"
            ),
        )
    )

    parts.append(
        section(
            "Error handling",
            ul(
                [
                    "ON ERROR … with ERR and ERL available in handlers.",
                    "RESUME where supported.",
                    "ON CLOSE for window close (pygame).",
                ]
            )
            + p(
                "Missing THEN line targets abort RUN after an IF error message (classic-safe behaviour).",
            ),
        )
    )

    # Family matrix from feature file (simplified parse)
    family_rows: list[list[str]] = []
    if _FAMILY.is_file():
        for line in _FAMILY.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip().startswith(("PROC", "DEF", "LIST", "CASE", "WHILE", "SYS", "@", "INSTALL", "MODE", "VDU", "ORIGIN", "PLOT", "CIRCLE", "GCOL", "Colour", "INKEY", "ENVELOPE", "MOUSE", "ON ", "Integer", "DIV", "TRUE", "Line", "Tokenized", "welcome", "Bare", "ASC")):
                continue
            # fixed-width-ish columns
            m = re.match(
                r"^\s*(.+?)\s{2,}([+\-~])\s+([+\-~])\s+([+\-~])\s+([+\-~])\s+([+\-~])\s+(.*)$",
                line,
            )
            if not m:
                continue
            feat, beeb, ros, bb4w, sdl, mini, notes = m.groups()
            family_rows.append(
                [
                    html.escape(feat.strip()),
                    status(beeb),
                    status(ros),
                    status(bb4w),
                    status(sdl),
                    status(mini),
                    html.escape(notes.strip()[:80]),
                ]
            )

    parts.append(
        section(
            "BBC family compatibility matrix",
            p(
                "Legend: yes = supported, partial = subset or different semantics, no = not available. "
                "Columns: Beeb MOS, RISC OS, BB4W, BBCSDL, mini_basic (bbc mode).",
            )
            + (
                table(
                    ["Feature", "Beeb", "ROS", "BB4W", "SDL", "mini", "Notes"],
                    family_rows,
                )
                if family_rows
                else p("(Matrix file documentation/feature_matrices/01b_bbc_family.txt not found.)")
            ),
        )
    )

    parts.append(
        section(
            "Keywords (quick reference)",
            p(
                "Common statements and functions available in bbc/mini modes. "
                "This is not the full classic keyword encyclopaedia; see BBC_BASIC_Manual.html Part 3 for historical prose.",
            )
            + pre(
                "Program:    NEW LOAD SAVE CHAIN RUN LIST END STOP REM\n"
                "Flow:       IF THEN ELSE ELSEIF ENDIF FOR NEXT WHILE WEND REPEAT UNTIL\n"
                "            CASE WHEN OTHERWISE ENDCASE GOTO GOSUB RETURN ON EXIT\n"
                "Proc/FN:    DEF PROC ENDPROC DEF FN END DEF\n"
                "I/O:        PRINT INPUT LINE GET GET$ INKEY INKEY$ COLOUR COLOR\n"
                "Files:      OPENIN OPENOUT OPENUP PRINT# INPUT# BGET# BPUT# EOF# CLOSE#\n"
                "Graphics:   MODE GCOL MOVE DRAW PLOT CIRCLE RECTANGLE CLS CLG ORIGIN\n"
                "            WAIT OFF VDU OSCLI *\n"
                "Data:       DATA READ RESTORE DIM\n"
                "Errors:     ON ERROR RESUME ON CLOSE\n"
                "Functions:  ABS ACS ASN ATN COS SIN TAN SQR LOG EXP INT SGN RND\n"
                "            RAD DEG ASC CHR$ LEFT$ RIGHT$ MID$ STR$ VAL LEN INSTR\n"
                "            TIME TIME$ POINT TINT (where implemented)\n"
            ),
        )
    )

    parts.append(
        section(
            "Not implemented (deferred)",
            p(
                "These areas are out of scope for the 1.00 language baseline. Programs that need them "
                "should be deferred or rewritten.",
            )
            + table(
                ["Area", "Examples"],
                [
                    ["RISC OS WIMP", "MENU, WINDOW, ICON, rich ON MOUSE UI"],
                    ["Inline assembler", "OSASM, CALL/USR machine code"],
                    ["OS FFI", "SYS Windows API, INSTALL libraries"],
                    ["Structures", "DIM struct{} / TYPE as in BB4W"],
                    ["Pointers", "byte/word/string indirection ? ! $ $$"],
                    [
                        "Sound (real audio)",
                        "Multi-channel synthesis / polly. Stubs: ENVELOPE no-op; "
                        "SOUND silent + optional capped wait (see Sound section)",
                    ],
                    ["Teletext remainder", "Double-height, conceal, boxed, full SAA5050"],
                    ["Physics / network", "Box2D bindings, Ceefax HTTP"],
                    ["Compiler", "Crunch / compile-to-native"],
                ],
            ),
        )
    )

    parts.append(
        section(
            "Relationship to the classic manual",
            p(
                "Source HTML: documentation/BBC_BASIC_Manual.html (Part 1 Overview, Part 2 Programming techniques, "
                "Part 3 Keywords, Part 4 Appendices). That text describes classic BBC BASIC / RISC OS environments.",
            )
            + ul(
                [
                    "Part 1 (entering BASIC, editing): use mini_basic CLI/REPL instead of RISC OS *BASIC.",
                    "Part 2 techniques (loops, PROC, arrays, strings): largely apply when using dialect bbc/mini.",
                    "Graphics and VDU chapters: use this edition’s MODE/VDU tables; hardware MODE timings differ.",
                    "WIMP / assembler / SYS chapters: not applicable to mini_basic 1.00.",
                    "Sound chapters: not a full synthesis engine here.",
                ]
            )
            + p(
                "Open the classic HTML for historical wording; open this HTML for what mini_basic will actually run.",
            ),
        )
    )

    parts.append(
        section(
            "Examples",
            p(
                "Runnable samples live under examples/ in a full source checkout "
                "(not inside the pip wheel).",
            )
            + ul(
                [
                    "examples/mini/ — small demos and CLI samples",
                    "examples/graphics/ — squares, saucer, piechart, jclock, wheel, …",
                    "examples/vdu/ — VDU phase demos",
                    "examples/teletext/ — MODE 7 test screen",
                    "examples/games/ — larger BBCSDL-style games (needs full tree + often pygame)",
                ]
            )
            + p(
                "Programs confirmed to look right on mini_basic include welcome, squares, saucer, flier, "
                "soccerball, wheel, jclock, filters, hanoi, and animal (when those files are in your tree).",
            )
            + '<div class="note"><strong>Developers only:</strong> automated BBCSDL regression material is under '
            "<code>test/corpus/bbcsdl/</code> (audit list in CORPUS_AUDIT.txt). That tree is not part of the "
            "language reference for end users and is omitted from the PyPI package.</div>",
        )
    )

    body = "\n".join(parts)
    banner = f"""
<div class="banner">
  <strong>mini_basic BBC BASIC Reference</strong> (edition for this interpreter)<br>
  Version {_esc(ver)} · Generated {_esc(today)} ·
  Companion to <code>BBC_BASIC_Manual.html</code><br>
  Language baseline: <code>docs/LANGUAGE_FEATURES_1.00.md</code> · Packaging: <code>docs/PACKAGING.md</code>
</div>
"""

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>mini_basic BBC BASIC Reference</title>
<style>
{css}
</style>
</head>
<body>
{banner}
<h1>mini_basic BBC BASIC Reference</h1>
<p>A practical reference for programming in BBC-style BASIC under
<strong>mini_basic</strong>, compiled as a companion to the included classic
BBC BASIC HTML manual.</p>
{toc}
{body}
<footer class="meta">
Generated by documentation/build_minibasic_manual.py ·
Source style from BBC_BASIC_Manual.html ·
Not affiliated with Acorn or RISC OS Ltd ·
mini_basic is an independent Python interpreter.
</footer>
</body>
</html>
"""
    return doc


def main() -> int:
    html_out = build()
    _OUT.write_text(html_out, encoding="utf-8")
    print(f"Wrote {_OUT} ({len(html_out)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
