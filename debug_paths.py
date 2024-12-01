import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def check_paths():
    # Get the absolute path of the current directory
    current_dir = os.path.abspath(os.getcwd())
    logger.info(f"Current working directory: {current_dir}")
    
    # Get the MODEL_DIR from environment
    model_dir = os.getenv("MODEL_DIR", "models")
    model_dir_abs = os.path.abspath(model_dir)
    logger.info(f"Model directory from env: {model_dir}")
    logger.info(f"Absolute model directory: {model_dir_abs}")
    
    # Check if directory exists
    logger.info(f"Model directory exists: {os.path.exists(model_dir_abs)}")
    
    # List contents if directory exists
    if os.path.exists(model_dir_abs):
        contents = os.listdir(model_dir_abs)
        logger.info(f"Contents of model directory: {contents}")

if __name__ == "__main__":
    check_paths()