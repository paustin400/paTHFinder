# tests/config.py

import os
import tempfile
import shutil
import logging
from datetime import datetime

class TestConfig:
    # Base paths
    TEST_MODEL_DIR = tempfile.mkdtemp()
    TEST_LOG_DIR = tempfile.mkdtemp()
    
    # Test database config
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
    
    # Logging config
    LOG_FILE = os.path.join(TEST_LOG_DIR, f'test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    # Model file names
    MODEL_FILES = {
        'ann_model': 'pathfinder_ann.pkl',
        'ann_metadata': 'pathfinder_ann_metadata.json',
        'rf_model': 'pathfinder_model.pkl'
    }
    
    @classmethod
    def init(cls):
        """Initialize test environment"""
        # Set up directories
        os.makedirs(cls.TEST_MODEL_DIR, exist_ok=True)
        os.makedirs(cls.TEST_LOG_DIR, exist_ok=True)
        
        # Set environment variables
        os.environ['MODEL_DIR'] = cls.TEST_MODEL_DIR
        os.environ['TESTING'] = 'True'
        
        # Initialize logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(cls.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info(f"Initialized test environment in {cls.TEST_MODEL_DIR}")
        logger.info(f"Logs will be written to {cls.LOG_FILE}")
    
    @classmethod
    def cleanup(cls):
        """Clean up test environment"""
        try:
            # Remove test directories and contents
            if os.path.exists(cls.TEST_MODEL_DIR):
                shutil.rmtree(cls.TEST_MODEL_DIR)
            
            # Keep logs unless explicitly told to remove them
            # if os.path.exists(cls.TEST_LOG_DIR):
            #     shutil.rmtree(cls.TEST_LOG_DIR)
            
            # Clear environment variables
            os.environ.pop('MODEL_DIR', None)
            os.environ.pop('TESTING', None)
            
            logger = logging.getLogger(__name__)
            logger.info("Cleaned up test environment")
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error during cleanup: {str(e)}")
    
    @classmethod
    def get_model_path(cls, model_name):
        """Get full path for a model file"""
        return os.path.join(cls.TEST_MODEL_DIR, cls.MODEL_FILES.get(model_name, ''))