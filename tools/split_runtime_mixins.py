#!/usr/bin/env python3
"""Split mini_basic/runtime.py monorepo into mixin modules.

Reads the live monorepo, classifies BASICInterpreter methods into mixins,
writes mixin modules under mini_basic/runtime_parts/, and emits a thin
facade runtime.py that re-exports the same public API.

Usage (from repo root):
    python tools/split_runtime_mixins.py [--dry-run] [--classify-only]
"""
from __future__ import annotations

import argparse
import ast
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SRC = ROOT / "mini_basic" / "runtime.py"
PARTS_DIR = ROOT / "mini_basic" / "runtime_parts"
BACKUP_MONO = ROOT / "backup" / "runtime_monolith.py"


# ---------------------------------------------------------------------------
# Classification rules (first match wins)
# ---------------------------------------------------------------------------

# (module_stem, list of regexes matching method name)
# Order matters: more specific first.
CLASSIFY_RULES: List[Tuple[str, List[str]]] = [
    (
        "graphics",
        [
            r"^_",  # will filter further below with sets
        ],
    ),
]

# Explicit name -> module (highest priority)
NAME_TO_MODULE: Dict[str, str] = {}

# Prefix / contains rules applied after exact map
PREFIX_RULES: List[Tuple[str, str]] = [
    # graphics / display / BBC VDU
    ("_ensure_display", "graphics"),
    ("_get_display", "graphics"),
    ("_close_display", "graphics"),
    ("_display_", "graphics"),
    ("_present_display", "graphics"),
    ("_bbc_", "graphics"),
    ("_vdu", "graphics"),
    ("_plot", "graphics"),
    ("_draw", "graphics"),
    ("_move", "graphics"),
    ("_gcol", "graphics"),
    ("_colour", "graphics"),
    ("_color", "graphics"),
    ("_mode", "graphics"),
    ("_cls", "graphics"),
    ("_clg", "graphics"),
    ("_origin", "graphics"),
    ("_rectangle", "graphics"),
    ("_circle", "graphics"),
    ("_sprite", "graphics"),
    ("_mouse", "graphics"),
    ("_sound", "graphics"),
    ("_oscli", "graphics"),
    ("_get_point", "graphics"),
    ("_set_point", "graphics"),
    ("_palette", "graphics"),
    ("_text_", "graphics"),
    ("_print_at", "graphics"),
    ("_tab", "graphics"),
    ("_width", "graphics"),
    ("_inkey", "graphics"),
    ("_get_key", "graphics"),
    ("_read_key", "graphics"),
    ("_wait", "graphics"),
    ("_beep", "graphics"),
    # definitions / procedures / functions
    ("_def_", "defs"),
    ("_call_fn", "defs"),
    ("_call_proc", "defs"),
    ("_endproc", "defs"),
    ("_end_fn", "defs"),
    ("_local", "defs"),
    ("_install", "defs"),
    ("_user_fn", "defs"),
    ("_user_proc", "defs"),
    ("_fn_", "defs"),
    ("_proc_", "defs"),
    ("_register_def", "defs"),
    ("_parse_def", "defs"),
    ("_scan_defs", "defs"),
    ("_collect_def", "defs"),
    # expressions / evaluation
    ("_eval", "expr"),
    ("_expand", "expr"),
    ("_compile_expr", "expr"),
    ("_safe_eval", "expr"),
    ("_arith", "expr"),
    ("_condition", "expr"),
    ("_cond_", "expr"),
    ("_compare", "expr"),
    ("_truth", "expr"),
    ("_coerce", "expr"),
    ("_to_number", "expr"),
    ("_to_string", "expr"),
    ("_to_int", "expr"),
    ("_parse_number", "expr"),
    ("_numeric", "expr"),
    ("_string_expr", "expr"),
    ("_builtin", "expr"),
    ("_func_", "expr"),
    ("_apply_", "expr"),
    ("_resolve_var", "expr"),
    ("_get_var", "expr"),
    ("_set_var", "expr"),
    ("_let_", "expr"),
    ("_assign", "expr"),
    ("_dim_", "expr"),
    ("_array_", "expr"),
    ("_subscript", "expr"),
    ("_index_", "expr"),
    ("_slice", "expr"),
    ("_mid", "expr"),
    ("_left", "expr"),
    ("_right", "expr"),
    ("_chr", "expr"),
    ("_asc", "expr"),
    ("_val", "expr"),
    ("_str_fn", "expr"),
    ("_instrument", "expr"),
    # I/O / files / data / print / input
    ("_print", "io"),
    ("_input", "io"),
    ("_read", "io"),
    ("_data", "io"),
    ("_restore", "io"),
    ("_open", "io"),
    ("_close", "io"),
    ("_write", "io"),
    ("_file_", "io"),
    ("_channel", "io"),
    ("_field", "io"),
    ("_get#", "io"),
    ("_put#", "io"),
    ("_using", "io"),
    ("_format_", "io"),
    ("_load", "io"),
    ("_save", "io"),
    ("_chain", "io"),
    ("_merge", "io"),
    ("_list", "io"),
    ("_renumber", "io"),
    ("_new", "io"),
    ("_clear", "io"),
    ("_report", "io"),
    ("_trace", "io"),
    ("_emit", "io"),
    ("_flush", "io"),
    ("_out", "io"),
    ("_stdin", "io"),
    ("_stdout", "io"),
    # control flow / execution
    ("_execute", "execution"),
    ("_run", "execution"),
    ("_step", "execution"),
    ("_goto", "execution"),
    ("_gosub", "execution"),
    ("_return", "execution"),
    ("_for_", "execution"),
    ("_next", "execution"),
    ("_while", "execution"),
    ("_wend", "execution"),
    ("_repeat", "execution"),
    ("_until", "execution"),
    ("_if_", "execution"),
    ("_else", "execution"),
    ("_endif", "execution"),
    ("_case", "execution"),
    ("_when", "execution"),
    ("_otherwise", "execution"),
    ("_endcase", "execution"),
    ("_break", "execution"),
    ("_continue", "execution"),
    ("_exit_", "execution"),
    ("_stop", "execution"),
    ("_end", "execution"),
    ("_resume", "execution"),
    ("_on_", "execution"),
    ("_error", "execution"),
    ("_trap", "execution"),
    ("_handle_", "execution"),
    ("_parse_cmd", "execution"),
    ("_dispatch", "execution"),
    ("_stmt", "execution"),
    ("_statement", "execution"),
    ("_do_", "execution"),
    ("_skip", "execution"),
    ("_find_", "execution"),
    ("_match_", "execution"),
    ("_split_statements", "execution"),
    ("_line_", "execution"),
    # dialect
    ("_dialect", "dialect"),
    ("_hint", "dialect"),
    ("_auto_", "dialect"),
    ("_detect", "dialect"),
    ("_compat", "dialect"),
    # program structure / parse / labels
    ("_parse", "program"),
    ("_program", "program"),
    ("_label", "program"),
    ("_add_line", "program"),
    ("_delete", "program"),
    ("_insert", "program"),
    ("_normalize", "program"),
    ("_tokenize", "program"),
    ("_scan_", "program"),
    ("_preprocess", "program"),
    ("_prepare", "program"),
    ("_build_", "program"),
    ("_index_lines", "program"),
    ("_get_line", "program"),
    ("_set_line", "program"),
    ("_indent", "program"),
    ("_cont", "program"),
    # core / state / time / options
    ("_init", "core"),
    ("_reset", "core"),
    ("_time", "core"),
    ("_option", "core"),
    ("_system", "core"),
    ("_var_kind", "core"),
    ("_kind", "core"),
    ("_default_type", "core"),
    ("_memory", "core"),
    ("_himem", "core"),
    ("_lomem", "core"),
    ("_page", "core"),
    ("_config", "core"),
    ("_clone", "core"),
    ("_copy", "core"),
    ("_state", "core"),
    ("_snapshot", "core"),
    ("_restore_state", "core"),
    ("__init__", "core"),
    ("__repr__", "core"),
    ("__str__", "core"),
]

