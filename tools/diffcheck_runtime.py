import difflib
import sys

old_file = sys.argv[1] if len(sys.argv) > 1 else 'runtime (1).py'
new_file = sys.argv[2] if len(sys.argv) > 2 else 'runtime.py'

with open(old_file, encoding='utf-8') as f:
    old_lines = f.readlines()
with open(new_file, encoding='utf-8') as f:
    new_lines = f.readlines()

diff = difflib.unified_diff(old_lines, new_lines, fromfile=old_file, tofile=new_file)
sys.stdout.writelines(diff)
