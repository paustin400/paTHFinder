def init_routes(app):
    # Import blueprints from the submodules
    from .main import bp as main_bp
    from .api import bp as api_bp

    # Register blueprints with the application
    app.register_blueprint(main_bp)              # Routes for the main site (e.g., '/')
    app.register_blueprint(api_bp, url_prefix='/api')  # Routes under '/api'

    app.logger.info("Routes initialized successfully")
