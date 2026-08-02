"""Compare mini_basic speed with PYTHON_JIT on vs off."""
import io
import os
import re
import subprocess
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BENCH = os.path.join(_ROOT, 'test', 'corpus', 'agon', 'benchm7.bas')


def load_program() -> dict[int, str]:
    program: dict[int, str] = {}
    with open(BENCH, encoding='utf-8') as handle:
        for raw in handle:
            match = re.match(r'^\s*(\d+)\s+(.*)$', raw.rstrip())
            if match:
                program[int(match.group(1))] = match.group(2)
    return program


def run_once(jit: bool) -> float:
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    from mini_basic import BASICInterpreter, InterpreterConfig

    interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
    interp.program = load_program()
    interp._program_stdout = io.StringIO()
    start = time.perf_counter()
    interp.run()
    return time.perf_counter() - start


def run_subprocess(jit: bool, repeats: int = 3) -> list[float]:
    env = os.environ.copy()
    if jit:
        env['PYTHON_JIT'] = '1'
    else:
        env.pop('PYTHON_JIT', None)
    script = f"""
import io, os, re, sys, time
sys.path.insert(0, {repr(_ROOT)})
from mini_basic import BASICInterpreter, InterpreterConfig
program = {{}}
with open({repr(BENCH)}, encoding='utf-8') as handle:
    for raw in handle:
        match = re.match(r'^\\s*(\\d+)\\s+(.*)$', raw.rstrip())
        if match:
            program[int(match.group(1))] = match.group(2)
interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
interp.program = program
interp._program_stdout = io.StringIO()
start = time.perf_counter()
interp.run()
print(time.perf_counter() - start)
"""
    times: list[float] = []
    for _ in range(repeats):
        out = subprocess.check_output([sys.executable, '-c', script], env=env, text=True)
        times.append(float(out.strip()))
    return times


def main() -> int:
    print(f'Python: {sys.version.split()[0]}')
    for label, jit in [('JIT off', False), ('JIT on', True)]:
        times = run_subprocess(jit)
        print(f'{label}: {min(times):.4f}s best of {len(times)} ({", ".join(f"{t:.4f}" for t in times)})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())