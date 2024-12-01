# run.py
import logging
from app import create_app
from app.ml.ai_model import init_ai_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create the Flask app instance
app = create_app()

if __name__ == "__main__":
    # Initialize the AI model within the application context
    try:
        with app.app_context():
            init_ai_model()
            logger.info("AI model initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI model: {e}")
        raise
    
    # Start the Flask development server
    app.run(debug=True)