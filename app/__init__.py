# __init__.py: Initializes the Flask application and configures MySQL.

from flask import Flask  # Import Flask to create the application
from flask_mysqldb import MySQL  # Import MySQL to connect Flask with the database
import os  # Import os to load environment variables
from dotenv import load_dotenv  # Load environment variables from a .env file

# Load environment variables from the .env file
load_dotenv()

# Initialize MySQL globally
mysql = MySQL()

def create_app():
    """
    Creates and configures the Flask application.
    Initializes MySQL and registers blueprints.
    """
    app = Flask(__name__)

    # Set MySQL configuration from environment variables
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

    # Initialize MySQL with the Flask app
    mysql.init_app(app)

    # Register blueprints (imported later to avoid circular imports)
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
