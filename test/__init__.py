"""
test package initialization with automatic logging.

This makes logging active for almost everything in the test suite
as soon as any test module does `import test` or `from test import ...`

To activate:
1. Replace your current test/__init__.py with this file (or merge the content)
2. Run any test normally (python -m test, python test_xxx.py, etc.)

You can still override by calling setup_logging(force=True) later.
"""

from .test_logging import setup_logging

# This runs automatically when the package is imported
setup_logging()