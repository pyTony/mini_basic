#!/usr/bin/env python3
"""
Improved function finder - better for test files and class methods.
"""

import argparse
import re
from pathlib import Path
from typing import List, Tuple, Optional


def is_text_file(path: Path) -> bool:
    try:
        with open(path, 'rb') as f:
            return b'\0' not in f.read(8192)
    except Exception:
        return False


def find_test_methods(root_dir: str, pattern: str, filename_part: str = ""):
    """Find test methods (def test_...) containing the pattern."""
    root = Path(root_dir).resolve()
    results = []

    regex = re.compile(rf"def\s+(test_\w*{re.escape(pattern)}\w*)", re.IGNORECASE)

    for file_path in root.rglob("test*.py"):
        if filename_part and filename_part.lower() not in file_path.name.lower():
            continue
        if not is_text_file(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for match in regex.finditer(content):
            method_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            results.append((file_path, line_num, method_name))

    return results


def main():
    parser = argparse.ArgumentParser(description="Find test methods containing a pattern")
    parser.add_argument("pattern", help="Pattern to search in test method names (e.g. animal)")
    parser.add_argument("filename_part", nargs="?", default="", help="Optional filename filter")
    parser.add_argument("-d", "--dir", default=".", help="Root directory")

    args = parser.parse_args()

    matches = find_test_methods(args.dir, args.pattern, args.filename_part)

    if not matches:
        print("No test methods found.")
        return

    print(f"Found {len(matches)} test method(s):\n")
    for file_path, line_num, method_name in matches:
        print(f"{file_path}:{line_num}  →  def {method_name}()")


if __name__ == "__main__":
    main()
