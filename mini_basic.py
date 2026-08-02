"""Backward-compatible entry point: ``python mini_basic.py``.

Implementation lives in the ``mini_basic`` package (``mini_basic/runtime.py``).
Prefer ``python -m mini_basic`` for the same CLI.
"""
from mini_basic import main
from mini_basic.util import hard_exit

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\nGoodbye!')
        raise SystemExit(130)