# Fallback keywords inside name (substring)
SUBSTRING_RULES: List[Tuple[str, str]] = [
    ("display", "graphics"),
    ("graphics", "graphics"),
    ("colour", "graphics"),
    ("color", "graphics"),
    ("vdu", "graphics"),
    ("palette", "graphics"),
    ("pixel", "graphics"),
    ("sprite", "graphics"),
    ("sound", "graphics"),
    ("inkey", "graphics"),
    ("mouse", "graphics"),
    ("gcol", "graphics"),
    ("plot", "graphics"),
    ("draw_line", "graphics"),
    ("def_fn", "defs"),
    ("def_proc", "defs"),
    ("procedure", "defs"),
    ("function", "defs"),
    ("local_var", "defs"),
    ("eval", "expr"),
    ("expr", "expr"),
    ("array", "expr"),
    ("subscript", "expr"),
    ("variable", "expr"),
    ("assign", "expr"),
    ("print", "io"),
    ("input", "io"),
    ("file", "io"),
    ("channel", "io"),
    ("using", "io"),
    ("data", "io"),
    ("read_", "io"),
    ("write", "io"),
    ("load", "io"),
    ("save", "io"),
    ("list", "io"),
    ("execute", "execution"),
    ("for_loop", "execution"),
    ("gosub", "execution"),
    ("goto", "execution"),
    ("repeat", "execution"),
    ("while", "execution"),
    ("if_block", "execution"),
    ("case_block", "execution"),
    ("error", "execution"),
    ("dialect", "dialect"),
    ("label", "program"),
    ("parse", "program"),
    ("program", "program"),
    ("time", "core"),
    ("option", "core"),
]

