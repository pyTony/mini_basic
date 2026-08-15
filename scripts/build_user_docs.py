"""Build browsable HTML next to docs/site/ from selected Markdown files.

Run from the repo root:

    python scripts/build_user_docs.py
"""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
SITE = DOCS / 'site'

PAGES = [
    ('LANGUAGE_FEATURES_1.00.md', 'Language features (1.00)'),
    ('RELEASE_1.00.md', 'Release 1.00'),
    ('MITS_IMPLEMENTATION.md', 'MITS implementation'),
    ('PACKAGING.md', 'Packaging'),
    ('LLM.md', 'Notes for people and LLMs'),
    ('BASIC_VARIANTS.md', 'BASIC variants'),
    ('INDEX.md', 'Markdown index', 'markdown-index.html'),
]

NAV = '''    <nav>
      <a href="index.html">Home</a>
      <a href="install.html">Install</a>
      <a href="tree.html">Public tree</a>
      <a href="LANGUAGE_FEATURES_1.00.html">Language</a>
      <a href="https://github.com/pyTony/mini_basic">GitHub</a>
    </nav>'''


def convert_md(text: str) -> str:
    text = text.replace('\r\n', '\n')
    chunks: list[str] = []
    i = 0
    lines = text.split('\n')
    n = len(lines)

    def flush_para(buf: list[str]) -> None:
        if buf:
            chunks.append('<p>' + inline(' '.join(buf)) + '</p>')
            buf.clear()

    para: list[str] = []
    while i < n:
        line = lines[i]
        if line.startswith('```'):
            flush_para(para)
            i += 1
            body: list[str] = []
            while i < n and not lines[i].startswith('```'):
                body.append(lines[i])
                i += 1
            i += 1
            chunks.append('<pre><code>' + html.escape('\n'.join(body)) + '</code></pre>')
            continue
        if re.match(r'^\|', line) and i + 1 < n and re.match(r'^\|[\s:|-]+\|', lines[i + 1]):
            flush_para(para)
            rows = []
            while i < n and line.startswith('|'):
                cells = [c.strip() for c in line.strip('|').split('|')]
                rows.append(cells)
                i += 1
                line = lines[i] if i < n else ''
            if len(rows) >= 2:
                header, body_rows = rows[0], rows[2:]
                thead = ''.join(f'<th>{inline(c)}</th>' for c in header)
                tbody = []
                for row in body_rows:
                    tbody.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in row) + '</tr>')
                chunks.append(f'<table><tr>{thead}</tr>{"".join(tbody)}</table>')
            continue
        heading = re.match(r'^(#{1,4})\s+(.*)$', line)
        if heading:
            flush_para(para)
            level = len(heading.group(1)) + 1
            chunks.append(f'<h{level}>{inline(heading.group(2))}</h{level}>')
            i += 1
            continue
        if re.match(r'^[-*] ', line):
            flush_para(para)
            items = []
            while i < n and re.match(r'^[-*] ', lines[i]):
                items.append('<li>' + inline(lines[i][2:]) + '</li>')
                i += 1
            chunks.append('<ul>' + ''.join(items) + '</ul>')
            continue
        if re.match(r'^\d+\. ', line):
            flush_para(para)
            items = []
            while i < n and re.match(r'^\d+\. ', lines[i]):
                items.append('<li>' + inline(re.sub(r'^\d+\. ', '', lines[i])) + '</li>')
                i += 1
            chunks.append('<ol>' + ''.join(items) + '</ol>')
            continue
        if line.strip() == '---':
            flush_para(para)
            chunks.append('<hr>')
            i += 1
            continue
        if not line.strip():
            flush_para(para)
            i += 1
            continue
        para.append(line.strip())
        i += 1
    flush_para(para)
    return '\n'.join(chunks)


def inline(text: str) -> str:
    parts: list[str] = []
    pos = 0
    pattern = re.compile(
        r'`([^`]+)`|\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|\*([^*]+)\*'
    )
    for match in pattern.finditer(text):
        parts.append(html.escape(text[pos:match.start()]))
        if match.group(1) is not None:
            parts.append('<code>' + html.escape(match.group(1)) + '</code>')
        elif match.group(2) is not None:
            label, href = match.group(2), match.group(3)
            if href.endswith('.md'):
                href = Path(href).name.replace('.md', '.html')
            parts.append(f'<a href="{html.escape(href)}">{html.escape(label)}</a>')
        elif match.group(4) is not None:
            parts.append('<strong>' + html.escape(match.group(4)) + '</strong>')
        else:
            parts.append('<em>' + html.escape(match.group(5)) + '</em>')
        pos = match.end()
    parts.append(html.escape(text[pos:]))
    return ''.join(parts)


def wrap(title: str, body: str) -> str:
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} — mini_basic</title>
  <link rel="stylesheet" href="site.css">
</head>
<body>
  <header>
{NAV}
    <h1>{html.escape(title)}</h1>
    <p class="tag">Generated from the Markdown source in docs/.</p>
  </header>
  <main>
    <article>
{body}
    </article>
  </main>
  <footer>
    <a href="index.html">Home</a>
  </footer>
</body>
</html>
'''


def main() -> None:
    SITE.mkdir(parents=True, exist_ok=True)
    for item in PAGES:
        name, title = item[0], item[1]
        dest_name = item[2] if len(item) > 2 else Path(name).stem + '.html'
        src = DOCS / name
        dest = SITE / dest_name
        dest.write_text(wrap(title, convert_md(src.read_text(encoding='utf-8'))), encoding='utf-8')
        print(dest.relative_to(ROOT))


if __name__ == '__main__':
    main()
