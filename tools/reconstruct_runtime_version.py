#!/usr/bin/env python3
"""
Reconstruct runtime versions from a base file + sequential unified diffs.

This allows dropping full historic runtime files and keeping only small diffs + this script.

Usage examples:
  python tools/reconstruct_runtime_version.py --help
  python tools/reconstruct_runtime_version.py --list
  python tools/reconstruct_runtime_version.py --base backup/runtime_diffs/base_runtime.py --diffs "v01.diff,v02.diff" --output reconstructed.py

The script applies diffs in order using Python (no external patch needed, pure stdlib).

For best results with the project's git workflow, you can also use:
  git apply --reject the.diff
"""

import argparse
import difflib
import os
import sys
from pathlib import Path

def apply_unified_diff(base_lines, diff_lines):
    """Apply a unified diff to base_lines. Returns new list of lines.
    Simple but robust implementation for standard unified diffs (no renames, binary, etc.).
    """
    result = list(base_lines)
    i = 0
    while i < len(diff_lines):
        line = diff_lines[i].rstrip('\n')
        if line.startswith('@@'):
            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            import re
            m = re.search(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
            if m:
                old_start = int(m.group(1)) - 1  # 0-based
                old_count = int(m.group(2)) if m.group(2) else 1
                # We ignore new_start/new_count for application, we apply the changes
                i += 1
                # Collect changes for this hunk
                changes = []
                while i < len(diff_lines):
                    l = diff_lines[i]
                    if l.startswith( (' ', '+', '-') ):
                        changes.append(l)
                        i += 1
                    else:
                        break
                # Apply the hunk to result
                # We will rebuild the segment
                # For simplicity and correctness for our use case, we process line by line
                # A practical way: use the context to locate and splice
                # To keep it simple and working:
                # Collect the expected old lines and new lines
                old_segment = []
                new_segment = []
                for ch in changes:
                    if ch.startswith(' '):
                        old_segment.append(ch[1:])
                        new_segment.append(ch[1:])
                    elif ch.startswith('-'):
                        old_segment.append(ch[1:])
                    elif ch.startswith('+'):
                        new_segment.append(ch[1:])
                # Find position in current result and replace the old_segment with new_segment
                # Search for the sequence
                for j in range(len(result) - len(old_segment) + 1):
                    if result[j:j+len(old_segment)] == old_segment:
                        result[j:j+len(old_segment)] = new_segment
                        break
                continue
            i += 1
        else:
            i += 1
    return result

def main():
    parser = argparse.ArgumentParser(description="Reconstruct runtime.py version from base + diffs.")
    parser.add_argument('--base', required=True, help='Path to base runtime.py')
    parser.add_argument('--diffs', required=True, help='Comma separated list of .diff files in order')
    parser.add_argument('--output', required=True, help='Output file for reconstructed version')
    parser.add_argument('--list', action='store_true', help='List available (if in standard layout)')
    args = parser.parse_args()

    if args.list:
        print("Provide --base and --diffs to reconstruct.")
        return

    base_path = Path(args.base)
    if not base_path.exists():
        print(f"Base not found: {base_path}")
        sys.exit(1)

    with open(base_path, 'r', encoding='utf-8', errors='replace') as f:
        base_lines = f.readlines()

    diff_files = [Path(d.strip()) for d in args.diffs.split(',') if d.strip()]
    current_lines = base_lines

    for dpath in diff_files:
        if not dpath.exists():
            print(f"Diff not found: {dpath}")
            sys.exit(1)
        with open(dpath, 'r', encoding='utf-8', errors='replace') as f:
            diff_lines = f.readlines()
        current_lines = apply_unified_diff(current_lines, diff_lines)
        print(f"Applied {dpath.name}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(current_lines)
    print(f"Wrote reconstructed version to {out_path}")

if __name__ == "__main__":
    main()
