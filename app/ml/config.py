import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ModelConfig:
    # Base directory for all models
    MODEL_DIR = os.getenv('MODEL_DIR', 'models')
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Model file paths
    RF_MODEL_PATH = os.path.join(MODEL_DIR, 'pathfinder_model.pkl')
    ANN_MODEL_PATH = os.path.join(MODEL_DIR, 'pathfinder_ann.pkl')
    ANN_METADATA_PATH = os.path.join(MODEL_DIR, 'pathfinder_ann_metadata.json')
    
    # Model parameters for Random Forest classifier
    RF_CLASSIFIER_PARAMS = {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 5,
        'random_state': 42,
        'n_jobs': -1
    }
    
    # Model parameters for Gradient Boosting regressor
    GB_REGRESSOR_PARAMS = {
        'n_estimators': 100,
        'learning_rate': 0.1,
        'max_depth': 5,
        'random_state': 42
    }
    
    # ANN model parameters (if used elsewhere during training)
    ANN_PARAMS = {
        'hidden_layer_sizes': (128, 64, 32),
        'activation': 'relu',
        'solver': 'adam',
        'alpha': 0.0001,
        'batch_size': 32,
        'learning_rate': 'adaptive',
        'max_iter': 1000,
        'early_stopping': True,
        'validation_fraction': 0.1,
        'n_iter_no_change': 10,
        'random_state': 42
    }
    
    # Expected features for models
    REQUIRED_FEATURES = [
        'distance',
        'elevation_gain',
        'has_sidewalks',
        'is_lit',
        'surface_type'
    ]
    
    ANN_FEATURES = [
        'distance',
        'elevation_gain',
        'traffic_level',
        'surface_quality',
        'safety_score'
    ]
