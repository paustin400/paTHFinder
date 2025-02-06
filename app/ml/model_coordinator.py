# app/ml/model_coordinator.py
from typing import Dict, Optional, Any
import numpy as np
from cachetools import TTLCache, cached
from datetime import datetime
import joblib
import logging
import os
from flask import current_app
from ..models import Route
from .ai_model import PathfinderAI
from .ann_model import PathfinderANN, prepare_route_features

logger = logging.getLogger(__name__)

class ModelCoordinator:
    def __init__(self):
        self.predictions_cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour TTL
        self.version_hash = None
        self.rf_model: Optional[PathfinderAI] = None  # RF model via PathfinderAI
        self.ann_model: Optional[PathfinderANN] = None  # ANN model instance
        self.model_version = "unknown"
        
    def initialize_models(self) -> bool:
        """Initialize both the RF and ANN models."""
        try:
            # Initialize RF model using PathfinderAI
            self.rf_model = PathfinderAI()
            if not self.rf_model.init_models():
                logger.error("Failed to initialize RF model in PathfinderAI")
                return False

            # Initialize ANN model using PathfinderANN
            self.ann_model = PathfinderANN()
            if not self.ann_model.load_model():
                logger.warning("ANN model not loaded; building a new model.")
                self.ann_model.build_model()
            # Use the version from the RF model (or combine versions as needed)
            self.model_version = self.rf_model.model_version
            return True
        except Exception as e:
            logger.error(f"Error initializing models: {e}", exc_info=True)
            return False

    @cached(lambda self: self.predictions_cache)
    def get_route_predictions(self, route_id: int, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        try:
            route = Route.query.get(route_id)
            if not route:
                return self.get_fallback_predictions()
                
            # Prepare features for each model branch
            # For the RF model, use its own feature preparation method.
            rf_features = self.rf_model.prepare_route_features(route)
            # For the ANN model, prepare features using our helper from ann_model.
            ann_features = self.prepare_ann_features(route, user_preferences)
            
            predictions = self._generate_predictions(route, user_preferences)
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction error for route {route_id}: {e}")
            return self.get_fallback_predictions()

    def _generate_predictions(self, route: Route, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictions by combining both models."""
        try:
            # Prepare features (redundant calls ensure both branches are using fresh data)
            rf_features = self.rf_model.prepare_route_features(route)
            ann_features = self.prepare_ann_features(route, preferences)
            
            # Get predictions from the RF model (which provides route type, difficulty, etc.)
            rf_predictions = self.rf_model.predict_route_properties(rf_features)
            # Get quality score from the ANN model
            ann_quality_score = float(self.ann_model.predict_route_quality(ann_features)[0][0])
            
            predictions = {
                'route_type': rf_predictions.get('route_type', 'unknown'),
                'difficulty_score': rf_predictions.get('difficulty_score', 0.5),
                'quality_score': ann_quality_score,
                'confidence_score': rf_predictions.get('confidence_score', 0.0),
                'prediction_timestamp': datetime.utcnow().isoformat(),
                'model_version': self.model_version,
                'is_fallback': False
            }
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}", exc_info=True)
            return self.get_fallback_predictions()
    
    def prepare_ann_features(self, route: Route, user_preferences: Dict[str, Any]) -> np.ndarray:
        """Prepare features for the ANN model, including user preferences."""
        features = {
            'distance': float(route.distance),
            'elevation_gain': float(route.elevation_gain) if route.elevation_gain else 0.0,
            'traffic_level': self.get_traffic_score(user_preferences),
            'surface_quality': self.get_surface_score(user_preferences),
            'safety_score': self.get_safety_score(user_preferences)
        }
        return prepare_route_features(features)
    
    def get_traffic_score(self, preferences: Dict[str, Any]) -> float:
        """Convert traffic preferences to a numerical score."""
        traffic_map = {'avoid': 0.0, 'neutral': 0.5}
        return traffic_map.get(preferences.get('traffic_preference', 'neutral'), 0.5)
    
    def get_surface_score(self, preferences: Dict[str, Any]) -> float:
        """Convert surface preferences to a numerical score."""
        surface_map = {'asphalt': 1.0, 'dirt': 0.7, 'grass': 0.4}
        return surface_map.get(preferences.get('surface_preference', 'asphalt'), 0.7)
    
    def get_safety_score(self, preferences: Dict[str, Any]) -> float:
        """Calculate a safety score based on user preferences."""
        base_score = 0.8  # Default safety score
        if preferences.get('require_lighting'):
            base_score += 0.1
        if preferences.get('require_sidewalks'):
            base_score += 0.1
        return min(base_score, 1.0)
    
    def get_fallback_predictions(self) -> Dict[str, Any]:
        """Return fallback predictions if model processing fails."""
        return {
            'route_type': 'mixed',
            'difficulty_score': 0.5,
            'quality_score': 0.5,
            'confidence_score': 0.0,
            'prediction_timestamp': datetime.utcnow().isoformat(),
            'model_version': self.model_version,
            'is_fallback': True
        }
    
    def update_models(self, new_training_data: Optional[Dict] = None) -> bool:
        """Update both models with new training data."""
        try:
            if not new_training_data:
                logger.error("No training data provided")
                return False
                
            # Ensure models are initialized
            if not self.rf_model or not self.ann_model:
                logger.info("Initializing models before training")
                if not self.initialize_models():
                    raise RuntimeError("Failed to initialize models")
            
            # Update RF model
            logger.info("Training RF model...")
            rf_success = self.rf_model.train(new_training_data['rf_features'], 
                                             new_training_data['rf_labels'])
            
            # Update ANN model
            logger.info("Training ANN model...")
            ann_success, metrics = self.ann_model.train(
                new_training_data['ann_features'],
                new_training_data['ann_labels']
            )
            
            if not (rf_success and ann_success):
                logger.error("Training failed for one or both models")
                return False
            
            self.model_version = f"1.0.{int(datetime.utcnow().timestamp())}"
            self.predictions_cache.clear()  # Clear the cache after training
            
            logger.info("Models trained successfully")
            logger.info(f"ANN training metrics: {metrics}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating models: {str(e)}", exc_info=True)
            return False
