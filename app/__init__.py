# app/__init__.py

from flask import Flask, render_template, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import logging
import os
from .config import Config, init_security

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(test_config=None):
    app = Flask(__name__,
                static_folder='static',
                static_url_path='/static',
                template_folder='templates')
    
    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.update(test_config)

    # Initialize the database and migrations BEFORE using db.create_all()
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    with app.app_context():
        from . import models
        # Now that db is registered with the app, create tables:
        db.create_all()

        # Initialize model coordinator and routes (example)
        try:
            from .ml.model_coordinator import ModelCoordinator
            app.model_coordinator = ModelCoordinator()
            if not app.model_coordinator.initialize_models():
                app.logger.error("Failed to initialize model coordinator")
                raise RuntimeError("Model coordinator initialization failed")
            app.logger.info("Model coordinator initialized successfully")
        except Exception as e:
            app.logger.error(f"Error initializing model coordinator: {e}")
            raise

        try:
            from .routes import init_routes
            init_routes(app)
            app.logger.info("Routes initialized successfully")
        except Exception as e:
            app.logger.error(f"Failed to initialize routes: {e}")
            raise

        # Initialize security features after routes
        init_security(app)

    # Configure context processor and error handlers
    @app.context_processor
    def utility_processor():
        return {
            'static_url': lambda filename: url_for('static', filename=filename, _external=True),
            'google_maps_api_key': app.config.get('GOOGLE_MAPS_API_KEY')
        }

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Configure logging (if needed)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
    app.logger.info("Application initialization completed successfully")
    return app
