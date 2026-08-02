"""Run Agon BBC BASIC benchmarks via fab-agon-emulator agon-cli-emulator."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import time

EMULATOR_DIR = os.environ.get(
    'AGON_EMULATOR_DIR',
    r'C:\Users\Tony\Downloads\fab-agon-emulator-v1.2.2-windows-x64',
)
CLI = os.path.join(EMULATOR_DIR, 'agon-cli-emulator.exe')
SDCARD = os.path.join(EMULATOR_DIR, 'sdcard')
LINE_DELAY = 1.05


def run_failed(output: str) -> str | None:
    if 'Unknown packet VDU' in output:
        return (
            'agon-cli-emulator fake VDP does not implement graphics VDU codes '
            '(COLOUR, MODE, TAB, etc.). Use life28_print / life28_compute, or the GUI emulator.'
        )
    return None


def run_script(
    commands: list[str],
    unlimited_cpu: bool = False,
    timeout: float = 600.0,
    expect_timing: bool = True,
) -> str:
    args = [CLI, '--sdcard', SDCARD]
    if unlimited_cpu:
        args.append('--unlimited-cpu')

    proc = subprocess.Popen(
        args,
        cwd=EMULATOR_DIR,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None

    output_chunks: list[str] = []

    def reader() -> None:
        for line in proc.stdout:
            output_chunks.append(line)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()

    def wait_for_boot() -> None:
        deadline = time.time() + 30.0
        while time.time() < deadline:
            text = ''.join(output_chunks)
            if re.search(r'/\s*$', text) or 'MOS Version' in text:
                time.sleep(1.5)
                return
            time.sleep(0.1)
        raise RuntimeError('Timed out waiting for Agon MOS prompt')

    wait_for_boot()

    for command in commands:
        proc.stdin.write(command + '\n')
        proc.stdin.flush()
        time.sleep(LINE_DELAY)

    saw_run = False
    deadline = time.time() + timeout
    while time.time() < deadline:
        text = ''.join(output_chunks)
        if '>RUN' in text:
            saw_run = True
        failure = run_failed(text)
        if saw_run and failure:
            raise RuntimeError(failure)
        if expect_timing and extract_number(text) is not None:
            break
        if not expect_timing and saw_run and ('HELLO' in text or proc.poll() is not None):
            break
        if proc.poll() is not None:
            break
        time.sleep(0.2)

    proc.stdin.close()
    try:
        proc.wait(timeout=10.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    return ''.join(output_chunks)


def extract_number(output: str) -> float | None:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith('>') or line.startswith('/'):
            continue
        if re.fullmatch(r'-?\d+(\.\d+)?', line):
            return float(line)
    for line in reversed(lines):
        if 'Version' in line or line in {'S', 'E'}:
            continue
        match = re.search(r'\b(\d+\.\d+)\b', line)
        if match:
            return float(match.group(1))
    return None


def bench_bbc(
    program: str,
    unlimited_cpu: bool = False,
    expect_timing: bool = True,
) -> tuple[str, float | None]:
    commands = [
        'load /bin/bbcbasic24.bin',
        'run',
        f'LOAD "{program}"',
        'RUN',
    ]
    output = run_script(
        commands,
        unlimited_cpu=unlimited_cpu,
        expect_timing=expect_timing,
    )
    return output, extract_number(output)


def main() -> int:
    args = sys.argv[1:]
    unlimited = False
    targets: list[str] = []
    for arg in args:
        if arg in ('-u', '--unlimited-cpu'):
            unlimited = True
        else:
            targets.append(arg)
    if not targets:
        targets = ['benchm7', 'life28_compute', 'life38_compute']
    mapping = {
        'benchm7': ('bench/benchm7.bas', 1, True),
        'hello': ('bench/hello.bas', 1, False),
        'life28': ('bench/life_bench28.bas', 5, True),
        'life28_1': ('bench/life_bench28_1gen.bas', 1, True),
        'life28_compute': ('bench/life_compute28.bas', 5, True),
        'life28_print': ('bench/life_bench28_print.bas', 5, True),
        'life38': ('bench/life_bench38.bas', 5, True),
        'life38_compute': ('bench/life_compute38.bas', 5, True),
    }

    if not os.path.isfile(CLI):
        print(f'agon-cli-emulator not found: {CLI}', file=sys.stderr)
        return 1

    for name in targets:
        entry = mapping.get(name)
        if not entry:
            print(f'Unknown benchmark: {name}', file=sys.stderr)
            return 1
        path, generations, expect_timing = entry
        print(f'=== {name} ({path}){" [unlimited CPU]" if unlimited else ""} ===')
        try:
            output, value = bench_bbc(
                path,
                unlimited_cpu=unlimited,
                expect_timing=expect_timing,
            )
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if value is None:
            if expect_timing:
                print(output)
                print('Could not parse timing from output', file=sys.stderr)
                return 1
            print('OK (no timing expected)')
            print()
            continue
        if name.startswith('life'):
            per_gen = value / generations
            print(
                f'Total {generations} generation(s): {value:.3f} s  ->  {per_gen:.3f} s/gen'
            )
        else:
            print(f'Time: {value:.3f} s')
        print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())