MODULE_ORDER = [
    "core",
    "program",
    "expr",
    "defs",
    "execution",
    "io",
    "graphics",
    "dialect",
]

MODULE_DOC = {
    "core": "Core state, init, clocks, options, and shared helpers.",
    "program": "Program storage, labels, line parse, and preprocess.",
    "expr": "Expression expansion/evaluation, variables, and arrays.",
    "defs": "DEF FN / DEF PROC, LOCAL, and user callables.",
    "execution": "RUN loop, statement dispatch, and control flow.",
    "io": "PRINT/INPUT/DATA/files, LIST/SAVE/LOAD, and formatting.",
    "graphics": "Display, MODE/VDU/graphics, INKEY, sound, OSCLI.",
    "dialect": "Dialect detection and compatibility helpers.",
}


def classify_method(name: str) -> str:
    if name in NAME_TO_MODULE:
        return NAME_TO_MODULE[name]
    # longest prefix first
    for prefix, mod in sorted(PREFIX_RULES, key=lambda x: -len(x[0])):
        if name.startswith(prefix) or name == prefix.rstrip("_"):
            return mod
    low = name.lower()
    for needle, mod in SUBSTRING_RULES:
        if needle in low:
            return mod
    return "core"  # default bucket


def get_source_segment(source: str, node: ast.AST) -> str:
    """Get exact source for a node using lineno/end_lineno (3.8+)."""
    if hasattr(ast, "get_source_segment"):
        seg = ast.get_source_segment(source, node)
        if seg is not None:
            return seg
    lines = source.splitlines(keepends=True)
    start = node.lineno - 1
    end = getattr(node, "end_lineno", node.lineno)
    return "".join(lines[start:end])


def method_source_with_decorators(source: str, node: ast.FunctionDef) -> str:
    """Include decorators in the extracted method source."""
    lines = source.splitlines(keepends=True)
    if node.decorator_list:
        start = min(d.lineno for d in node.decorator_list) - 1
    else:
        start = node.lineno - 1
    end = node.end_lineno
    # Preserve original indentation (class body is typically 4 spaces)
    return "".join(lines[start:end])


def class_level_assignments(source: str, class_node: ast.ClassDef) -> List[str]:
    """Extract class body assignments and non-method statements (constants, re)."""
    lines = source.splitlines(keepends=True)
    chunks: List[str] = []
    for stmt in class_node.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        start = stmt.lineno - 1
        end = getattr(stmt, "end_lineno", stmt.lineno)
        chunks.append("".join(lines[start:end]).rstrip() + "\n")
    return chunks


def extract_module_preamble(source: str, tree: ast.Module) -> Tuple[str, int]:
    """Everything before class BASICInterpreter (imports, module constants)."""
    class_lineno = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "BASICInterpreter":
            class_lineno = node.lineno
            break
    if class_lineno is None:
        raise SystemExit("BASICInterpreter class not found")
    lines = source.splitlines(keepends=True)
    # Keep through line before class
    preamble = "".join(lines[: class_lineno - 1])
    return preamble, class_lineno


def extract_post_class(source: str, tree: ast.Module) -> str:
    """Everything after BASICInterpreter class (module-level helpers, main)."""
    class_node = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "BASICInterpreter":
            class_node = node
            break
    assert class_node is not None
    lines = source.splitlines(keepends=True)
    # Find next top-level after class
    end = class_node.end_lineno
    return "".join(lines[end:])


