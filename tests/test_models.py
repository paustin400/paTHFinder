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
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_tests.log'),
        logging.StreamHandler()
    ]
)
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

@pytest.fixture
def diverse_test_routes():
    """Generate a diverse set of test routes"""
    return [
        {
            'id': 1,
            'distance': 5.0,
            'elevation_gain': 100.0,
            'has_sidewalks': 1,
            'is_lit': 1,
            'surface_type': 'asphalt',
            'description': 'Easy urban route'
        },
        {
            'id': 2,
            'distance': 12.0,
            'elevation_gain': 400.0,
            'has_sidewalks': 0,
            'is_lit': 0,
            'surface_type': 'dirt',
            'description': 'Challenging trail'
        },
        {
            'id': 3,
            'distance': 8.0,
            'elevation_gain': 200.0,
            'has_sidewalks': 1,
            'is_lit': 0,
            'surface_type': 'grass',
            'description': 'Moderate park route'
        }
    ]

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

class TestPredictions:
    """Test suite for model predictions"""
    
    def test_diverse_route_predictions(self, app, diverse_test_routes):
        """Test predictions for different types of routes"""
        with app.app_context():
            coordinator = ModelCoordinator()
            assert coordinator.initialize_models()
            
            for route_data in diverse_test_routes:
                # Create mock route object
                mock_route = MagicMock()
                for key, value in route_data.items():
                    setattr(mock_route, key, value)
                
                # Test with different user preferences
                preferences = {
                    'traffic_preference': 'neutral',
                    'surface_preference': route_data['surface_type'],
                    'require_lighting': bool(route_data['is_lit']),
                    'require_sidewalks': bool(route_data['has_sidewalks'])
                }
                
                with patch('app.models.Route.query') as mock_query:
                    mock_query.get.return_value = mock_route
                    predictions = coordinator.get_route_predictions(
                        route_data['id'], 
                        preferences
                    )
                
                logger.info(f"\nPredictions for {route_data['description']}:")
                logger.info(f"Route characteristics: {route_data}")
                logger.info(f"Predictions: {predictions}")
                
                # Verify prediction structure and ranges
                assert 'route_type' in predictions
                assert 'difficulty_score' in predictions
                assert 'quality_score' in predictions
                assert 0 <= predictions['difficulty_score'] <= 1
                assert 0 <= predictions['quality_score'] <= 1
                assert predictions['route_type'] in ['easy', 'moderate', 'challenging']
    
    def test_prediction_consistency(self, app, mock_route):
        """Test consistency of predictions"""
        with app.app_context():
            coordinator = ModelCoordinator()
            assert coordinator.initialize_models()
            
            preferences = {
                'traffic_preference': 'neutral',
                'surface_preference': 'asphalt',
                'require_lighting': True,
                'require_sidewalks': True
            }
            
            # Make multiple predictions for the same route
            predictions = []
            with patch('app.models.Route.query') as mock_query:
                mock_query.get.return_value = mock_route
                for _ in range(3):
                    pred = coordinator.get_route_predictions(1, preferences)
                    predictions.append(pred)
            
            # Verify predictions are consistent
            for i in range(1, len(predictions)):
                assert predictions[i]['route_type'] == predictions[0]['route_type']
                assert abs(predictions[i]['difficulty_score'] - predictions[0]['difficulty_score']) < 1e-6
                assert abs(predictions[i]['quality_score'] - predictions[0]['quality_score']) < 1e-6

    def test_edge_cases(self, app):
        """Test prediction behavior with edge cases"""
        with app.app_context():
            coordinator = ModelCoordinator()
            assert coordinator.initialize_models()
            
            # Test edge case routes
            edge_cases = [
                {
                    'id': 4,
                    'distance': 0.1,  # Very short distance
                    'elevation_gain': 0.0,
                    'has_sidewalks': 1,
                    'is_lit': 1,
                    'surface_type': 'asphalt'
                },
                {
                    'id': 5,
                    'distance': 50.0,  # Very long distance
                    'elevation_gain': 1000.0,
                    'has_sidewalks': 0,
                    'is_lit': 0,
                    'surface_type': 'dirt'
                }
            ]
            
            for route_data in edge_cases:
                mock_route = MagicMock()
                for key, value in route_data.items():
                    setattr(mock_route, key, value)
                
                preferences = {
                    'traffic_preference': 'neutral',
                    'surface_preference': route_data['surface_type'],
                    'require_lighting': bool(route_data['is_lit']),
                    'require_sidewalks': bool(route_data['has_sidewalks'])
                }
                
                with patch('app.models.Route.query') as mock_query:
                    mock_query.get.return_value = mock_route
                    predictions = coordinator.get_route_predictions(
                        route_data['id'],
                        preferences
                    )
                
                logger.info(f"\nEdge case predictions:")
                logger.info(f"Route data: {route_data}")
                logger.info(f"Predictions: {predictions}")
                
                # Verify predictions are still within valid ranges
                assert 0 <= predictions['difficulty_score'] <= 1
                assert 0 <= predictions['quality_score'] <= 1

def test_end_to_end(app, sample_training_data, mock_route):
    """End-to-end test of the entire model pipeline"""
    with app.app_context():
        coordinator = ModelCoordinator()
        
        # Initialize and train
        assert coordinator.initialize_models()
        assert coordinator.update_models(sample_training_data)
        
        # Test predictions
        preferences = {
            'traffic_preference': 'neutral',
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