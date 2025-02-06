from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, validate, ValidationError
from bleach import clean
from app.models import db, Route, Preference, Feedback
from functools import wraps
from typing import Dict, Any
import logging

bp = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

# Initialize the rate limiter; it will be attached to the app later.
limiter = Limiter(
    get_remote_address,
    app=None,
    default_limits=["200 per day", "50 per hour"]
)

class RouteSearchSchema(Schema):
    latitude = fields.Float(required=True, validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(required=True, validate=validate.Range(min=-180, max=180))
    max_distance = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    route_type = fields.String(validate=validate.OneOf(['road', 'trail', 'mixed']))
    elevation_preference = fields.String(validate=validate.OneOf(['flat', 'moderate', 'challenging']))

class FeedbackSchema(Schema):
    route_id = fields.Integer(required=True, validate=validate.Range(min=1))
    user_id = fields.Integer(required=True, validate=validate.Range(min=1))
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    comment = fields.String(validate=validate.Length(max=1000))

search_schema = RouteSearchSchema()
feedback_schema = FeedbackSchema()

def sanitize_text(text: str) -> str:
    return clean(text, strip=True)

def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            return jsonify({'error': 'Validation error', 'details': e.messages}), 400
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({
                'error': 'An error occurred processing your request',
                'detail': str(e) if current_app.debug else None
            }), 500
    return wrapper

@bp.route('/routes/search', methods=['GET'])
@handle_errors
@limiter.limit("1 per second")
def search_routes():
    # Validate and load the query parameters.
    params = search_schema.load(request.args)
    user_preferences = get_user_preferences()
    model_coordinator = current_app.model_coordinator

    # Find nearby routes based on the search parameters.
    routes = Route.search_nearby(**params)
    enriched_routes = []
    for route in routes:
        try:
            predictions = model_coordinator.get_route_predictions(route.id, user_preferences)
            route_data = route.to_dict()
            route_data.update(predictions)
            enriched_routes.append(route_data)
        except Exception as e:
            logger.error(f"Error enriching route {route.id}: {str(e)}")
            continue

    return jsonify(enriched_routes)

@bp.route('/routes/<int:route_id>', methods=['GET'])
@handle_errors
@limiter.limit("1 per second")
def get_route_details(route_id: int):
    # Basic check for a valid route_id.
    if route_id < 1:
        return jsonify({'error': 'Invalid route ID'}), 400

    route = Route.query.get_or_404(route_id)
    user_preferences = get_user_preferences()
    model_coordinator = current_app.model_coordinator

    predictions = model_coordinator.get_route_predictions(route_id, user_preferences)
    route_data = route.to_dict()
    route_data.update(predictions)

    return jsonify(route_data)

@bp.route('/feedback', methods=['POST'])
@handle_errors
@limiter.limit("1 per second")
def submit_feedback():
    data = feedback_schema.load(request.get_json())

    if 'comment' in data:
        data['comment'] = sanitize_text(data['comment'])

    feedback = Feedback(
        route_id=data['route_id'],
        user_id=data['user_id'],
        rating=data['rating'],
        comment=data.get('comment')
    )
    db.session.add(feedback)
    db.session.commit()

    model_coordinator = current_app.model_coordinator
    # Clear any cached predictions if the method supports it.
    if hasattr(model_coordinator.get_route_predictions, "cache_clear"):
        model_coordinator.get_route_predictions.cache_clear()

    return jsonify({'message': 'Feedback submitted successfully'})

def get_user_preferences() -> Dict[str, Any]:
    """Return current user preferences or default values."""
    return {
        'traffic_preference': 'neutral',
        'surface_preference': 'asphalt',
        'require_lighting': False,
        'require_sidewalks': True
    }

def init_api_routes(app):
    """
    Initialize the API routes and rate limiter for the Flask app.
    Note: Model coordinator initialization is handled in app/__init__.py.
    """
    app.register_blueprint(bp)
    limiter.init_app(app)
    app.logger.info("API routes initialized successfully")
