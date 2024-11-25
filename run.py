# run.py: Entry point to start the Flask application

from app import create_app  # Import the create_app function to initialize the app

# Create the Flask app instance
app = create_app()

if __name__ == "__main__":
    # Use the Flask application context to initialize the AI model
    with app.app_context():
        try:
            from app.routes import fetch_route_data, preprocess_data
            from app.ann_model import train_ann_model

            # Example data for AI model initialization
            routes_df = fetch_route_data({'lat': 40.7128, 'lng': -74.0060})  # Default to NYC
            X, scaler, encoder = preprocess_data(routes_df)
            y = [1] * len(X)  # Example target data (all labeled 'good')
            ann_model = train_ann_model(X, y)  # Train the ANN model

            app.logger.info("AI model initialized successfully.")
        except Exception as e:
            app.logger.error(f"Error initializing AI model: {e}")

    # Start the Flask app with debug mode enabled
    app.run(debug=True)
