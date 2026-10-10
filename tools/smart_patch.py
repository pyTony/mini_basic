#!/usr/bin/env python3
"""
smart_patch.py - Better way to edit large files (especially runtime.py) from LLM output.

Problems it solves:
- Copy-pasting huge functions in IDLE often messes up indentation.
- LLMs often return a function/method with wrong (or zero) indentation.
- You need to safely replace an entire function or method, whether top-level or inside a class.

Main recommended command for your use case:

    python tools/smart_patch.py replace-function mini_basic/runtime.py \
        --find "_expand_builtin_calls" \
        --new-file /tmp/new_func.py

    # or with a partial signature
    python tools/smart_patch.py replace-function mini_basic/runtime.py \
        --find "def _expand_builtin_calls(self, expr: str)" \
        --new-file /tmp/new_func.py

    # dry-run first (highly recommended)
    python tools/smart_patch.py replace-function mini_basic/runtime.py \
        --find "_expand_builtin_calls" --new-file /tmp/new_func.py --dry-run

It will:
- Locate the old def (works for methods inside classes too)
- Take your new code (even if it has wrong indent level)
- Re-indent the whole replacement so the 'def' line matches the original indent
- Replace the complete old function body

Other commands still available:
    python tools/smart_patch.py replace ...          (general context block)
    python tools/smart_patch.py diff old.py new.py
    python tools/smart_patch.py apply target.py patch.txt
"""

import argparse
import difflib
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def find_block_with_context(lines: List[str], context: str, context_lines: int = 2) -> Optional[tuple]:
    """
    Find the best matching block using surrounding context.
    Returns (start_idx, end_idx) or None.
    """
    ctx_lines = context.strip().splitlines()
    if not ctx_lines:
        return None

    for i in range(len(lines)):
        # Try to match the anchor line
        if ctx_lines[0] in lines[i]:
            # Check surrounding context
            match = True
            for j, cl in enumerate(ctx_lines):
                idx = i + j
                if idx >= len(lines) or cl.strip() not in lines[idx].strip():
                    match = False
                    break
            if match:
                # Extend to a reasonable function/block if possible
                start = max(0, i - context_lines)
                end = i + len(ctx_lines) + context_lines
                # Try to find a better end (next def or blank heavy area)
                for k in range(end, min(len(lines), end + 30)):
                    if lines[k].startswith('def ') or lines[k].startswith('class '):
                        end = k
                        break
                    if k > end + 5 and not lines[k].strip():
                        end = k
                        break
                return start, min(end, len(lines))
    return None


def replace_block(target_path: Path, old_snippet: str, new_snippet: str, context_lines: int = 3, dry_run=False):
    """
    Replace the region in target that best matches old_snippet with new_snippet.
    Preserves exact new_snippet as provided (including its indentation).
    """
    text = target_path.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)

    # Try exact match first
    if old_snippet in text:
        new_text = text.replace(old_snippet, new_snippet, 1)
        if not dry_run:
            target_path.write_text(new_text, encoding='utf-8')
        print(f"Exact match replaced in {target_path}")
        return True

    # Context search
    block = find_block_with_context(lines, old_snippet, context_lines)
    if not block:
        print("ERROR: Could not locate the block uniquely by context.", file=sys.stderr)
        print("Try providing more unique surrounding lines in --before / old_snippet.", file=sys.stderr)
        return False

    start, end = block
    before = ''.join(lines[:start])
    after = ''.join(lines[end:])
    new_text = before + new_snippet + after

    if not dry_run:
        target_path.write_text(new_text, encoding='utf-8')
    print(f"Context block replaced (lines ~{start}-{end}) in {target_path}")
    return True


# ===================== NEW: Function/Method replace with auto-indent fix =====================

def find_function_block(lines: List[str], find_str: str) -> Optional[Tuple[int, int, int]]:
    """
    Find a function or method definition.
    Returns (start_line_index, end_line_index, def_line_indent) or None.
    Works for both top-level functions and methods inside classes.
    """
    find_str = find_str.strip()
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        # Match lines that look like def, containing the find string
        if stripped.startswith('def ') and find_str in stripped:
            def_indent = len(line) - len(line.lstrip())
            # Now walk forward to find where this block ends
            j = i + 1
            while j < len(lines):
                l = lines[j]
                l_stripped = l.strip()
                if not l_stripped or l_stripped.startswith('#'):
                    j += 1
                    continue
                l_indent = len(l) - len(l.lstrip())
                if l_indent <= def_indent:
                    # next sibling or dedent -> end of this function
                    break
                j += 1
            return i, j, def_indent
    return None


def reindent_code(new_code: str, target_def_indent: int) -> str:
    """
    Take new function/method code (which may be provided with wrong indentation,
    e.g. dedented to column 0, or indented as if it was inside a class already)
    and re-indent the entire block so the 'def' line ends up at target_def_indent.
    Inner indentation is preserved relatively.
    """
    if not new_code.strip():
        return new_code

    lines = new_code.splitlines(keepends=True)

    # Find the actual indent of non-blank lines
    indents = []
    for line in lines:
        if line.strip():
            indents.append(len(line) - len(line.lstrip()))

    if not indents:
        return new_code

    min_indent = min(indents)

    result_lines = []
    for line in lines:
        if not line.strip():
            result_lines.append(line)  # keep blank lines exactly
            continue

        current_indent = len(line) - len(line.lstrip())
        # Remove the original common indent, then add the target one
        relative = current_indent - min_indent
        new_indent = target_def_indent + relative
        new_line = ' ' * max(0, new_indent) + line.lstrip()
        result_lines.append(new_line)

    return ''.join(result_lines)


