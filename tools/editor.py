"""A minimal tkinter source editor for mini_basic ``.bas``/``.bbc`` programs.

Scope (intentionally small; grown from a first pass towards a fuller tool):
  * Open/Save/Save As for BASIC source files.
  * mini_basic-aware syntax highlighting (keywords, PROC/ENDPROC/FN,
    ``*``-commands, line numbers, dialect hint comments).
  * A "Run" action that launches the *real* interpreter as a subprocess
    (``python -m mini_basic <file>``), the same way it is normally run
    from a shell. This editor does not reimplement any display: pygame
    graphics programs still open their own pygame window, and console
    programs still use the ANSI terminal the interpreter already uses.
  * A **Listener** pane (bottom, resizable), lispy3-machine-style: a
    persistent in-process interpreter you can type statements into and
    get results back immediately, without any line numbers, ``AUTO``, or
    line-targeted ``EDIT`` -- the natural style for the unnumbered
    ``mini`` dialect. ``F5`` evaluates the line at the cursor in the
    editor buffer there; ``Shift+F5`` evaluates the current selection
    (a full ``DEF PROC``/``DEF FN`` ... ``ENDPROC``/``END DEF`` block
    included). Every evaluation goes through the same unmodified
    ``mini_basic.runtime`` REPL dispatch used by the command-line REPL
    (``_execute_repl_line``) -- this pane only drives it.

No in-editor graphics/terminal pane for running whole programs: ``Run``
still launches a subprocess so pygame/console display behaves exactly as
it does from a shell. See docs/ for anything beyond this.

Usage::

    python tools/editor.py [file.bas]
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

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

_LISTENER_TAG_STYLES = {
    'echo': {'foreground': '#0033cc'},
    'result': {'foreground': '#000000'},
    'error': {'foreground': '#cc0000'},
    'info': {'foreground': '#888888', 'font': ('TkFixedFont', 10, 'italic')},
}

_LEADING_LINE_NUM_RE = re.compile(r'^\s*\d+\s*')

# Commands that drive an interactive terminal prompt loop (AUTO, bare EDIT)
# -- not representable in a GUI entry widget, and exactly what Tony asked
# the immediate pane to do without. Multi-line DEF PROC/DEF FN entry is the
# same shape (line-numbered prompt-per-line) and is handled separately: a
# whole selected block is stored directly rather than routed through here.
_LISTENER_BLOCKED_RE = re.compile(r'^(AUTO\b|EDIT\s*$)', re.IGNORECASE)


def _strip_leading_line_number(line: str) -> str:
    """Drop an optional leading ``N `` so Listener input never needs one."""
    return _LEADING_LINE_NUM_RE.sub('', line, count=1)


class _ListenerWriter(io.TextIOBase):
    """Routes interpreter ``print`` output into the Listener pane.

    Same approach as lispy3_machine's Listener writer: redirect stdout for
    the duration of each evaluation rather than patching the interpreter,
    so every native command that prints (not just one wrapped builtin)
    lands in the pane.
    """

    def __init__(self, window: 'EditorWindow') -> None:
        self.window = window

    def write(self, s: str) -> int:
        if s:
            self.window._listener_write(s, 'result')
        return len(s)

    def writable(self) -> bool:
        return True

    def flush(self) -> None:
        pass


class EditorWindow:
    def __init__(self, root: tk.Tk, path: Optional[str] = None) -> None:
        self.root = root
        self.path: Optional[str] = None
        self._highlight_job: Optional[str] = None
        self._run_proc: Optional[subprocess.Popen] = None
        self._listener_interp = None
        self._listener_history: List[str] = []
        self._listener_history_index = 0

        self._build_menu()
        self._build_widgets()

        if path:
            self._load_file(path)
        else:
            self._update_title()

        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    def _on_close(self) -> None:
        """Cancel the pending highlight debounce before destroying the window.

        Without this, a keystroke followed quickly by closing the window
        lets the 200ms ``self.root.after(200, self._highlight)`` callback
        fire after ``self.text``/``self.root`` are gone, raising a TclError
        that surfaces as a traceback right as the window closes.
        """
        if self._highlight_job is not None:
            try:
                self.root.after_cancel(self._highlight_job)
            except Exception:
                pass
            self._highlight_job = None
        if self._listener_interp is not None:
            try:
                self._listener_interp._shutdown_display(hold=False)
            except Exception:
                pass
        self.root.destroy()

    # -- UI construction -------------------------------------------------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Open...', accelerator='Ctrl+O', command=self.open_file)
        file_menu.add_command(label='Save', accelerator='Ctrl+S', command=self.save_file)
        file_menu.add_command(label='Save As...', command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self._on_close)
        menubar.add_cascade(label='File', menu=file_menu)
        self.root.config(menu=menubar)

        self.root.bind('<Control-o>', lambda _e: self.open_file())
        self.root.bind('<Control-s>', lambda _e: self.save_file())
        self.root.bind('<F5>', lambda _e: self.eval_line_at_cursor())
        self.root.bind('<Shift-F5>', lambda _e: self.eval_selection())
        self.root.bind('<Control-l>', lambda _e: self._focus_listener_entry())

    def _build_widgets(self) -> None:
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text='Run', command=self.run_program).pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(
            toolbar, text='Pretty (no numbers)', command=self.pretty_no_numbers,
        ).pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(
            toolbar, text='Renumber', command=self.renumber,
        ).pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(
            toolbar, text='Eval Line (F5)', command=self.eval_line_at_cursor,
        ).pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(
            toolbar, text='Eval Selection (Shift+F5)', command=self.eval_selection,
        ).pack(side=tk.LEFT, padx=4, pady=4)

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

        self.wait_esc_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            toolbar, text='Wait for Esc at end of run', variable=self.wait_esc_var,
        ).pack(side=tk.LEFT, padx=(12, 2))

        self.status_var = tk.StringVar(value='Ready')
        ttk.Label(self.root, textvariable=self.status_var, anchor='w').pack(
            side=tk.BOTTOM, fill=tk.X,
        )

        paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        text_frame = ttk.Frame(paned)

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
        paned.add(text_frame, weight=3)

        self._build_listener(paned)
        paned.add(self.listener_frame, weight=1)

    def _build_listener(self, parent: tk.Widget) -> None:
        """A persistent Listener pane: type a statement, press Enter, see the result.

        Backed by the same ``_execute_repl_line`` dispatch as the command-line
        REPL (imported lazily in ``_get_listener_interp``), so this never
        reimplements parsing or execution -- it only drives the interpreter
        and shows what it prints.
        """
        self.listener_frame = ttk.Frame(parent)

        listener_toolbar = ttk.Frame(self.listener_frame)
        listener_toolbar.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(listener_toolbar, text='Listener (immediate mode)').pack(
            side=tk.LEFT, padx=4,
        )
        ttk.Button(
            listener_toolbar, text='Reset', command=self._reset_listener,
        ).pack(side=tk.RIGHT, padx=4, pady=2)

        output_frame = ttk.Frame(self.listener_frame)
        output_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.listener_output = tk.Text(
            output_frame, height=8, wrap='word', state='disabled',
            font=('TkFixedFont', 10),
        )
        listener_scroll = ttk.Scrollbar(
            output_frame, orient='vertical', command=self.listener_output.yview,
        )
        self.listener_output.configure(yscrollcommand=listener_scroll.set)
        self.listener_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        listener_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        for tag, style in _LISTENER_TAG_STYLES.items():
            self.listener_output.tag_configure(tag, **style)

        entry_row = ttk.Frame(self.listener_frame)
        entry_row.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(entry_row, text='>').pack(side=tk.LEFT, padx=(4, 2))
        self.listener_entry = ttk.Entry(entry_row, font=('TkFixedFont', 10))
        self.listener_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), pady=4,
        )
        self.listener_entry.bind('<Return>', self._listener_submit)
        self.listener_entry.bind('<Up>', self._listener_history_prev)
        self.listener_entry.bind('<Down>', self._listener_history_next)

    # -- File handling -----------------------------------------------------

    def open_file(self) -> None:
        path = filedialog.askopenfilename(
            title='Open BASIC program',
            filetypes=[('BASIC source', '*.bas *.bbc *.txt'), ('All files', '*.*')],
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str) -> None:
        if os.path.splitext(path)[1].lower() == '.bbc':
            self._load_tokenized_bbc(path)
            return
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
        self._highlight()
        self._update_title()
        self.status_var.set(f'Opened {path}')

    def _load_tokenized_bbc(self, path: str) -> None:
        """Open a tokenized BBC BASIC program, detokenized into editable text.

        Reuses the interpreter's own ``LOAD`` (which already detects and
        detokenizes Wilson/Russell-format tokenized binaries) plus the same
        ``LIST`` formatting the REPL uses, so this is not a reimplementation
        of detokenization. The ``.bbc`` extension is reserved for tokenized
        programs, so the result is left untitled: Save As targets a new
        ``.bas`` (plain-text) file rather than overwriting the binary.
        """
        interp = self._make_interpreter()
        err_buf = io.StringIO()
        try:
            with contextlib.redirect_stderr(err_buf):
                ok = interp.load(path, announce=False)
            if not ok:
                raise ValueError(err_buf.getvalue().strip() or 'Could not load program')
        except (ValueError, OSError) as exc:
            messagebox.showerror('Open failed', str(exc))
            return
        lines = interp._program_display_lines(
            'standard', include_line_numbers=True, case_fold=interp._detokenize_fold(),
        )
        self.path = None
        self._replace_text('\n'.join(lines) + '\n')
        self._update_title()
        self.status_var.set(f'Detokenized {path} - use Save As to save as .bas text')

    def save_file(self) -> None:
        if not self.path:
            self.save_file_as()
            return
        self._write_to(self.path)

    def save_file_as(self) -> None:
        path = filedialog.asksaveasfilename(
            title='Save BASIC program',
            defaultextension='.bas',
            filetypes=[('BASIC source', '*.bas *.txt'), ('All files', '*.*')],
        )
        if path and self._write_to(path):
            self.path = path
            self._update_title()

    def _write_to(self, path: str) -> bool:
        if os.path.splitext(path)[1].lower() == '.bbc':
            messagebox.showerror('Save failed', '.bbc is reserved for tokenized programs. Save editable text as .bas.')
            return False
        content = self.text.get('1.0', 'end-1c')
        try:
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(content)
        except OSError as exc:
            messagebox.showerror('Save failed', str(exc))
            return False
        self.text.edit_modified(False)
        self.status_var.set(f'Saved {path}')
        return True

    def _update_title(self) -> None:
        name = self.path or '(untitled)'
        self.root.title(f'mini_basic editor - {name}')

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

    # -- Pretty / Renumber -------------------------------------------------

    def _make_interpreter(self):
        """Build a fresh interpreter honoring the toolbar's dialect choice."""
        from mini_basic.config import InterpreterConfig
        from mini_basic.runtime import BASICInterpreter

        config = InterpreterConfig()
        dialect = self.dialect_var.get()
        if dialect and dialect != 'auto':
            config.dialect = dialect
            config.dialect_locked = True
        return BASICInterpreter(config)

    def _parse_source(self):
        """Load the editor's current text into a fresh interpreter.

        Reuses the real interpreter's own LOAD so tokenizing, dialect
        detection and numbered/unnumbered sniffing behave exactly as they
        do for ``mini_basic file.bas`` (no reimplemented parsing here).
        """
        interp = self._make_interpreter()

        source = self.text.get('1.0', 'end-1c')
        fd, tmp_path = tempfile.mkstemp(suffix='.bas')
        os.close(fd)
        try:
            with open(tmp_path, 'w', encoding='utf-8') as fh:
                fh.write(source)
            err_buf = io.StringIO()
            with contextlib.redirect_stderr(err_buf):
                ok = interp.load(tmp_path, announce=False)
            if not ok:
                raise ValueError(err_buf.getvalue().strip() or 'Could not parse program')
        finally:
            os.remove(tmp_path)
        if not interp.program:
            raise ValueError('No program lines found')
        return interp

    def _replace_text(self, content: str) -> None:
        self.text.delete('1.0', tk.END)
        self.text.insert('1.0', content)
        self.text.edit_modified(True)
        self._highlight()

    def pretty_no_numbers(self) -> None:
        """Reformat the buffer as structural-indent source with no line numbers.

        Same presentation as ``SAVE PRETTY`` / ``LIST PRETTY`` in the REPL.
        """
        try:
            interp = self._parse_source()
            interp._apply_structural_indents()
            lines = interp._program_display_lines(
                'pretty', include_line_numbers=False, case_fold=interp._detokenize_fold(),
            )
        except ValueError as exc:
            messagebox.showerror('Pretty failed', str(exc))
            return
        self._replace_text('\n'.join(lines) + '\n')
        self.status_var.set('Prettified (line numbers removed)')

    def renumber(self) -> None:
        """Renumber the program 10, 20, 30, ... fixing up GOTO/GOSUB/etc targets.

        Delegates to the interpreter's own ``RENUMBER``/``REN`` logic.
        """
        try:
            interp = self._parse_source()
            interp.renumber_program(10, 10)
            case_fold = interp._detokenize_fold()
            lines = [
                f'{interp._format_line_number(num, True)}'
                f'{" " * interp.line_indent.get(num, 0)}'
                f'{interp.format_list_line(interp.program[num])}'
                for num in sorted(interp.program)
            ]
        except ValueError as exc:
            messagebox.showerror('Renumber failed', str(exc))
            return
        self._replace_text('\n'.join(lines) + '\n')
        self.status_var.set('Renumbered')

    # -- Listener (immediate mode) ---------------------------------------

    def _get_listener_interp(self):
        """The Listener's persistent interpreter, created on first use.

        Shares ``_make_interpreter``'s dialect choice with Run/Pretty/
        Renumber. State (variables, DEF PROC/FN, the program being built)
        lives here across evaluations until Reset.
        """
        if self._listener_interp is None:
            self._listener_interp = self._make_interpreter()
            self._listener_write(
                f'New {self.dialect_var.get()} session.\n', 'info',
            )
        return self._listener_interp

    def _reset_listener(self) -> None:
        if self._listener_interp is not None:
            try:
                self._listener_interp._shutdown_display(hold=False)
            except Exception:
                pass
        self._listener_interp = None
        self.listener_output.configure(state='normal')
        self.listener_output.delete('1.0', tk.END)
        self.listener_output.configure(state='disabled')
        self._get_listener_interp()

    def _listener_write(self, text: str, tag: str = 'result') -> None:
        self.listener_output.configure(state='normal')
        self.listener_output.insert(tk.END, text, tag)
        self.listener_output.see(tk.END)
        self.listener_output.configure(state='disabled')

    def _focus_listener_entry(self) -> None:
        self.listener_entry.focus_set()

    def _listener_execute(self, text: str) -> None:
        """Run one line through the real REPL dispatch, output into the pane."""
        interp = self._get_listener_interp()
        stripped = text.strip()
        if not stripped:
            return
        if _LISTENER_BLOCKED_RE.match(stripped):
            self._listener_write(
                'AUTO and bare EDIT need a real terminal prompt loop and are '
                'not available here -- type or paste statements directly, or '
                'select a DEF PROC/DEF FN block and use Eval Selection.\n',
                'error',
            )
            return
        if interp._classify_multiline_def_start(stripped) is not None:
            self._listener_write(
                'This starts a multi-line DEF PROC/DEF FN -- select the whole '
                'block (through ENDPROC/END DEF) and use Eval Selection.\n',
                'error',
            )
            return
        from mini_basic.runtime import _execute_repl_line

        writer = _ListenerWriter(self)
        try:
            with contextlib.redirect_stdout(writer):
                _execute_repl_line(interp, stripped)
        except Exception as exc:
            self._listener_write(f'Error: {exc}\n', 'error')

    def _eval_multiline_def_block(self, interp, lines: List[str]) -> bool:
        """Store a selected DEF PROC/DEF FN ... ENDPROC/END DEF block directly.

        Mirrors what the interpreter's own ``_auto_entry_loop`` does one
        line at a time from a terminal prompt, except the Listener already
        has every line of the block at once, so no interactive loop (and no
        line numbers typed by hand) is needed.
        """
        if not lines:
            return False
        kind = interp._classify_multiline_def_start(lines[0])
        if kind is None:
            return False
        step = 10
        line_num = interp._next_auto_line_start(step)
        for raw in lines:
            text = raw.strip()
            if not text:
                continue
            stored_num, statement = interp._parse_auto_line(line_num, text)
            indent, statement = interp._preserve_or_parse_indent(
                stored_num, statement, fallback_line=line_num,
            )
            interp.set_program_line(stored_num, statement, indent)
            line_num = stored_num + step
        interp._ensure_definitions_current()
        kind_label = 'DEF PROC' if kind == 'proc' else 'DEF FN'
        self._listener_write(f'{kind_label} defined.\n', 'info')
        return True

    def _run_in_listener(self, text: str) -> None:
        interp = self._get_listener_interp()
        raw_lines = [_strip_leading_line_number(ln) for ln in text.splitlines() if ln.strip()]
        if not raw_lines:
            return
        if len(raw_lines) > 1 and interp._classify_multiline_def_start(raw_lines[0]) is not None:
            preview = '\n'.join(raw_lines)
            self._listener_write(f'> {preview}\n', 'echo')
            try:
                if self._eval_multiline_def_block(interp, raw_lines):
                    self._focus_listener_entry()
                    return
            except Exception as exc:
                self._listener_write(f'Error: {exc}\n', 'error')
                self._focus_listener_entry()
                return
        for line in raw_lines:
            self._listener_write(f'> {line}\n', 'echo')
            self._listener_execute(line)
        self._focus_listener_entry()

    def _listener_submit(self, _event: object = None) -> str:
        text = self.listener_entry.get()
        self.listener_entry.delete(0, tk.END)
        if text.strip():
            self._listener_history.append(text)
            self._listener_history_index = len(self._listener_history)
            self._listener_write(f'> {text}\n', 'echo')
            self._listener_execute(text)
        return 'break'

    def _set_listener_entry(self, text: str) -> None:
        self.listener_entry.delete(0, tk.END)
        self.listener_entry.insert(0, text)

    def _listener_history_prev(self, _event: object = None) -> str:
        if self._listener_history:
            self._listener_history_index = max(0, self._listener_history_index - 1)
            self._set_listener_entry(self._listener_history[self._listener_history_index])
        return 'break'

    def _listener_history_next(self, _event: object = None) -> str:
        if self._listener_history:
            self._listener_history_index = min(
                len(self._listener_history), self._listener_history_index + 1,
            )
            if self._listener_history_index == len(self._listener_history):
                self._set_listener_entry('')
            else:
                self._set_listener_entry(self._listener_history[self._listener_history_index])
        return 'break'

    def eval_line_at_cursor(self) -> None:
        """F5: evaluate the editor line under the cursor in the Listener."""
        line = self.text.get('insert linestart', 'insert lineend')
        self._run_in_listener(line)

    def eval_selection(self) -> None:
        """Shift+F5: evaluate the current selection (or the cursor's line)."""
        try:
            selection = self.text.get('sel.first', 'sel.last')
        except tk.TclError:
            self.eval_line_at_cursor()
            return
        self._run_in_listener(selection)

    def _build_run_command(self, path: str) -> List[str]:
        cmd = [sys.executable, '-m', 'mini_basic', path]
        dialect = self.dialect_var.get()
        if dialect and dialect != 'auto':
            cmd += ['--dialect', dialect]
        if self.pygame_var.get():
            cmd.append('--pygame')
        cmd.append('--hold' if self.wait_esc_var.get() else '--no-hold')
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
