"""List example programs that fail to load/run headless (12 s each, stdin empty).

Usage: python scripts/check_examples.py [repo_root]   (timeouts count as running)
"""
import subprocess, sys, os, re, json
from concurrent.futures import ThreadPoolExecutor
root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = []
for top in ('examples', 'basics', 'showcase'):
    for d, dirs, fs in os.walk(os.path.join(root, top)):
        dirs[:] = [x for x in dirs if x != 'm6502-cport']  # needs --dialect mits; tested in test/
        for f in fs:
            if f.lower().endswith(('.bas', '.bbc')):
                files.append(os.path.relpath(os.path.join(d, f), root))
env = dict(os.environ, PYTHONPATH=root, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
ERR = re.compile(r'Traceback.*|^\? (?!Loaded|Dialect).*|^.*(?:Unknown statement|error:).*', re.M)
def run(f):
    try:
        p = subprocess.run([sys.executable, '-m', 'mini_basic', '-q', '--display', 'none', f], cwd=root,
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=12, env=env)
        out = p.stdout + p.stderr
        m = ERR.search(out)
        status = 'ERROR' if m else 'OK'
        return f, status, p.returncode, (m.group(0)[:150].replace(root,'') if m else '')
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b'').decode(errors='replace') + (e.stderr or b'').decode(errors='replace') if isinstance(e.stdout,(bytes,type(None))) else (e.stdout or '')
        m = ERR.search(out)
        return f, ('ERROR' if m else 'TIMEOUT'), None, (m.group(0)[:150].replace(root,'') if m else '')
with ThreadPoolExecutor(8) as ex:
    res = sorted(ex.map(run, files))

from collections import Counter
print(Counter(r[1] for r in res))
for r in res:
    if r[1] == 'ERROR': print(r[0], '|', r[2], '|', r[3])
