"""Backward-compatible wrapper: use mini_basic --pygame instead."""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import main


def _forward_argv() -> list[str]:
    argv = ['--pygame']
    user = sys.argv[1:]
    if user and user[0] == '--no-hold':
        argv.append('--no-hold')
        user = user[1:]
    if not user:
        user = [os.path.join('test', 'corpus', 'agon', 'life.bas')]
    argv.extend(user)
    return argv


if __name__ == '__main__':
    raise SystemExit(main(_forward_argv()))