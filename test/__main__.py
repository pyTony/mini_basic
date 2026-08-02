"""Run the test suite with progress logging: python -m test"""
import test.test_logging as test_logging
test_logging.setup_logging()
from test.progress_runner import run_discover

if __name__ == '__main__':
    raise SystemExit(run_discover(timeout=180))   # 3 minutes
