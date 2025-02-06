from flask import Blueprint, render_template, request, redirect, url_for, current_app, session
from app.models import get_route_details, Preference
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET'], endpoint='homepage')
def homepage():
    return render_template('home.html')

@bp.route('/search', methods=['GET'])
def search_page():
    """Render the search page."""
    try:
        google_maps_api_key = current_app.config.get('GOOGLE_MAPS_API_KEY', '')
        if not google_maps_api_key:
            current_app.logger.warning('Google Maps API key not configured')

        # Use the existing model coordinator to determine if AI is enabled
        ai_enabled = current_app.model_coordinator is not None

        # Collect search parameters from the query string
        template_vars = {
            'ai_enabled': ai_enabled,
            'google_maps_api_key': google_maps_api_key,
            'route_type': request.args.get('route_type', 'road'),
            'elevation': request.args.get('elevation', 'flat'),
            'require_sidewalks': request.args.get('require_sidewalks', 'false').lower() == 'true'
        }

        return render_template('search.html', **template_vars)
    except Exception as e:
        current_app.logger.error(f"Error rendering search page: {e}")
        return render_template('error.html', error=str(e))

@bp.route('/preferences', methods=['GET'])
def preferences_page():
    """Render the preferences page."""
    try:
        # Retrieve user preferences from the session/database if available
        user_preferences = None
        if 'user_id' in session:
            user_preferences = Preference.query.filter_by(user_id=session['user_id']).first()

        # Default preferences
        preferences = {
            'route_type': 'road',
            'elevation_preference': 'flat',
            'surface_preference': 'pavement',
            'traffic_preference': 'avoid',
            'crowd_preference': 'quiet',
            'well_lit': False,
            'require_sidewalks': False
        }

        # Update default preferences if the user has saved preferences
        if user_preferences:
            preferences.update(user_preferences.to_dict())

        # Allow query parameters to override default/user preferences
        for key in preferences:
            value = request.args.get(key)
            if value is not None:
                if isinstance(preferences[key], bool):
                    preferences[key] = value.lower() == 'true'
                else:
                    preferences[key] = value

        return render_template('preferences.html', preferences=preferences)
    except Exception as e:
        current_app.logger.error(f"Error rendering preferences page: {e}")
        return render_template('error.html', error=str(e))

@bp.app_template_filter('get_difficulty_label')
def get_difficulty_label(score: float) -> str:
    if not isinstance(score, (int, float)):
        return "Unknown"
    if score < 0.3:
        return "Easy"
    elif score < 0.6:
        return "Moderate"
    elif score < 0.8:
        return "Challenging"
    return "Very Challenging"

@bp.app_template_filter('tojson')
def to_json(value):
    from flask import json
    return json.dumps(value)

def prepare_ai_analysis(route_data, user_preferences=None):
    """
    Use the centralized model coordinator (already attached to the app) to
    retrieve AI predictions and prepare descriptive route features.
    """
    try:
        # Use the model coordinator initialized in app/__init__.py
        coordinator = current_app.model_coordinator
        if not coordinator:
            logger.error("Model coordinator not initialized")
            return None

        # Extract route ID (supports both dicts and objects)
        route_id = (
            route_data.get('id')
            if isinstance(route_data, dict)
            else getattr(route_data, 'id', None)
        )
        if route_id is None:
            logger.error("Invalid route data format: missing route id")
            return None

        # Get predictions from the coordinator (e.g., route type and difficulty)
        predictions = coordinator.get_route_predictions(route_id, user_preferences or {})

        # Build a list of descriptive features based on the predictions and route details
        features = []
        if predictions.get('route_type') == 'road':
            features.append("Road running with good pavement")
        elif predictions.get('route_type') == 'trail':
            features.append("Trail running with natural surfaces")

        has_sidewalks = (
            route_data.get('has_sidewalks')
            if isinstance(route_data, dict)
            else getattr(route_data, 'has_sidewalks', False)
        )
        is_lit = (
            route_data.get('is_lit')
            if isinstance(route_data, dict)
            else getattr(route_data, 'is_lit', False)
        )

        if has_sidewalks:
            features.append("Dedicated sidewalks available")
        if is_lit:
            features.append("Well-lit route")

        difficulty = get_difficulty_label(predictions.get('difficulty_score', 0))
        features.append(f"{difficulty} difficulty level")

        predictions['route_features'] = features
        return predictions

    except Exception as e:
        logger.error(f"Error preparing AI analysis: {e}")
        return None

@bp.route('/route/<int:route_id>', methods=['GET'])
def route_detail_page(route_id):
    try:
        route = get_route_details(route_id)
        if not route:
            return render_template('404.html'), 404

        user_preferences = None
        if 'user_id' in session:
            preferences = Preference.query.filter_by(user_id=session['user_id']).first()
            if preferences:
                user_preferences = preferences.to_dict()

        ai_analysis = prepare_ai_analysis(route, user_preferences)

        return render_template(
            'route_detail.html',
            route=route,
            ai_analysis=ai_analysis
        )
    except Exception as e:
        logger.error("Error retrieving route %s: %s", route_id, str(e))
        return render_template('500.html'), 500
