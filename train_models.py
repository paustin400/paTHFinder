# train_models.py

import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from app.ml.model_coordinator import ModelCoordinator
import logging
from flask import Flask
import json

# Enhanced logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verify_model_files(model_dir):
    """Verify model files exist and are valid"""
    files_status = {}
    expected_files = {
        'pathfinder_model.pkl': 0,
        'pathfinder_ann.pkl': 0,
        'pathfinder_ann_metadata.json': 0
    }
    
    for file in os.listdir(model_dir):
        if file in expected_files:
            size = os.path.getsize(os.path.join(model_dir, file))
            files_status[file] = {
                'exists': True,
                'size': size,
                'valid': size > 0
            }
            logger.info(f"Found {file}: {size} bytes")
    
    return files_status

def log_data_info(data, name):
    """Safely log information about data arrays"""
    if isinstance(data, np.ndarray):
        if data.dtype.kind in ['i', 'f']:  # Integer or float
            logger.info(f"{name} - Shape: {data.shape}, Range: [{data.min():.2f}, {data.max():.2f}]")
        else:  # String or other types
            logger.info(f"{name} - Shape: {data.shape}, Types: {np.unique(data).tolist()}")
    elif isinstance(data, pd.DataFrame):
        logger.info(f"{name} - Shape: {data.shape}")
        for column in data.columns:
            if data[column].dtype.kind in ['i', 'f']:
                logger.info(f"  {column} - Range: [{data[column].min():.2f}, {data[column].max():.2f}]")
            else:
                logger.info(f"  {column} - Unique values: {data[column].unique().tolist()}")

def create_training_data():
    """Generate and validate training data"""
    logger.info("Generating sample training data...")
    n_samples = 200
    
    # Create sample routes data
    routes_data = pd.DataFrame({
        'distance': np.random.uniform(1, 15, n_samples),
        'elevation_gain': np.random.uniform(0, 500, n_samples),
        'has_sidewalks': np.random.choice([0, 1], n_samples),
        'is_lit': np.random.choice([0, 1], n_samples),
        'surface_type': np.random.choice(['asphalt', 'dirt', 'grass'], n_samples)
    })
    
    route_types = np.random.choice(['easy', 'moderate', 'challenging'], n_samples)
    difficulty_scores = np.clip(np.random.normal(0.5, 0.2, n_samples), 0, 1)
    
    ann_features = np.column_stack([
        routes_data['distance'],
        routes_data['elevation_gain'],
        np.random.uniform(0, 1, n_samples),  # traffic_level
        np.random.uniform(0, 1, n_samples),  # surface_quality
        np.random.uniform(0.5, 1, n_samples)  # safety_score
    ])
    
    quality_scores = np.clip(np.random.normal(0.7, 0.15, n_samples), 0, 1)
    
    # Save sample data for verification
    sample_data = {
        'routes_data': routes_data.head().to_dict(),
        'route_types': route_types[:5].tolist(),
        'difficulty_scores': difficulty_scores[:5].tolist(),
        'quality_scores': quality_scores[:5].tolist()
    }
    
    with open('sample_training_data.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    logger.info("Saved sample training data to sample_training_data.json")
    
    return {
        'rf_features': routes_data,
        'rf_labels': {
            'route_type': route_types,
            'difficulty': difficulty_scores
        },
        'ann_features': ann_features,
        'ann_labels': quality_scores
    }

def train_models():
    try:
        # Create Flask app context
        app = Flask(__name__)
        with app.app_context():
            # Setup model directory
            model_dir = os.getenv("MODEL_DIR", "models")
            abs_model_dir = os.path.abspath(model_dir)
            logger.info(f"Using model directory: {abs_model_dir}")
            
            if not os.path.exists(abs_model_dir):
                os.makedirs(abs_model_dir)
                logger.info(f"Created model directory: {abs_model_dir}")
            
            # Check existing model files
            logger.info("Checking existing model files...")
            initial_files = verify_model_files(abs_model_dir)
            
            # Initialize coordinator
            logger.info("Initializing ModelCoordinator...")
            coordinator = ModelCoordinator()
            
            # Generate and verify training data
            training_data = create_training_data()
            
            # Log data information safely
            logger.info("Training data summary:")
            log_data_info(training_data['rf_features'], "RF Features")
            log_data_info(training_data['rf_labels']['route_type'], "Route Types")
            log_data_info(training_data['rf_labels']['difficulty'], "Difficulty Scores")
            log_data_info(training_data['ann_features'], "ANN Features")
            log_data_info(training_data['ann_labels'], "Quality Scores")
            
            # Train models
            logger.info("Starting model training...")
            success = coordinator.update_models(training_data)
            
            if success:
                logger.info("Model training reported success. Verifying files...")
                final_files = verify_model_files(abs_model_dir)
                
                # Compare initial and final states
                new_files = {k: v for k, v in final_files.items() if k not in initial_files}
                updated_files = {k: v for k, v in final_files.items() if k in initial_files and v != initial_files[k]}
                
                if new_files:
                    logger.info(f"New files created: {new_files}")
                if updated_files:
                    logger.info(f"Files updated: {updated_files}")
                
                return True
            else:
                logger.error("Model training reported failure")
                return False
                
    except Exception as e:
        logger.error(f"Error during training process: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = train_models()
    if success:
        logger.info("Training completed successfully")
    else:
        logger.error("Training failed")