def dedent_method(src: str, spaces: int = 4) -> str:
    """Remove class-body indent from method source for mixin module top-level class."""
    lines = src.splitlines(keepends=True)
    out = []
    prefix = " " * spaces
    for line in lines:
        if line.startswith(prefix):
            out.append(line[spaces:])
        elif line.strip() == "":
            out.append(line if line.endswith("\n") else line + "\n")
        else:
            out.append(line)
    return "".join(out)


def indent_block(src: str, spaces: int = 4) -> str:
    """Indent every non-empty line by ``spaces`` (always; no skip-if-already)."""
    prefix = " " * spaces
    lines = []
    for line in src.splitlines(keepends=True):
        if line.strip() == "":
            lines.append("\n" if line.endswith("\n") or not line else line)
        else:
            # Always add class-body indent after dedent_method.
            lines.append(prefix + line)
    return "".join(lines)


def module_func_sources(source: str, tree: ast.Module) -> Dict[str, str]:
    """Map top-level function name -> full source text."""
    lines = source.splitlines(keepends=True)
    out: Dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            start = node.lineno - 1
            end = node.end_lineno
            out[node.name] = "".join(lines[start:end])
    return out


def method_used_module_funcs(
    class_node: ast.ClassDef, module_func_names: Set[str]
) -> Set[str]:
    """Names of module-level functions referenced as bare loads inside methods."""
    used: Set[str] = set()
    for stmt in class_node.body:
        if not isinstance(stmt, ast.FunctionDef):
            continue
        for node in ast.walk(stmt):
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id in module_func_names
            ):
                used.add(node.id)
    return used


def helper_dependency_closure(
    roots: Set[str], func_nodes: Dict[str, ast.FunctionDef]
) -> Set[str]:
    """Transitive callees among module-level functions."""
    seen: Set[str] = set()

    def walk(name: str) -> None:
        if name in seen or name not in func_nodes:
            return
        seen.add(name)
        for node in ast.walk(func_nodes[name]):
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id in func_nodes
            ):
                walk(node.id)

    for r in roots:
        walk(r)
    return seen


def build_helpers_module(
    source: str,
    tree: ast.Module,
    needed: Set[str],
    shared_imports: str,
) -> str:
    """Emit runtime_parts/helpers.py with free functions methods need."""
    func_src = module_func_sources(source, tree)
    # Minimal imports for helpers (typing + config + bbc_mode + sys)
    header = '''"""Module-level helpers shared by runtime mixins and the facade.

Auto-generated by tools/split_runtime_mixins.py.
Free functions that instance methods call by bare name live here so each
mixin module can import them into its globals.
"""
# ruff: noqa: F401,F403,F405,E402
import sys
from typing import Callable, Dict, List, Optional, Set, TextIO, Tuple

from ..config import DEFAULT_CONFIG, InterpreterConfig, SYSTEM_VAR_SPEC
from mini_basic.bbc_modes import bbc_mode_spec

'''
    parts = [header]
    # stable order by appearance in source
    order = [
        n.name
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name in needed
    ]
    for name in order:
        body = func_src[name]
        if not body.endswith("\n"):
            body += "\n"
        parts.append(body)
        parts.append("\n\n")
    return "".join(parts)


def build_mixin_file(
    module: str,
    methods: List[Tuple[str, str]],  # (name, source_with_class_indent)
    shared_imports: str,
    helper_names: List[str],
) -> str:
    doc = MODULE_DOC.get(module, "")
    class_name = f"Runtime{module.title()}Mixin"
    helper_import = ""
    if helper_names:
        names = ",\n    ".join(helper_names)
        helper_import = f"from .helpers import (\n    {names},\n)\n\n"
    parts = [
        f'"""BASICInterpreter mixin: {module}.\n\n{doc}\n\n'
        f"Auto-generated by tools/split_runtime_mixins.py — do not hand-edit bulk.\n"
        f'"""\n',
        "# ruff: noqa: F401,F403,F405,E402,W291,W293\n",
        "# Imports mirrored from monorepo runtime for method bodies.\n",
        shared_imports.rstrip() + "\n\n",
        helper_import,
        f"class {class_name}:\n",
        f'    """Mixin providing {module}-related BASICInterpreter methods."""\n\n',
    ]
    for name, src in methods:
        body = dedent_method(src, 4)
        # Package-relative imports inside methods were written for mini_basic.*
        # (from .display). Under runtime_parts they must be parent-relative.
        body = re.sub(
            r"^(\s*)from \.([A-Za-z_])",
            r"\1from ..\2",
            body,
            flags=re.MULTILINE,
        )
        body = re.sub(
            r"^(\s*)from \.(\s+import\s+)",
            r"\1from ..\2",
            body,
            flags=re.MULTILINE,
        )
        # Re-indent as class body
        indented = indent_block(body, 4)
        if not indented.endswith("\n"):
            indented += "\n"
        parts.append(indented)
        parts.append("\n")
    return "".join(parts)


