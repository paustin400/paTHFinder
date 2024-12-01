# run_tests.py

import os
import logging
from dotenv import load_dotenv
import pytest

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_model_tests():
    """Run all model tests with proper setup"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Ensure model directory exists
        model_dir = os.getenv("MODEL_DIR", "models")
        os.makedirs(model_dir, exist_ok=True)
        
        # Run tests
        logger.info("Starting model tests...")
        pytest.main(["-v", "tests/test_models.py"])
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        raise

if __name__ == "__main__":
    run_model_tests()