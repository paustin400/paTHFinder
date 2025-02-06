import os
from flask_talisman import Talisman
from datetime import timedelta
from flask import request

class ModelConfig:
    RF_MODEL_PATH = os.path.join('models', 'pathfinder_model.pkl')
    REQUIRED_FEATURES = ['distance', 'elevation_gain', 'has_sidewalks', 'is_lit', 'surface_type']
    RF_CLASSIFIER_PARAMS = {
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': 42
    }
    GB_REGRESSOR_PARAMS = {
        'n_estimators': 100,
        'learning_rate': 0.1,
        'random_state': 42
    }

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_DB = os.environ.get('MYSQL_DB')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    MODEL_DIR = os.environ.get('MODEL_DIR', 'models')

def init_security(app):
    from flask import request
    # Define CSP with additional allowed domains:
    csp = {
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",
            "https://code.jquery.com",
            "https://cdn.jsdelivr.net",
            "https://*.googleapis.com",
            "https://*.gstatic.com",
            "https://maps.googleapis.com",
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            "https://fonts.googleapis.com",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",  # Added for Font Awesome
            "https://*.googleapis.com",
            "https://*.gstatic.com",
        ],
        'img-src': [
            "'self'",
            "data:",
            "blob:",
            "https://*.googleapis.com",
            "https://*.gstatic.com",
            "https://maps.googleapis.com",
        ],
        'font-src': [
            "'self'",
            "https://fonts.gstatic.com",
            "https://cdnjs.cloudflare.com",
            "https://cdn.jsdelivr.net"
        ],
        'connect-src': [
            "'self'",
            "https://*.googleapis.com",
            "https://*.gstatic.com",
            "https://maps.googleapis.com",
        ],
        'worker-src': ["'self'", "blob:"],
        'child-src': ["'self'", "blob:"],
        'frame-src': ["'self'", "https://*.googleapis.com"],
        'manifest-src': ["'self'"]
    }

    @app.before_request
    def before_request_func():
        if app.debug:
            # Append local development URLs only once.
            for directive, sources in csp.items():
                if "http://127.0.0.1:5000" not in sources:
                    sources.append("http://127.0.0.1:5000")
                if "http://localhost:5000" not in sources:
                    sources.append("http://localhost:5000")

    @app.after_request
    def add_security_headers(response):
        csp_string = '; '.join(
            f"{directive} {' '.join(sorted(set(sources)))}"
            for directive, sources in csp.items()
        )
        response.headers['Content-Security-Policy'] = csp_string
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        if request.path.startswith('/static/'):
            response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    
    return app
