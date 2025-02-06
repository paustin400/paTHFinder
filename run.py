import logging
from app import create_app
from app.ml.model_coordinator import ModelCoordinator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def init_application():
    try:
        app = create_app()
        with app.app_context():
            coordinator = ModelCoordinator()
            if not coordinator.initialize_models():
                logger.warning("ML models initialization failed - will use fallback predictions")
            app.model_coordinator = coordinator
        return app
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

if __name__ == "__main__":
    app = init_application()
    app.run(debug=True, host='0.0.0.0', port=5000)