# tests/test_models.py

import os
import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from datetime import datetime
from app.ml.model_coordinator import ModelCoordinator
from app.ml.ai_model import PathfinderAI
from app.ml.ann_model import PathfinderANN, prepare_route_features
from tests.config import TestConfig
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before all tests"""
    TestConfig.init()
    yield
    TestConfig.cleanup()

@pytest.fixture
def app():
    """Create test Flask application"""
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TestConfig.SQLALCHEMY_DATABASE_URI,
        'MODEL_DIR': TestConfig.TEST_MODEL_DIR
    })
    return app

@pytest.fixture
def mock_route():
    """Create a mock Route object"""
    route = MagicMock()
    route.id = 1
    route.distance = 5.0
    route.elevation_gain = 100.0
    route.has_sidewalks = 1
    route.is_lit = 1
    route.surface_type = 'asphalt'
    return route

@pytest.fixture
def sample_route_data():
    """Generate sample route data for ANN model"""
    return {
        'distance': 5.0,
        'elevation_gain': 100.0,
        'traffic_level': 0.5,
        'surface_quality': 0.7,
        'safety_score': 0.8
    }

@pytest.fixture
def sample_training_data():
    """Generate sample training data"""
    n_samples = 100
    routes_data = pd.DataFrame({
        'distance': np.random.uniform(1, 15, n_samples),
        'elevation_gain': np.random.uniform(0, 500, n_samples),
        'has_sidewalks': np.random.choice([0, 1], n_samples),
        'is_lit': np.random.choice([0, 1], n_samples),
        'surface_type': np.random.choice(['asphalt', 'dirt', 'grass'], n_samples)
    })
    
    # Create consistent training data shapes
    ann_features = np.random.uniform(0, 1, (n_samples, 5))
    ann_labels = np.random.uniform(0, 1, n_samples)
    
    return {
        'rf_features': routes_data,
        'rf_labels': {
            'route_type': np.random.choice(['easy', 'moderate', 'challenging'], n_samples),
            'difficulty': np.random.uniform(0, 1, n_samples)
        },
        'ann_features': ann_features,
        'ann_labels': ann_labels
    }

class TestANNModel:
    """Test suite for PathfinderANN model"""
    
    def test_initialization(self):
        """Test ANN model initialization"""
        model = PathfinderANN()
        assert model is not None
        assert model.input_shape == 5
        assert len(model.feature_names) == 5
        logger.info("ANN initialization test passed")

    def test_build_model(self):
        """Test model building"""
        model = PathfinderANN()
        model.build_model()
        assert model.model is not None
        assert model.scaler is not None
        logger.info("Model building test passed")

    def test_feature_preparation(self, sample_route_data):
        """Test ANN feature preparation"""
        features = prepare_route_features(sample_route_data)
        assert isinstance(features, np.ndarray)
        assert features.shape == (1, 5)
        assert np.all(np.isfinite(features))
        logger.info("Feature preparation test passed")

    def test_train_and_predict(self, sample_training_data):
        """Test training and prediction pipeline"""
        model = PathfinderANN()
        success, metrics = model.train(
            sample_training_data['ann_features'],
            sample_training_data['ann_labels']
        )
        assert success is True
        assert isinstance(metrics, dict)
        assert 'r2_score' in metrics
        
        # Test predictions
        test_features = np.random.uniform(0, 1, (1, 5))
        predictions = model.predict_route_quality(test_features)
        assert predictions.shape == (1, 1)
        assert 0 <= predictions[0][0] <= 1
        logger.info("Training and prediction test passed")

    def test_model_save_load(self, sample_training_data):
        """Test model saving and loading"""
        model = PathfinderANN()
        
        # Train and save
        success, _ = model.train(
            sample_training_data['ann_features'],
            sample_training_data['ann_labels']
        )
        assert success is True
        
        # Create new instance and load
        new_model = PathfinderANN()
        load_success = new_model.load_model()
        assert load_success is True
        assert new_model.model is not None
        logger.info("Model save/load test passed")

class TestModelCoordinator:
    """Test suite for ModelCoordinator"""
    
    def test_initialization(self, app):
        """Test coordinator initialization"""
        with app.app_context():
            coordinator = ModelCoordinator()
            success = coordinator.initialize_models()
            assert success is True
            assert coordinator.rf_model is not None
            assert coordinator.ann_model is not None
            logger.info("Coordinator initialization test passed")

    def test_prediction_pipeline(self, app, mock_route, sample_training_data):
        """Test full prediction pipeline"""
        with app.app_context():
            coordinator = ModelCoordinator()
            # Initialize and train first
            assert coordinator.initialize_models()
            assert coordinator.update_models(sample_training_data)
            
            preferences = {
                'traffic_preference': 'avoid',
                'surface_preference': 'asphalt',
                'require_lighting': True,
                'require_sidewalks': True
            }
            
            with patch('app.models.Route.query') as mock_query:
                mock_query.get.return_value = mock_route
                predictions = coordinator.get_route_predictions(1, preferences)
            
            assert isinstance(predictions, dict)
            assert 'route_type' in predictions
            assert 'quality_score' in predictions
            assert not predictions.get('is_fallback', False)
            logger.info("Prediction pipeline test passed")

    def test_model_training(self, app, sample_training_data):
        """Test coordinator model training"""
        with app.app_context():
            coordinator = ModelCoordinator()
            success = coordinator.update_models(sample_training_data)
            assert success is True
            logger.info("Coordinator training test passed")

    def test_fallback_behavior(self, app):
        """Test fallback predictions"""
        with app.app_context():
            coordinator = ModelCoordinator()
            predictions = coordinator.get_fallback_predictions()
            assert isinstance(predictions, dict)
            assert predictions.get('is_fallback') is True
            logger.info("Fallback behavior test passed")

def test_end_to_end(app, sample_training_data, mock_route):
    """End-to-end test of the entire model pipeline"""
    with app.app_context():
        coordinator = ModelCoordinator()
        
        # Initialize and train
        assert coordinator.initialize_models()
        assert coordinator.update_models(sample_training_data)
        
        # Test predictions
        preferences = {
            'traffic_preference': 'avoid',
            'surface_preference': 'asphalt',
            'require_lighting': True,
            'require_sidewalks': True
        }
        
        with patch('app.models.Route.query') as mock_query:
            mock_query.get.return_value = mock_route
            predictions = coordinator.get_route_predictions(1, preferences)
        
        assert predictions is not None
        assert not predictions.get('is_fallback', False)
        assert all(k in predictions for k in [
            'route_type', 'difficulty_score', 'quality_score'
        ])
        logger.info("End-to-end test passed")