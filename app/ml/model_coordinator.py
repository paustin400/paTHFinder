# app/ml/model_coordinator.py

from typing import Dict, Optional, Tuple, Any
import numpy as np
from functools import lru_cache
from datetime import datetime
import joblib
import logging
import os
from flask import current_app
from ..models import Route
from .ai_model import PathfinderAI
from .ann_model import PathfinderANN, prepare_route_features

class ModelCoordinator:
    def __init__(self):
        self.rf_model: Optional[PathfinderAI] = None
        self.ann_model: Optional[PathfinderANN] = None
        self.logger = logging.getLogger(__name__)
        self.model_version = "1.0.0"
        
    def initialize_models(self) -> bool:
        """Initialize both AI models with error handling"""
        try:
            self.rf_model = PathfinderAI()
            self.ann_model = PathfinderANN()
            
            # Initialize both models
            rf_success = self.rf_model.init_models()
            ann_success = self.ann_model.load_model()
            
            if not (rf_success and ann_success):
                self.logger.error("Failed to initialize one or both models")
                return False
                
            self.logger.info("Successfully initialized both AI models")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during model initialization: {str(e)}")
            return False
    
    def get_route_predictions(self, route_id: int, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Get combined predictions from both models"""
        try:
            route = Route.query.get(route_id)
            if not route:
                return self.get_fallback_predictions()
                
            # Create cache key from preferences
            pref_key = self._create_cache_key(user_preferences)
            return self._get_cached_predictions(route_id, route, pref_key)
            
        except Exception as e:
            self.logger.error(f"Error getting predictions: {str(e)}")
            return self.get_fallback_predictions()

    def _create_cache_key(self, preferences: Dict[str, Any]) -> str:
        """Create a hashable key from preferences dictionary"""
        sorted_items = sorted(preferences.items())
        return '_'.join(f"{k}:{str(v)}" for k, v in sorted_items)

    @lru_cache(maxsize=1000)
    def _get_cached_predictions(self, route_id: int, route: Any, pref_key: str) -> Dict[str, Any]:
        """Get predictions using a hashable cache key"""
        try:
            # Convert pref_key back to dictionary
            preferences = dict(
                item.split(':', 1) for item in pref_key.split('_')
            )
            
            # Prepare features for both models
            rf_features = self.rf_model.prepare_route_features(route)
            ann_features = self.prepare_ann_features(route, preferences)
            
            # Get predictions from both models
            rf_predictions = self.rf_model.predict_route_properties(rf_features)
            ann_quality_score = float(self.ann_model.predict_route_quality(ann_features)[0][0])
            
            # Combine predictions
            return {
                'route_type': rf_predictions['route_type'],
                'difficulty_score': rf_predictions['difficulty_score'],
                'quality_score': ann_quality_score,
                'confidence_score': rf_predictions['confidence_score'],
                'prediction_timestamp': datetime.utcnow().isoformat(),
                'model_version': self.model_version
            }
            
        except Exception as e:
            self.logger.error(f"Error in cached predictions: {str(e)}")
            return self.get_fallback_predictions()
    
    def prepare_ann_features(self, route: Route, user_preferences: Dict[str, Any]) -> np.ndarray:
        """Prepare features for ANN model with user preferences"""
        features = {
            'distance': float(route.distance),
            'elevation_gain': float(route.elevation_gain) if route.elevation_gain else 0,
            'traffic_level': self.get_traffic_score(user_preferences),
            'surface_quality': self.get_surface_score(user_preferences),
            'safety_score': self.get_safety_score(user_preferences)
        }
        return prepare_route_features(features)
    
    def get_traffic_score(self, preferences: Dict[str, Any]) -> float:
        """Convert traffic preferences to numerical score"""
        traffic_map = {'avoid': 0.0, 'neutral': 0.5}
        return traffic_map.get(preferences.get('traffic_preference', 'neutral'), 0.5)
    
    def get_surface_score(self, preferences: Dict[str, Any]) -> float:
        """Convert surface preferences to numerical score"""
        surface_map = {'asphalt': 1.0, 'dirt': 0.7, 'grass': 0.4}
        return surface_map.get(preferences.get('surface_preference', 'asphalt'), 0.7)
    
    def get_safety_score(self, preferences: Dict[str, Any]) -> float:
        """Calculate safety score based on user preferences"""
        base_score = 0.8  # Default safety score
        if preferences.get('require_lighting'):
            base_score += 0.1
        if preferences.get('require_sidewalks'):
            base_score += 0.1
        return min(base_score, 1.0)
    
    def get_fallback_predictions(self) -> Dict[str, Any]:
        """Provide fallback predictions when models fail"""
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
        """Update models with new training data"""
        try:
            if not new_training_data:
                self.logger.error("No training data provided")
                return False
                
            # Initialize models if not already initialized
            if not self.rf_model or not self.ann_model:
                self.logger.info("Initializing models before training")
                if not self.initialize_models():
                    raise RuntimeError("Failed to initialize models")
            
            # Update RF model
            self.logger.info("Training RF model...")
            rf_success = self.rf_model.train(new_training_data['rf_features'], 
                                           new_training_data['rf_labels'])
            
            # Update ANN model
            self.logger.info("Training ANN model...")
            ann_success, metrics = self.ann_model.train(
                new_training_data['ann_features'],
                new_training_data['ann_labels']
            )
            
            if not (rf_success and ann_success):
                self.logger.error("Training failed for one or both models")
                return False
            
            self.model_version = f"1.0.{int(datetime.utcnow().timestamp())}"
            self._get_cached_predictions.cache_clear()  # Clear prediction cache
            
            self.logger.info("Models trained successfully")
            self.logger.info(f"ANN training metrics: {metrics}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating models: {str(e)}", exc_info=True)
            return False