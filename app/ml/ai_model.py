import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
from typing import Dict, Optional, Any
import logging
from datetime import datetime
from .config import ModelConfig

logger = logging.getLogger(__name__)

def init_ai_model():
    """Initialize the AI model for the application."""
    try:
        model = PathfinderAI()
        success = model.init_models()
        if not success:
            raise RuntimeError("Failed to initialize PathfinderAI model")
        return model
    except Exception as e:
        logger.error(f"Error initializing AI model: {str(e)}")
        raise

class PathfinderAI:
    def __init__(self):
        self.model_path = ModelConfig.RF_MODEL_PATH
        self.route_classifier: Optional[RandomForestClassifier] = None
        self.difficulty_predictor: Optional[GradientBoostingRegressor] = None
        self.scaler = StandardScaler()
        self.logger = logging.getLogger(__name__)
        self.model_version = "1.0.0"
        self.last_training_date: Optional[datetime] = None
        self.required_features = ModelConfig.REQUIRED_FEATURES
        
    def init_models(self) -> bool:
        """Initialize or load ML models with validation."""
        try:
            if os.path.exists(self.model_path):
                models = joblib.load(self.model_path)
                self.route_classifier = models['classifier']
                self.difficulty_predictor = models['regressor']
                self.scaler = models.get('scaler', StandardScaler())
                self.model_version = models.get('version', "1.0.0")
                self.last_training_date = models.get('training_date')
                return self.validate_models()
                
            self.logger.warning("No existing models found, initializing new ones")
            self.route_classifier = RandomForestClassifier(**ModelConfig.RF_CLASSIFIER_PARAMS)
            self.difficulty_predictor = GradientBoostingRegressor(**ModelConfig.GB_REGRESSOR_PARAMS)
            return True
        except Exception as e:
            self.logger.error(f"Error initializing models: {str(e)}")
            return False

    def validate_models(self) -> bool:
        """Validate the loaded models using test data."""
        try:
            # Create test data
            test_data = pd.DataFrame([{
                'distance': 5.0,
                'elevation_gain': 100.0,
                'has_sidewalks': 1,
                'is_lit': 1,
                'surface_type': 'asphalt'
            }])
            
            # Test feature preparation using our method
            features = self.prepare_route_features(test_data.iloc[0])
            if features.empty:
                raise ValueError("Failed to prepare test features")
            
            # Test predictions
            classifier_pred = self.route_classifier.predict(features)
            regressor_pred = self.difficulty_predictor.predict(features)
            
            return (isinstance(classifier_pred, np.ndarray) and 
                    isinstance(regressor_pred, np.ndarray) and 
                    len(classifier_pred) > 0 and 
                    len(regressor_pred) > 0)
                    
        except Exception as e:
            self.logger.error(f"Model validation failed: {str(e)}")
            return False

    def prepare_route_features(self, route: Any) -> pd.DataFrame:
        """Prepare and validate features for model prediction.
        
        Expects `route` to have attributes matching the required features.
        """
        try:
            # Check for required features
            missing_features = [f for f in self.required_features if not hasattr(route, f)]
            if missing_features:
                raise ValueError(f"Missing required features: {missing_features}")
            
            features = pd.DataFrame([{
                'distance': float(route.distance),
                'elevation_gain': float(route.elevation_gain) if route.elevation_gain else 0.0,
                'has_sidewalks': int(getattr(route, 'has_sidewalks', 0)),
                'is_lit': int(getattr(route, 'is_lit', 0)),
                'surface_type': str(getattr(route, 'surface_type', 'unknown'))
            }])
            
            # One-hot encode categorical variables
            if 'surface_type' in features:
                features = pd.get_dummies(features, columns=['surface_type'], prefix=['surface'])
            
            # Ensure all expected columns exist if the classifier has been trained
            if self.route_classifier and hasattr(self.route_classifier, 'feature_names_in_'):
                expected_columns = self.route_classifier.feature_names_in_
                for col in expected_columns:
                    if col not in features:
                        features[col] = 0
                features = features[expected_columns]
            
            return features
        except Exception as e:
            self.logger.error(f"Error preparing features: {str(e)}")
            return pd.DataFrame()

    def predict_route_properties(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Make predictions using both the classifier and regressor."""
        try:
            if features.empty:
                raise ValueError("Empty features provided")
            
            if not self.route_classifier or not self.difficulty_predictor:
                raise ValueError("Models not initialized")

            # Scale numerical features if present
            numerical_cols = ['distance', 'elevation_gain']
            numerical_cols = [col for col in numerical_cols if col in features.columns]
            if numerical_cols:
                features[numerical_cols] = self.scaler.transform(features[numerical_cols])
            
            predictions = {
                'route_type': self.route_classifier.predict(features)[0],
                'difficulty_score': float(self.difficulty_predictor.predict(features)[0]),
                'confidence_score': float(max(self.route_classifier.predict_proba(features)[0])),
                'model_version': self.model_version,
                'prediction_timestamp': datetime.utcnow().isoformat()
            }
            return predictions
        except Exception as e:
            self.logger.error(f"Error making predictions: {str(e)}")
            return {
                'route_type': 'unknown',
                'difficulty_score': 0.5,
                'confidence_score': 0.0,
                'model_version': self.model_version,
                'prediction_timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }

    def train(self, X: pd.DataFrame, y: Dict[str, np.ndarray], validation_split: float = 0.2) -> bool:
        """Train both models with validation data."""
        try:
            if X.empty or not y or 'route_type' not in y or 'difficulty' not in y:
                raise ValueError("Invalid training data")
            
            # One-hot encode surface_type if present
            if 'surface_type' in X:
                X = pd.get_dummies(X, columns=['surface_type'], prefix=['surface'])
                
            # Scale numerical features
            numerical_cols = ['distance', 'elevation_gain']
            numerical_cols = [col for col in numerical_cols if col in X.columns]
            if numerical_cols:
                X[numerical_cols] = self.scaler.fit_transform(X[numerical_cols])
            
            # Split data for training/validation
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train_type, y_val_type = y['route_type'][:split_idx], y['route_type'][split_idx:]
            y_train_diff, y_val_diff = y['difficulty'][:split_idx], y['difficulty'][split_idx:]
            
            # Initialize models if needed
            if self.route_classifier is None:
                self.route_classifier = RandomForestClassifier(**ModelConfig.RF_CLASSIFIER_PARAMS)
            if self.difficulty_predictor is None:
                self.difficulty_predictor = GradientBoostingRegressor(**ModelConfig.GB_REGRESSOR_PARAMS)
            
            # Train the classifier
            self.logger.info("Training Random Forest classifier...")
            self.route_classifier.fit(X_train, y_train_type)
            classifier_score = self.route_classifier.score(X_val, y_val_type)
            
            # Train the regressor
            self.logger.info("Training Gradient Boosting regressor...")
            self.difficulty_predictor.fit(X_train, y_train_diff)
            regressor_score = self.difficulty_predictor.score(X_val, y_val_diff)
            
            self.logger.info(f"Training scores - Classifier: {classifier_score:.3f}, Regressor: {regressor_score:.3f}")
            
            self.last_training_date = datetime.utcnow()
            self.model_version = f"1.1.{int(datetime.utcnow().timestamp())}"
            
            return self.save_models()
        except Exception as e:
            self.logger.error(f"Error training models: {str(e)}")
            return False

    def save_models(self) -> bool:
        """Save the trained models along with metadata."""
        try:
            if not (self.route_classifier and self.difficulty_predictor):
                raise ValueError("Models not initialized")
                
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            models = {
                'classifier': self.route_classifier,
                'regressor': self.difficulty_predictor,
                'scaler': self.scaler,
                'version': self.model_version,
                'training_date': self.last_training_date,
                'feature_names': list(self.route_classifier.feature_names_in_) if hasattr(self.route_classifier, 'feature_names_in_') else []
            }
            
            backup_path = f"{self.model_path}.backup"
            if os.path.exists(self.model_path):
                os.rename(self.model_path, backup_path)
            
            self.logger.info(f"Saving models to {self.model_path}")
            joblib.dump(models, self.model_path)
            
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
            return True
        except Exception as e:
            self.logger.error(f"Error saving models: {str(e)}")
            if os.path.exists(f"{self.model_path}.backup"):
                os.rename(f"{self.model_path}.backup", self.model_path)
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Retrieve model metadata and initialization info."""
        return {
            'version': self.model_version,
            'last_training_date': self.last_training_date.isoformat() if self.last_training_date else None,
            'classifier_type': type(self.route_classifier).__name__ if self.route_classifier else None,
            'regressor_type': type(self.difficulty_predictor).__name__ if self.difficulty_predictor else None,
            'required_features': self.required_features,
            'is_initialized': bool(self.route_classifier and self.difficulty_predictor)
        }
