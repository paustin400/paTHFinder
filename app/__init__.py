# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import logging

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
logger = logging.getLogger(__name__)

def create_app():
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_env_vars = ['MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_HOST', 'MYSQL_DB']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Initialize Flask app
    app = Flask(__name__)
    
    try:
        # Configure app
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+pymysql://{os.getenv('MYSQL_USER')}:"
            f"{os.getenv('MYSQL_PASSWORD')}@"
            f"{os.getenv('MYSQL_HOST')}/"
            f"{os.getenv('MYSQL_DB')}"
        )
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['GOOGLE_MAPS_API_KEY'] = os.getenv('GOOGLE_MAPS_API_KEY')
        
        # Initialize extensions
        db.init_app(app)
        migrate.init_app(app, db)
        
        # Register routes
        from .routes import init_routes
        init_routes(app)
        
        logger.info("Application initialized successfully")
        return app
        
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        raise
