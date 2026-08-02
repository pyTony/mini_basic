"""Allow ``python -m mini_basic`` as the primary CLI entry point."""
from mini_basic import main

if __name__ == '__main__':
    raise SystemExit(main())
