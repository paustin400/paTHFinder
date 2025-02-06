import os
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
import logging
from datetime import datetime
import json
import pickle
import warnings
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning
from .config import ModelConfig

warnings.filterwarnings('ignore', category=ConvergenceWarning)

def prepare_route_features(route_data: Dict[str, float]) -> np.ndarray:
    """Prepare features for the ANN model in a consistent order."""
    features = np.array([
        route_data.get('distance', 0.0),
        route_data.get('elevation_gain', 0.0),
        route_data.get('traffic_level', 0.5),
        route_data.get('surface_quality', 0.7),
        route_data.get('safety_score', 0.8)
    ]).reshape(1, -1)
    return features

class PathfinderANN:
    def __init__(self):
        self.model_dir = os.getenv("MODEL_DIR", "models")
        os.makedirs(self.model_dir, exist_ok=True)
        self.model_path = os.path.join(self.model_dir, "pathfinder_ann.pkl")
        self.metadata_path = os.path.join(self.model_dir, "pathfinder_ann_metadata.json")
        self.model: Optional[MLPRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.input_shape: Optional[int] = 5
        self.logger = logging.getLogger(__name__)
        self.model_version = "1.0.0"
        self.last_training_date: Optional[datetime] = None
        self.feature_names: List[str] = [
            'distance', 'elevation_gain', 'traffic_level',
            'surface_quality', 'safety_score'
        ]

    def build_model(self) -> None:
        """Build a new ANN model using sklearn's MLPRegressor."""
        try:
            self.logger.info("Building new ANN model...")
            self.scaler = StandardScaler()
            self.model = MLPRegressor(
                hidden_layer_sizes=(128, 64, 32),
                activation='relu',
                solver='adam',
                alpha=0.0001,
                batch_size=32,
                learning_rate='adaptive',
                max_iter=1000,
                early_stopping=True,
                validation_fraction=0.1,
                n_iter_no_change=10,
                random_state=42
            )
            self.logger.info("ANN model built successfully")
        except Exception as e:
            self.logger.error(f"Error building ANN model: {str(e)}")
            raise

    def load_model(self) -> bool:
        """Load the saved ANN model and its metadata."""
        try:
            if not os.path.exists(self.model_path):
                self.logger.warning(f"No saved ANN model found at {self.model_path}")
                self.build_model()
                return True

            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.scaler = model_data['scaler']

            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
                    self.model_version = metadata.get('version', self.model_version)
                    self.last_training_date = datetime.fromisoformat(
                        metadata.get('training_date', datetime.utcnow().isoformat())
                    )
                    self.feature_names = metadata.get('feature_names', self.feature_names)
            return True
        except Exception as e:
            self.logger.error(f"Error loading ANN model: {str(e)}")
            self.build_model()  # Build new model as fallback
            return True

    def train(self, features: np.ndarray, labels: np.ndarray) -> Tuple[bool, Dict[str, float]]:
        """Train the ANN model with provided data."""
        try:
            if not self.model:
                self.build_model()

            X = np.array(features)
            y = np.array(labels).ravel()

            X_scaled = self.scaler.fit_transform(X)

            self.logger.info("Starting ANN model training...")
            self.model.fit(X_scaled, y)

            train_score = self.model.score(X_scaled, y)
            metrics = {
                'r2_score': float(train_score),
                'loss': float(self.model.loss_),
                'n_iter': int(self.model.n_iter_)
            }

            self.last_training_date = datetime.utcnow()
            self.model_version = f"1.1.{int(datetime.utcnow().timestamp())}"
            
            self.save_model(metrics)
            
            self.logger.info(f"ANN training completed. Metrics: {metrics}")
            return True, metrics
        except Exception as e:
            self.logger.error(f"Error training ANN model: {str(e)}")
            return False, {}

    def predict_route_quality(self, features: np.ndarray) -> np.ndarray:
        """Predict the route quality score using the ANN model."""
        try:
            if not self.model:
                if not self.load_model():
                    raise ValueError("ANN model not initialized and couldn't be loaded")
            features = np.array(features)
            if len(features.shape) == 1:
                features = features.reshape(1, -1)
            features_scaled = self.scaler.transform(features)
            predictions = self.model.predict(features_scaled)
            predictions = np.clip(predictions, 0, 1)
            return predictions.reshape(-1, 1)
        except Exception as e:
            self.logger.error(f"Error making ANN predictions: {str(e)}")
            return np.array([[0.5]])  # Neutral prediction as fallback

    def save_model(self, metrics: Optional[Dict[str, float]] = None) -> bool:
        """Save the ANN model and metadata to disk."""
        try:
            if not self.model:
                raise ValueError("No ANN model to save")
            model_data = {
                'model': self.model,
                'scaler': self.scaler
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)

            metadata = {
                'version': self.model_version,
                'training_date': self.last_training_date.isoformat(),
                'feature_names': self.feature_names,
                'input_shape': self.input_shape,
                'metrics': metrics or {}
            }
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving ANN model: {str(e)}")
            return False
