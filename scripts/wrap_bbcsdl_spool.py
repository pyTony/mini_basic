#!/usr/bin/env python3
"""Generate an instrumented copy of a BBC program that captures PRINT output via SPOOL when run under real BBCSDL.

Usage:
  python wrap_bbcsdl_spool.py input.txt output_wrapped.bbc --spool C:/temp/out.txt

Then run the wrapped file with BBC BASIC for SDL 2.0 (set BBCSDL_EXE if it is not
in the default Windows Program Files location).

After run, inspect the spool file for the text that was PRINTed.
This is the reliable way to get comparable output from the real interpreter.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path

def make_spool_open(path: str) -> str:
    # Use a form that works even if path has backslashes: build with CHR$
    # OSCLI "SPOOL " + CHR$(34) + path + CHR$(34)
    safe = path.replace('\\', '\\\\')
    return f'OSCLI "SPOOL " + CHR$(34) + "{safe}" + CHR$(34)'

def wrap_source(original: str, spool_path: str) -> str:
    lines = []
    lines.append('REM === WRAPPED FOR SPOOL CAPTURE ===')
    lines.append('REM Original program follows after spool setup')
    lines.append(make_spool_open(spool_path))
    lines.append('ON ERROR PRINT "WRAP ERR ";REPORT$ : *SPOOL : END')

    # Append original, but ensure we close spool at end if it reaches
    orig_lines = original.splitlines()
    lines.extend(orig_lines)

    # Ensure we close spool and quit
    lines.append('')
    lines.append('*SPOOL')
    lines.append('QUIT')

    return '\n'.join(lines) + '\n'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input', help='original .txt or .bbc source')
    ap.add_argument('output', help='path for the wrapped .bbc to feed to real bbcsdl')
    ap.add_argument('--spool', default=r'C:\temp\bbc_spool.txt', help='where the real interpreter should write the spool')
    args = ap.parse_args()

    src = Path(args.input).read_text(encoding='utf-8', errors='replace')
    wrapped = wrap_source(src, args.spool)

    outp = Path(args.output)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(wrapped, encoding='ascii')

    bbcsdl = os.environ.get(
        'BBCSDL_EXE',
        r'C:\Program Files (x86)\BBC BASIC for SDL 2.0\bbcsdl.exe',
    )
    print(f'Wrote wrapped: {outp}')
    print(f'Spool target (when run under bbcsdl): {args.spool}')
    print('Run with:')
    print(f'  "{bbcsdl}" "{outp}"')
    print('Then compare the spool file content to what mini_basic --dialect bbc produced.')

if __name__ == '__main__':
    main()
