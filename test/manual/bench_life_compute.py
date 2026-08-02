"""Compare Life: full display vs array-only (no terminal I/O)."""
import io
import os
import re
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

CORPUS = os.path.join(_ROOT, 'test', 'corpus', 'agon', 'life.bas')


def load_program():
    program = {}
    with open(CORPUS, encoding='utf-8') as handle:
        for raw in handle:
            match = re.match(r'^\s*(\d+)\s+(.*)$', raw.rstrip())
            if match:
                program[int(match.group(1))] = match.group(2)
    return program


def run_program(program, generations: int) -> float:
    program = dict(program)
    program[490] = f'IF G%>={generations} END ELSE GOTO 250'
    interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
    interp.program = program
    interp._program_stdout = io.StringIO()
    start = time.perf_counter()
    interp.run()
    return time.perf_counter() - start


def run_once(program: dict) -> float:
    interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
    interp.program = program
    interp._program_stdout = io.StringIO()
    start = time.perf_counter()
    interp.run()
    return time.perf_counter() - start


def main():
    gens = 5
    full = load_program()

    # Array only: init + neighbour compute loop; skip MODE/CLS/border/display
    compute_only = {
        k: v
        for k, v in full.items()
        if k <= 130 or k >= 350
    }
    compute_only[490] = full[490]

    full_s = run_program(full, gens)
    compute_s = run_program(compute_only, gens)

    ratio = full_s / compute_s if compute_s > 0 else float('inf')
    saved_pct = (1 - compute_s / full_s) * 100 if full_s > 0 else 0

    base = {k: v for k, v in full.items() if k <= 130}
    draw = dict(base)
    draw.update({k: v for k, v in full.items() if 150 <= k <= 345})
    draw[350] = 'END'
    compute_one = dict(base)
    compute_one.update({k: v for k, v in full.items() if 350 <= k <= 470})
    compute_one[480] = 'END'

    print(f'Grid: {full[40]} {full[50]}  |  Generations: {gens}')
    print()
    print('Per generation (StringIO — no real console):')
    print(f'  border + draw one frame:  {run_once(draw):.2f}s')
    print(f'  neighbour rules once:     {run_once(compute_one):.2f}s')
    print()
    print(f'Full ({gens} gens, display + compute):  {full_s:.2f}s  ({full_s / gens:.2f}s per gen)')
    print(f'Array only ({gens} gens, no terminal):  {compute_s:.2f}s  ({compute_s / gens:.2f}s per gen)')
    print(f'Speedup without terminal: {ratio:.1f}x  (~{saved_pct:.0f}% of time was display/flush)')


if __name__ == '__main__':
    main()