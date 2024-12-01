# tests/config.py

import os
import tempfile

class TestConfig:
    # Use temporary directory for test models
    TEST_MODEL_DIR = tempfile.mkdtemp()
    
    # Test database config (if needed)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
    
    @classmethod
    def init(cls):
        """Initialize test environment"""
        os.environ['MODEL_DIR'] = cls.TEST_MODEL_DIR
        
    @classmethod
    def cleanup(cls):
        """Clean up test environment"""
        # Remove temporary test files
        if os.path.exists(cls.TEST_MODEL_DIR):
            for file in os.listdir(cls.TEST_MODEL_DIR):
                os.remove(os.path.join(cls.TEST_MODEL_DIR, file))
            os.rmdir(cls.TEST_MODEL_DIR)