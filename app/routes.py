# routes.py: Defines the URL routes and their corresponding functions for the Flask app.
from flask import Blueprint, render_template, request, jsonify, current_app
from .models import search_routes, save_preferences, submit_feedback, get_route_details
from .utils import generate_and_store_routes
from .ai_model import fetch_route_data, preprocess_data  # AI model imports
from .ann_model import train_ann_model  # Import the ANN model logic
import json

# Create a Blueprint for the 'main' part of the application.
main = Blueprint('main', __name__)

# Initialize AI Model once when the app starts to save resources
try:
    routes_df = fetch_route_data({'lat': 40.7128, 'lng': -74.0060})  # Default: NYC
    X, scaler, encoder = preprocess_data(routes_df)
    y = [1] * len(X)  # Example target data for demo purposes (all labeled 'good')
    ann_model = train_ann_model(X, y)  # Train the ANN model
    current_app.logger.info("AI model initialized successfully.")
except Exception as e:
    current_app.logger.error(f"Error initializing AI model: {e}")

# Route for the home page
@main.route('/')
def home():
    return render_template('home.html')  # Render 'home.html' template

# Route for the search page with AI-enhanced suggestions
@main.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        try:
            # Log form data for debugging
            current_app.logger.info(f"Form Data: {request.form}")

            # Get inputs from the user
            location = request.form.get('location')
            proximity = float(request.form.get('proximity'))

            # Validate input
            if not location or not proximity:
                raise ValueError("All fields are required.")

            # Fetch location coordinates using Google Maps API
            coordinates = get_location_coordinates(location)

            # Fetch and preprocess routes for the given location
            routes_df = fetch_route_data(coordinates, proximity)
            X, _, _ = preprocess_data(routes_df)

            # Use the ANN model to predict route quality
            predictions = ann_model.predict(X).flatten()
            routes_df['score'] = predictions  # Add scores to DataFrame

            # Select top 10 routes
            top_routes = routes_df.nlargest(10, 'score').to_dict(orient='records')

            # Render search results with AI suggestions
            return render_template('search_results.html', routes=top_routes)

        except ValueError as ve:
            current_app.logger.error(f"Validation Error: {ve}")
            return render_template('search.html', error_message=str(ve)), 400

        except Exception as e:
            current_app.logger.error(f"Unexpected Error: {e}")
            return render_template('search.html', error_message="An unexpected error occurred."), 500

    # If GET request, render the search page
    return render_template('search.html')

# Utility function to fetch coordinates from Google Maps API
def get_location_coordinates(location_name):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location_name}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url).json()

    if response['status'] != 'OK':
        raise ValueError("Invalid location")

    loc = response['results'][0]['geometry']['location']
    return {'lat': loc['lat'], 'lng': loc['lng']}

# Route for showing search results (for pre-generated or mock data)
@main.route('/search_results')
def search_results():
    routes = [{'name': 'Route 1', 'latitude': 38.897957, 'longitude': -77.036560, 'distance': 5}]
    routes_json = json.dumps(routes)
    return render_template('search_results.html', routes_json=routes_json)

# Route to handle user preferences
@main.route('/preferences', methods=['GET', 'POST'])
def preferences():
    if request.method == 'POST':
        user_id = request.form['user_id']
        route_type = request.form['route_type']

        # Save preferences to the database
        save_preferences(user_id, route_type)
        return 'Preferences Saved!'

    return render_template('preferences.html')

# Route to handle user feedback submission
@main.route('/feedback', methods=['POST'])
def feedback():
    route_id = request.form['route_id']
    user_id = request.form['user_id']
    rating = request.form['rating']
    comment = request.form['comment']

    # Save feedback to the database
    submit_feedback(route_id, user_id, rating, comment)
    return 'Feedback Received!'

# Route to display the details of a specific route
@main.route('/route/<int:route_id>')
def route_detail(route_id):
    route = get_route_details(route_id)
    return render_template('route_detail.html', route=route)
