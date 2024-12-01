# train_models.py

import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from app.ml.model_coordinator import ModelCoordinator
import logging
from flask import Flask

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def create_training_data():
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
    
    logger.info(f"Created routes_data with shape: {routes_data.shape}")
    
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
    
    logger.info(f"ANN features shape: {ann_features.shape}")
    logger.info(f"ANN labels shape: {quality_scores.shape}")
    
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
            # Check models directory
            model_dir = os.getenv("MODEL_DIR", "models")
            abs_model_dir = os.path.abspath(model_dir)
            logger.info(f"Using model directory: {abs_model_dir}")
            
            if not os.path.exists(abs_model_dir):
                os.makedirs(abs_model_dir)
                logger.info(f"Created model directory: {abs_model_dir}")
            
            # Initialize coordinator
            logger.info("Initializing ModelCoordinator...")
            coordinator = ModelCoordinator()
            
            # Generate and verify training data
            training_data = create_training_data()
            logger.info("Verifying training data shapes:")
            logger.info(f"RF features shape: {training_data['rf_features'].shape}")
            logger.info(f"RF route types shape: {training_data['rf_labels']['route_type'].shape}")
            logger.info(f"RF difficulty scores shape: {training_data['rf_labels']['difficulty'].shape}")
            logger.info(f"ANN features shape: {training_data['ann_features'].shape}")
            logger.info(f"ANN labels shape: {training_data['ann_labels'].shape}")
            
            # Train models
            logger.info("Starting model training...")
            success = coordinator.update_models(training_data)
            
            if success:
                # Verify files were created
                expected_files = ['pathfinder_model.pkl', 'pathfinder_ann.pkl', 'pathfinder_ann_metadata.json']
                existing_files = os.listdir(abs_model_dir)
                logger.info(f"Files in model directory after training: {existing_files}")
                
                missing_files = [f for f in expected_files if f not in existing_files]
                if missing_files:
                    logger.error(f"Missing expected model files: {missing_files}")
                else:
                    logger.info("All model files were created successfully!")
            else:
                logger.error("Model training reported failure")
                
    except Exception as e:
        logger.error(f"Error during training process: {str(e)}", exc_info=True)

if __name__ == "__main__":
    train_models()