def extract_imports_block(preamble: str, *, for_parts_subpackage: bool = False) -> str:
    """Return import section + needed module-level bindings for mixins.

    When ``for_parts_subpackage`` is True, rewrite package-relative imports
    from ``from .X`` / ``import .X`` to ``from ..X`` so they work under
    ``runtime_parts/``.
    """
    lines = preamble.splitlines(keepends=True)
    out: List[str] = []
    i = 0
    # skip module docstring
    if lines and (lines[0].startswith('"""') or lines[0].startswith("'''")):
        q = lines[0][:3]
        if lines[0].count(q) >= 2 and len(lines[0].strip()) > 3:
            i = 1
        else:
            i = 1
            while i < len(lines):
                if q in lines[i]:
                    i += 1
                    break
                i += 1
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    out.extend(lines[i:])
    text = "".join(out)
    if for_parts_subpackage:
        # from .foo -> from ..foo ; from . import x -> from .. import x
        # Avoid turning already-parent imports or ellipsis.
        text = re.sub(
            r"^(\s*from\s+)\.([A-Za-z_])",
            r"\1..\2",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^(\s*from\s+)\.(\s+import\s+)",
            r"\1..\2",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^(\s*import\s+)\.([A-Za-z_])",
            r"\1..\2",
            text,
            flags=re.MULTILINE,
        )
    return text


