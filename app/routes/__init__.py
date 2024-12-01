# app/routes/__init__.py
def init_routes(app):
    # Import blueprints
    from .main import bp as main_bp
    from .api import api_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(main_bp)  # Main routes (/, /search, etc.)
    app.register_blueprint(api_bp, url_prefix='/api')  # All API routes under /api