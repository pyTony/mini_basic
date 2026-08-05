import unittest
import logging
from logging.handlers import RotatingFileHandler
import os

# ============================================================
# PROPER LOGGING SETUP FOR UNITTESTS (to ensure logs are captured)
# This fixes the common issue where unittest does not auto-create log files
# and avoids duplicate log messages (a frequent corner case)
# ============================================================

def setup_test_logging(log_file='test_execution.log'):
    """Configure root logger to write to a rotating log file.
    
    Call this once at module import time for automatic logging during tests.
    """
    root_logger = logging.getLogger()
    
    # CRITICAL: Remove any existing handlers to prevent duplicate logs
    # This is a common corner case when basicConfig is used incorrectly
    # or when multiple test modules are imported.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    
    root_logger.setLevel(logging.DEBUG)
    
    # File handler with rotation (good for large test suites)
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Optional: also log to console for immediate feedback during test runs
    # Comment out if you only want file logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Only INFO+ to console, DEBUG to file
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    logging.info("=== Test logging initialized ===")
    return log_file

# Initialize logging automatically when this test module is imported
# This makes it "automatic" for this test file
LOG_FILE = setup_test_logging(os.path.join(os.path.dirname(__file__), 'test_execution.log'))

# Now import the module under test (after logging is set up)
from example_module import do_something

class TestExample(unittest.TestCase):
    
    def setUp(self):
        logging.debug("setUp called for %s", self._testMethodName)
    
    def test_do_something(self):
        logging.info("Starting test_do_something")
        result = do_something()
        logging.debug("Result from module: %s", result)
        self.assertTrue(result)
        logging.info("test_do_something passed successfully")
    
    def test_another_case(self):
        logging.warning("This is a warning log to demonstrate different levels")
        self.assertEqual(1 + 1, 2)
    
    def tearDown(self):
        logging.debug("tearDown called for %s", self._testMethodName)

if __name__ == '__main__':
    # When running directly, logging is already set up at import
    unittest.main(verbosity=2)