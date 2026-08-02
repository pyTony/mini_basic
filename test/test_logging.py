"""
test_logging.py - Centralized, automatic logging for the mini_basic test suite.

Drop this file into your C:\\Users\\Tony\\mini_basic\\test\\ directory.

Usage (recommended - makes logging "automatic"):

1. Edit test/__init__.py and add:
   from .test_logging import setup_logging
   setup_logging()

2. Or import it early in your main runners:
   import test_logging
   test_logging.setup_logging()

This gives you:
- Timestamped rotating log files in logs/
- DEBUG level to file (full detail)
- INFO+ to console (clean output)
- Safe for mixed unittest + standalone probe scripts
- No duplicate logs even if imported multiple times
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
from datetime import datetime
from pathlib import Path

# Configuration - adjust if needed
LOG_DIR = Path(__file__).parent / "logs"
LOG_LEVEL_FILE = logging.DEBUG
LOG_LEVEL_CONSOLE = logging.INFO
LOG_FORMAT_FILE = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
)
LOG_FORMAT_CONSOLE = "%(levelname)s: %(message)s"
LOG_FILENAME_PREFIX = "mini_basic_test"


def setup_logging(
    log_dir: Path | str = LOG_DIR,
    level_file: int = LOG_LEVEL_FILE,
    level_console: int = LOG_LEVEL_CONSOLE,
    force: bool = False,
) -> Path:
    """
    Set up centralized logging for the entire test suite.
    
    Call this once early in your test run (ideally in __init__.py or main runners).
    
    Returns the path to the current log file.
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create a unique log file per run (with timestamp)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = log_dir / f"{LOG_FILENAME_PREFIX}_{timestamp}.log"

    root_logger = logging.getLogger()

    # Prevent duplicate handlers (very common corner case in large test suites)
    if root_logger.handlers and not force:
        # Already configured - just return the latest log file path
        for h in root_logger.handlers:
            if isinstance(h, TimedRotatingFileHandler):
                return Path(h.baseFilename)
        return log_file

    # Clean any previous handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    root_logger.setLevel(level_file)

    # === File handler (full debug, rotating daily, keep 14 days) ===
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=14,
        encoding="utf-8",
        delay=True,
    )
    file_handler.setLevel(level_file)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT_FILE))
    root_logger.addHandler(file_handler)

    # === Console handler (cleaner output) ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level_console)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT_CONSOLE))
    root_logger.addHandler(console_handler)

    # Log startup info
    logging.info("=" * 70)
    logging.info("MINI_BASIC TEST LOGGING INITIALIZED")
    logging.info(f"Log file: {log_file}")
    logging.info(f"Python: {sys.version.split()[0]} | Platform: {sys.platform}")
    logging.info("=" * 70)

    return log_file


def get_logger(name: str | None = None) -> logging.Logger:
    """Convenience function to get a properly namespaced logger."""
    return logging.getLogger(name or __name__)


# Auto-initialize when this module is imported directly
# (safe - will only configure once)
if __name__ != "__main__":
    # Only auto-setup when imported as a module, not when run directly
    pass  # We prefer explicit call for control


# Example of how to use in a specific test file if you don't use __init__.py:
# import test_logging
# test_logging.setup_logging()
# logger = test_logging.get_logger(__name__)
# logger.debug("This will go to the detailed log file")