def replace_function(target_path: Path, find_str: str, new_code: str, dry_run: bool = False) -> bool:
    """
    Replace the entire function/method (top-level or inside class) whose def line
    contains `find_str` with the provided new_code.

    The new_code may have wrong indentation — it will be automatically fixed
    to match the indentation level of the original def line.
    """
    text = target_path.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)

    block = find_function_block(lines, find_str)
    if not block:
        print(f"ERROR: Could not find a 'def' line containing: {find_str}", file=sys.stderr)
        print("Try a more unique part of the signature, e.g. 'def _my_func(self, arg)'", file=sys.stderr)
        return False

    start, end, def_indent = block

    # Re-indent the new code to the correct level
    corrected_new = reindent_code(new_code, def_indent)

    # Build new file content
    before = ''.join(lines[:start])
    after = ''.join(lines[end:])
    new_text = before + corrected_new + after

    if not dry_run:
        target_path.write_text(new_text, encoding='utf-8')

    # Show what we matched
    old_sig = lines[start].rstrip()
    print(f"Replaced function/method starting at line {start+1}:")
    print(f"  Old: {old_sig}")
    print(f"  New indent level: {def_indent} spaces")
    print(f"  Written to {target_path}" if not dry_run else "  (dry-run, not written)")
    return True



def apply_unified_patch(target_path: Path, patch_text: str, dry_run=False):
    """Very basic unified diff applier. Not as robust as GNU patch but pure Python."""
    # For simplicity we support only simple cases.
    # Better to recommend the context replace for LLM use.
    print("Note: unified patch apply is basic. Prefer the 'replace' mode for complex edits.")
    # TODO: could integrate a real pure-python patch library, but keep deps zero.
    # For now fall back to suggestion.
    print("For best results on big files, use the context replace mode instead.")


def main():
    parser = argparse.ArgumentParser(description="Smart patcher that respects indentation.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # replace command (general context replace)
    p_rep = sub.add_parser("replace", help="Replace a section using context or snippets")
    p_rep.add_argument("target", help="File to modify (e.g. mini_basic/runtime.py)")
    p_rep.add_argument("--before", help="Unique text (or first few lines) that identifies the old block")
    p_rep.add_argument("--after", help="New text to insert (exact, with desired indentation)")
    p_rep.add_argument("--old-snippet", type=Path, help="File containing the old block to find")
    p_rep.add_argument("--new-snippet", type=Path, help="File containing the replacement")
    p_rep.add_argument("--context-lines", type=int, default=3)
    p_rep.add_argument("--dry-run", action="store_true")

    # NEW: dedicated function/method replacer (handles wrong indentation from LLM)
    p_func = sub.add_parser("replace-function", help="Replace a whole function or method (top-level or in class). Auto-fixes indentation level of the replacement.")
    p_func.add_argument("target", help="File to modify (usually mini_basic/runtime.py)")
    p_func.add_argument("--find", required=True, help="String to find in the 'def ' line, e.g. '_expand_builtin_calls' or 'def _foo(self,'")
    p_func.add_argument("--new-file", type=Path, help="File containing the full new function/method code (recommended)")
    p_func.add_argument("--new-code", help="The new function/method code as a string (use for small ones or stdin)")
    p_func.add_argument("--dry-run", action="store_true")

    # diff command
    p_diff = sub.add_parser("diff", help="Generate a simple patch")
    p_diff.add_argument("old", type=Path)
    p_diff.add_argument("new", type=Path)
    p_diff.add_argument("-o", "--output", type=Path)

    # apply command
    p_app = sub.add_parser("apply", help="Apply a previously generated patch")
    p_app.add_argument("target", type=Path)
    p_app.add_argument("patch", type=Path)
    p_app.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.cmd == "replace":
        target = Path(args.target)
        if not target.exists():
            print(f"File not found: {target}", file=sys.stderr)
            sys.exit(1)

        if args.old_snippet and args.new_snippet:
            old = args.old_snippet.read_text(encoding='utf-8')
            new = args.new_snippet.read_text(encoding='utf-8')
        elif args.before and args.after:
            old = args.before
            new = args.after
        else:
            print("You must provide either --before + --after or --old-snippet + --new-snippet")
            sys.exit(1)

        ok = replace_block(target, old, new, args.context_lines, dry_run=args.dry_run)
        if not ok:
            sys.exit(2)

    elif args.cmd == "replace-function":
        target = Path(args.target)
        if not target.exists():
            print(f"File not found: {target}", file=sys.stderr)
            sys.exit(1)

        if args.new_file:
            new_code = args.new_file.read_text(encoding='utf-8')
        elif args.new_code:
            new_code = args.new_code
        else:
            print("You must provide either --new-file or --new-code for the replacement function")
            sys.exit(1)

        ok = replace_function(target, args.find, new_code, dry_run=args.dry_run)
        if not ok:
            sys.exit(2)

    elif args.cmd == "diff":
        old = args.old.read_text(encoding='utf-8').splitlines(keepends=True)
        new = args.new.read_text(encoding='utf-8').splitlines(keepends=True)
        diff = difflib.unified_diff(old, new, fromfile=str(args.old), tofile=str(args.new))
        out = ''.join(diff)
        if args.output:
            args.output.write_text(out, encoding='utf-8')
            print(f"Patch written to {args.output}")
        else:
            print(out)

    elif args.cmd == "apply":
        patch_text = args.patch.read_text(encoding='utf-8')
        apply_unified_patch(args.target, patch_text, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
