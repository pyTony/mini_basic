#!/usr/bin/env python3
"""Download BBCSDL example .txt sources into test/corpus/bbcsdl/."""
from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

INDEX_URL = 'https://www.bbcbasic.co.uk/bbcsdl/examples/index.html'
BASE_URL = 'https://www.bbcbasic.co.uk/bbcsdl/examples/'

_ROOT = Path(__file__).resolve().parents[2]
_CORPUS = _ROOT / 'test' / 'corpus' / 'bbcsdl'

# Do not reintroduce BBCSDL-only trees (IDE, Box2D, multi-channel music).
_SKIP_PATH_PREFIXES = (
    'tools/',
    'physics/',
    'sounds/',
)
# Individual demos that need SYS/network/OpenGL, not general pygame BASIC.
_SKIP_NAMES = frozenset({
    'opengl.txt',
    'world.txt',
    'teapot.txt',
    'lighting.txt',
    'pyramid.txt',
    'bbcowl.txt',
    'rubik.txt',
    'client.txt',
    'server.txt',
    'server_multi.txt',
    'lanchat.txt',
    'mysqldem.txt',
    'multitouch.txt',
    'dlgdemo.txt',
    'video.txt',
    'recorder.txt',
    'pdfdemo.txt',
})


def _should_skip(rel: str) -> bool:
    rel = rel.replace('\\', '/').lstrip('/')
    lower = rel.lower()
    if any(lower.startswith(p) for p in _SKIP_PATH_PREFIXES):
        return True
    name = Path(rel).name.lower()
    return name in _SKIP_NAMES


def _fetch(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'mini_basic-corpus-fetch/1.0'},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode('utf-8', errors='replace')


def _discover_txt_links(index_html: str) -> list[str]:
    links = set(re.findall(r'href="([^"]+\.txt)"', index_html, re.IGNORECASE))
    normalized: list[str] = []
    for link in sorted(links):
        link = link.replace('\\', '/').lstrip('/')
        if link.startswith('http'):
            normalized.append(link)
        else:
            normalized.append(BASE_URL + link)
    return normalized


def main() -> int:
    _CORPUS.mkdir(parents=True, exist_ok=True)
    print(f'Fetching index: {INDEX_URL}')
    try:
        index_html = _fetch(INDEX_URL)
    except urllib.error.URLError as exc:
        print(f'Failed to fetch index: {exc}', file=sys.stderr)
        return 1

    links = _discover_txt_links(index_html)
    print(f'Found {len(links)} example files')

    ok = 0
    skipped = 0
    failed: list[str] = []
    for url in links:
        rel = url.split('/examples/', 1)[-1]
        if _should_skip(rel):
            skipped += 1
            continue
        dest = _CORPUS / rel.replace('/', '\\')
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_file() and dest.stat().st_size > 0:
            ok += 1
            continue
        try:
            text = _fetch(url)
            dest.write_text(text, encoding='utf-8')
            ok += 1
            print(f'  {rel}')
        except urllib.error.URLError as exc:
            failed.append(f'{rel}: {exc}')
            print(f'  FAIL {rel}: {exc}', file=sys.stderr)

    print(f'Done: {ok} kept, {skipped} skipped (SDL-only), {len(failed)} fail; root {_CORPUS}')
    if failed:
        print(f'{len(failed)} failures', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())