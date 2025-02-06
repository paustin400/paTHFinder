# run_tests.py

import os
import logging
from dotenv import load_dotenv
import pytest
from datetime import datetime
from tests.config import TestConfig

def setup_logging():
    """Set up logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Create handler for file output
    file_handler = logging.FileHandler(TestConfig.LOG_FILE)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure root logger
    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(console_handler)
    logging.root.addHandler(file_handler)
    
    return logging.getLogger(__name__)

def run_model_tests():
    """Run all model tests with proper setup and logging"""
    logger = setup_logging()
    try:
        # Load environment variables
        load_dotenv()
        
        logger.info("Starting test run...")
        logger.info(f"Test directory: {TestConfig.TEST_MODEL_DIR}")
        logger.info(f"Log file: {TestConfig.LOG_FILE}")
        
        # Run tests with pytest
        args = [
            "-v",  # verbose output
            "--capture=tee-sys",  # capture stdout/stderr
            "tests/test_models.py",  # test file
            "-s",  # don't capture stdout (allows print statements)
        ]
        
        # Add coverage reporting if pytest-cov is installed
        try:
            import pytest_cov
            args.extend([
                "--cov=app.ml",
                "--cov-report=term-missing",
                "--cov-report=html:coverage_report"
            ])
            logger.info("Coverage reporting enabled")
        except ImportError:
            logger.warning("pytest-cov not installed, skipping coverage report")
        
        result = pytest.main(args)
        
        if result == 0:
            logger.info("All tests passed successfully!")
        else:
            logger.error(f"Some tests failed. Exit code: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}", exc_info=True)
        return 1
    
    finally:
        logger.info("Test run completed")

if __name__ == "__main__":
    exit_code = run_model_tests()
    exit(exit_code)