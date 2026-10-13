"""A minimal tkinter source editor for mini_basic ``.bas``/``.bbc`` programs.

Scope (intentionally small, first step towards a fuller tool):
  * Open/Save/Save As for BASIC source files.
  * mini_basic-aware syntax highlighting (keywords, PROC/ENDPROC/FN,
    ``*``-commands, line numbers, dialect hint comments).
  * A "Run" action that launches the *real* interpreter as a subprocess
    (``python -m mini_basic <file>``), the same way it is normally run
    from a shell. This editor does not reimplement any display: pygame
    graphics programs still open their own pygame window, and console
    programs still use the ANSI terminal the interpreter already uses.

No GUI REPL, no in-editor graphics/terminal pane: see tools/editor.py's
module docstring in future revisions, or docs/, for anything beyond this.

Usage::

    python tools/editor.py [file.bas]
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools.editor_logic import (  # noqa: E402
    dedent_for_keyword,
    detect_numbered,
    first_keyword,
    indent_for_new_line,
    next_line_number,
    split_leading_number,
    split_leading_ws,
    used_line_numbers,
)

# Keywords/operators for highlighting. mini_basic accepts several dialects
# (mini/mits/bbc/commodore/tiny); this list is a practical superset for
# readability, not a formal grammar.
_KEYWORDS = (
    'PRINT LET IF THEN ELSE FOR TO STEP NEXT GOTO GOSUB RETURN END STOP '
    'DIM DATA READ RESTORE INPUT REM DEF LOCAL REPEAT UNTIL WHILE ENDWHILE '
    'CASE OF WHEN OTHERWISE ENDCASE ON OFF ERROR TRACE LIBRARY INSTALL '
    'AND OR NOT EOR MOD DIV TRUE FALSE '
    'SOUND ENVELOPE VDU MODE COLOUR COLOR GCOL PLOT CIRCLE LINE RECTANGLE '
    'ELLIPSE POINT DRAW MOVE CLS CLG TAB SPC WIDTH HIMEM LOMEM '
    'CHR$ ASC LEN LEFT$ RIGHT$ MID$ STR$ STRING$ VAL INKEY INKEY$ GET GET$ '
    'SGN ABS INT SQR SIN COS TAN ATN LOG LN EXP RND PI TIME OSCLI'
).split()
_KEYWORD_RE = re.compile(r'\b(' + '|'.join(re.escape(k) for k in _KEYWORDS) + r')\b', re.IGNORECASE)
_PROC_RE = re.compile(r'\b(DEF\s+)?(PROC|ENDPROC|FN)\w*\b', re.IGNORECASE)
_STAR_CMD_RE = re.compile(r'(^|:)\s*(\*\w+)')
_LINE_NUM_RE = re.compile(r'^\s*(\d+)\b')
_STRING_RE = re.compile(r'"[^"\n]*"')
_REM_COMMENT_RE = re.compile(r"\bREM\b.*$|'.*$", re.IGNORECASE)
_DIALECT_HINT_RE = re.compile(r"^\s*(\d+\s+)?(REM\s+dialect\s*:|'\s*dialect\s*:)", re.IGNORECASE)

_TAG_STYLES = {
    'keyword': {'foreground': '#0033cc'},
    'proc': {'foreground': '#aa00aa', 'font': ('TkFixedFont', 10, 'bold')},
    'star': {'foreground': '#cc6600', 'font': ('TkFixedFont', 10, 'bold')},
    'line_number': {'foreground': '#888888'},
    'string': {'foreground': '#008800'},
    'comment': {'foreground': '#999999', 'font': ('TkFixedFont', 10, 'italic')},
    'dialect_hint': {'foreground': '#999999', 'font': ('TkFixedFont', 10, 'bold italic')},
}

_DIALECTS = ('auto', 'mini', 'mits', 'bbc', 'commodore', 'tiny')


class EditorWindow:
    def __init__(self, root: tk.Tk, path: Optional[str] = None) -> None:
        self.root = root
        self.path: Optional[str] = None
        self._highlight_job: Optional[str] = None
        self._run_proc: Optional[subprocess.Popen] = None
        self.numbered = False

        self._build_menu()
        self._build_widgets()

        if path:
            self._load_file(path)
        else:
            self._update_title()

    # -- UI construction -------------------------------------------------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Open...', accelerator='Ctrl+O', command=self.open_file)
        file_menu.add_command(label='Save', accelerator='Ctrl+S', command=self.save_file)
        file_menu.add_command(label='Save As...', command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.root.quit)
        menubar.add_cascade(label='File', menu=file_menu)
        self.root.config(menu=menubar)

        self.root.bind('<Control-o>', lambda _e: self.open_file())
        self.root.bind('<Control-s>', lambda _e: self.save_file())

    def _build_widgets(self) -> None:
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text='Run', command=self.run_program).pack(side=tk.LEFT, padx=4, pady=4)

        ttk.Label(toolbar, text='Dialect:').pack(side=tk.LEFT, padx=(12, 2))
        self.dialect_var = tk.StringVar(value='auto')
        ttk.Combobox(
            toolbar, textvariable=self.dialect_var, values=_DIALECTS,
            width=10, state='readonly',
        ).pack(side=tk.LEFT)

        self.pygame_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            toolbar, text='Use pygame display', variable=self.pygame_var,
        ).pack(side=tk.LEFT, padx=(12, 2))

        self.mode_var = tk.StringVar(value='Unnumbered')
        ttk.Label(toolbar, textvariable=self.mode_var, anchor='e').pack(
            side=tk.RIGHT, padx=(2, 12),
        )

        self.status_var = tk.StringVar(value='Ready')
        ttk.Label(self.root, textvariable=self.status_var, anchor='w').pack(
            side=tk.BOTTOM, fill=tk.X,
        )

        text_frame = ttk.Frame(self.root)
        text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.text = tk.Text(text_frame, wrap='none', undo=True, font=('TkFixedFont', 11))
        yscroll = ttk.Scrollbar(text_frame, orient='vertical', command=self.text.yview)
        xscroll = ttk.Scrollbar(text_frame, orient='horizontal', command=self.text.xview)
        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.text.grid(row=0, column=0, sticky='nsew')
        yscroll.grid(row=0, column=1, sticky='ns')
        xscroll.grid(row=1, column=0, sticky='ew')
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        for name, style in _TAG_STYLES.items():
            self.text.tag_configure(name, **style)

        self.text.bind('<<Modified>>', self._on_modified)
        self.text.bind('<Return>', self._on_return)
        self.text.bind('<KeyRelease>', self._on_key_release)

    # -- File handling -----------------------------------------------------

    def open_file(self) -> None:
        path = filedialog.askopenfilename(
            title='Open BASIC program',
            filetypes=[('BASIC source', '*.bas *.bbc *.txt'), ('All files', '*.*')],
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str) -> None:
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                content = fh.read()
        except OSError as exc:
            messagebox.showerror('Open failed', str(exc))
            return
        self.path = path
        self.text.delete('1.0', tk.END)
        self.text.insert('1.0', content)
        self.text.edit_modified(False)
        self._set_numbered_mode(detect_numbered(content))
        self._highlight()
        self._update_title()
        mode = 'numbered' if self.numbered else 'unnumbered'
        self.status_var.set(f'Opened {path} ({mode})')

    def save_file(self) -> None:
        if not self.path:
            self.save_file_as()
            return
        self._write_to(self.path)

    def save_file_as(self) -> None:
        path = filedialog.asksaveasfilename(
            title='Save BASIC program',
            defaultextension='.bas',
            filetypes=[('BASIC source', '*.bas *.bbc *.txt'), ('All files', '*.*')],
        )
        if path:
            self.path = path
            self._write_to(path)
            self._update_title()

    def _write_to(self, path: str) -> None:
        content = self.text.get('1.0', 'end-1c')
        try:
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(content)
        except OSError as exc:
            messagebox.showerror('Save failed', str(exc))
            return
        self.text.edit_modified(False)
        self.status_var.set(f'Saved {path}')

    def _update_title(self) -> None:
        name = self.path or '(untitled)'
        self.root.title(f'mini_basic editor - {name}')

    # -- Line numbering / auto-indent ------------------------------------

    def _set_numbered_mode(self, numbered: bool) -> None:
        self.numbered = numbered
        self.mode_var.set('Numbered' if numbered else 'Unnumbered')

    def _on_return(self, _event: object) -> str:
        """New line: carries a line number on if the program uses them, and
        auto-indents one step in after a block opener (FOR/WHILE/.../block IF)."""
        index = self.text.index('insert')
        line_no = index.split('.')[0]
        line_text = self.text.get(f'{line_no}.0', f'{line_no}.end')

        ws, rest = split_leading_ws(line_text)
        if self.numbered:
            number, statement = split_leading_number(rest)
        else:
            number, statement = None, rest

        new_ws = indent_for_new_line(ws, statement)
        prefix = ''
        if self.numbered:
            new_number = next_line_number(
                used_line_numbers(self.text.get('1.0', 'end-1c')), number,
            )
            prefix = f'{new_number} '
        self.text.insert('insert', '\n' + prefix + new_ws)
        return 'break'

    def _on_key_release(self, event: object) -> None:
        """Right as a closer keyword (NEXT/ENDPROC/ELSE/...) finishes being
        typed at the end of a line, dedent that line by one step.

        Only fires exactly once per keyword: it requires the cursor to sit
        at the end of the line and the line's statement text to match the
        keyword exactly (no trailing text yet), so further keystrokes
        (a trailing space, more words) don't keep dedenting the same line.
        """
        if getattr(event, 'keysym', None) in ('Return', 'KP_Enter'):
            return
        index = self.text.index('insert')
        line_no, col_str = index.split('.')
        col = int(col_str)
        line_start = f'{line_no}.0'
        line_text = self.text.get(line_start, f'{line_no}.end')
        if col != len(line_text):
            return

        ws, rest = split_leading_ws(line_text)
        statement = rest
        if self.numbered:
            _number, after_number = split_leading_number(rest)
            statement = after_number
        word = first_keyword(statement)
        if not word or statement.upper() != word:
            return
        new_ws = dedent_for_keyword(ws, word)
        if new_ws is None:
            return
        delta = len(ws) - len(new_ws)
        self.text.delete(line_start, f'{line_no}.{len(ws)}')
        self.text.insert(line_start, new_ws)
        self.text.mark_set('insert', f'{line_no}.{max(0, col - delta)}')

    # -- Highlighting --------------------------------------------------

    def _on_modified(self, _event: object = None) -> None:
        if not self.text.edit_modified():
            return
        if self._highlight_job is not None:
            self.root.after_cancel(self._highlight_job)
        self._highlight_job = self.root.after(200, self._highlight)

    def _highlight(self) -> None:
        self._highlight_job = None
        for tag in _TAG_STYLES:
            self.text.tag_remove(tag, '1.0', tk.END)

        lines = self.text.get('1.0', 'end-1c').split('\n')
        for lineno, line in enumerate(lines, start=1):
            self._highlight_line(lineno, line)

    def _highlight_line(self, lineno: int, line: str) -> None:
        def add(tag: str, start: int, end: int) -> None:
            self.text.tag_add(tag, f'{lineno}.{start}', f'{lineno}.{end}')

        if _DIALECT_HINT_RE.match(line):
            add('dialect_hint', 0, len(line))
            return

        m = _LINE_NUM_RE.match(line)
        if m:
            add('line_number', m.start(1), m.end(1))

        for m in _KEYWORD_RE.finditer(line):
            add('keyword', m.start(), m.end())
        for m in _PROC_RE.finditer(line):
            add('proc', m.start(), m.end())
        for m in _STAR_CMD_RE.finditer(line):
            add('star', m.start(2), m.end(2))
        for m in _STRING_RE.finditer(line):
            add('string', m.start(), m.end())
        m = _REM_COMMENT_RE.search(line)
        if m:
            add('comment', m.start(), m.end())

    # -- Running ---------------------------------------------------------

    def run_program(self) -> None:
        if not self.path:
            messagebox.showinfo('Save required', 'Save the program before running it.')
            self.save_file_as()
            if not self.path:
                return
        if self.text.edit_modified():
            self.save_file()

        cmd = self._build_run_command(self.path)
        run_dir = os.path.dirname(self.path) or '.'
        try:
            popen_kwargs = {}
            if sys.platform.startswith('win') and not self.pygame_var.get():
                popen_kwargs['creationflags'] = subprocess.CREATE_NEW_CONSOLE
            self._run_proc = subprocess.Popen(cmd, cwd=run_dir, **popen_kwargs)
        except OSError as exc:
            messagebox.showerror('Run failed', str(exc))
            return
        self.status_var.set('Running: ' + ' '.join(cmd))

    def _build_run_command(self, path: str) -> List[str]:
        cmd = [sys.executable, '-m', 'mini_basic', path]
        dialect = self.dialect_var.get()
        if dialect and dialect != 'auto':
            cmd += ['--dialect', dialect]
        if self.pygame_var.get():
            cmd.append('--pygame')
        return cmd


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else None

    root = tk.Tk()
    EditorWindow(root, path)
    root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