def build_facade(
    class_attrs: List[str],
    mixin_modules: List[str],
    post_class: str,
    imports: str,
) -> str:
    """Thin runtime.py: preamble imports + class with mixins + post helpers."""
    # Replace docstring
    header = '''"""mini-BASIC interpreter — runtime facade.

``BASICInterpreter`` is composed of mixins under ``runtime_parts/``.
Module-level REPL/CLI helpers and ``main`` remain in this file (extracted
from the former monorepo). The full pre-split monorepo is archived as
``backup/runtime_monolith.py``.

See ``RUNTIME_MODULARIZATION_STATUS.md`` for history.
"""
'''
    # Ensure we import mixins
    mixin_imports = []
    mixin_bases = []
    for mod in mixin_modules:
        cname = f"Runtime{mod.title()}Mixin"
        mixin_imports.append(f"from .runtime_parts.{mod} import {cname}")
        mixin_bases.append(cname)

    bases = ", ".join(mixin_bases) if mixin_bases else "object"
    class_body_attrs = "".join(
        ("    " + line if line.strip() and not line.startswith(" ") else line)
        if not line.startswith("    ")
        else line
        for chunk in class_attrs
        for line in [chunk if chunk.endswith("\n") else chunk + "\n"]
    )
    # class_attrs already include indent from source
    attr_block = ""
    for chunk in class_attrs:
        # ensure each chunk is indented with 4 spaces for class body
        for line in chunk.splitlines(keepends=True):
            if line.strip() == "":
                attr_block += "\n"
            elif line.startswith("    "):
                attr_block += line
            else:
                attr_block += "    " + line

    parts = [
        header,
        imports.rstrip() + "\n\n",
        "\n".join(mixin_imports) + "\n\n",
        f"class BASICInterpreter({bases}):\n",
        '    """BBC/mini BASIC interpreter (mixin composition)."""\n\n',
        attr_block if attr_block.strip() else "    pass\n",
        "\n",
        post_class if post_class.startswith("\n") else "\n" + post_class,
    ]
    return "".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--classify-only", action="store_true")
    ap.add_argument(
        "--source",
        type=Path,
        default=RUNTIME_SRC,
        help="Path to monorepo runtime.py",
    )
    args = ap.parse_args()
    src_path: Path = args.source
    if not src_path.is_file():
        print(f"Missing source: {src_path}", file=sys.stderr)
        return 1

    source = src_path.read_text(encoding="utf-8")
    # Quick sanity: must be monorepo size
    if len(source) < 100_000:
        print(
            f"Refusing to split: source only {len(source)} bytes "
            f"(expected monorepo ~500KB+). Restore backup first.",
            file=sys.stderr,
        )
        return 1

    tree = ast.parse(source)
    class_node: Optional[ast.ClassDef] = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "BASICInterpreter":
            class_node = node
            break
    if class_node is None:
        print("BASICInterpreter not found", file=sys.stderr)
        return 1

    methods: List[Tuple[str, ast.FunctionDef]] = []
    for stmt in class_node.body:
        if isinstance(stmt, ast.FunctionDef):
            methods.append((stmt.name, stmt))

    buckets: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    classify_counts: Dict[str, int] = defaultdict(int)
    for name, node in methods:
        mod = classify_method(name)
        classify_counts[mod] += 1
        src = method_source_with_decorators(source, node)
        buckets[mod].append((name, src))

    print(f"Methods: {len(methods)}")
    for mod in MODULE_ORDER:
        print(f"  {mod:12s} {classify_counts.get(mod, 0):4d}")
    extra = set(classify_counts) - set(MODULE_ORDER)
    for mod in sorted(extra):
        print(f"  {mod:12s} {classify_counts[mod]:4d}")

    if args.classify_only:
        # dump names
        for mod in MODULE_ORDER:
            names = [n for n, _ in buckets.get(mod, [])]
            print(f"\n=== {mod} ({len(names)}) ===")
            for n in names:
                print(f"  {n}")
        return 0

    preamble, _ = extract_module_preamble(source, tree)
    post = extract_post_class(source, tree)
    class_attrs = class_level_assignments(source, class_node)
    shared_imports = extract_imports_block(preamble, for_parts_subpackage=True)
    facade_imports = extract_imports_block(preamble, for_parts_subpackage=False)

    # Module-level free functions methods call by bare name
    func_nodes = {
        n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)
    }
    used_roots = method_used_module_funcs(class_node, set(func_nodes))
    helper_needed = helper_dependency_closure(used_roots, func_nodes)
    helper_names = [
        n.name
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name in helper_needed
    ]
    print(f"Helpers for mixins: {helper_names}")

    # Only emit modules that have methods
    active_modules = [m for m in MODULE_ORDER if buckets.get(m)]

    if args.dry_run:
        print("Dry run — would write:")
        print(f"  runtime_parts/helpers.py ({len(helper_names)} funcs)")
        for m in active_modules:
            print(f"  runtime_parts/{m}.py ({len(buckets[m])} methods)")
        print("  runtime.py (facade)")
        print(f"  backup/runtime_monolith.py")
        return 0

    # Backup monorepo if not already identical archive
    BACKUP_MONO.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP_MONO.exists() or BACKUP_MONO.stat().st_size != src_path.stat().st_size:
        shutil.copy2(src_path, BACKUP_MONO)
        print(f"Archived monorepo -> {BACKUP_MONO}")

    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    init_path = PARTS_DIR / "__init__.py"
    init_path.write_text(
        '"""Mixin parts composing BASICInterpreter (see runtime.py facade)."""\n',
        encoding="utf-8",
    )

    helpers_path = PARTS_DIR / "helpers.py"
    helpers_content = build_helpers_module(
        source, tree, helper_needed, shared_imports
    )
    helpers_path.write_text(helpers_content, encoding="utf-8")
    print(
        f"Wrote {helpers_path.relative_to(ROOT)} "
        f"({len(helper_names)} funcs, {len(helpers_content)} bytes)"
    )

    for mod in active_modules:
        path = PARTS_DIR / f"{mod}.py"
        content = build_mixin_file(
            mod, buckets[mod], shared_imports, helper_names
        )
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)} ({len(buckets[mod])} methods, {len(content)} bytes)")

    facade = build_facade(class_attrs, active_modules, post, facade_imports)
    # Write facade to runtime.py
    RUNTIME_SRC.write_text(facade, encoding="utf-8")
    print(f"Wrote facade {RUNTIME_SRC.relative_to(ROOT)} ({len(facade)} bytes)")

    # Smoke syntax check
    for mod in active_modules:
        p = PARTS_DIR / f"{mod}.py"
        ast.parse(p.read_text(encoding="utf-8"))
    ast.parse(RUNTIME_SRC.read_text(encoding="utf-8"))
    print("AST parse OK for all generated modules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
