# app/routes/api.py
from flask import Blueprint, request, jsonify, current_app
from app.models import db, Route, Preference, Feedback
from app.ml.model_coordinator import ModelCoordinator
from functools import wraps
from typing import Dict, Any
import logging

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({
                'error': 'An error occurred processing your request',
                'detail': str(e) if current_app.debug else None
            }), 500
    return wrapper

@api_bp.route('/routes/search', methods=['GET'])
@handle_errors
def search_routes():
    # Get search parameters
    params = {
        'latitude': request.args.get('latitude', type=float),
        'longitude': request.args.get('longitude', type=float),
        'max_distance': request.args.get('max_distance', type=float),
        'route_type': request.args.get('route_type'),
        'elevation_preference': request.args.get('elevation_preference')
    }
    
    # Validate required parameters
    if not all([params['latitude'], params['longitude'], params['max_distance']]):
        return jsonify({
            'error': 'Missing required parameters: latitude, longitude, max_distance'
        }), 400

    # Get user preferences and model predictions
    try:
        user_preferences = get_user_preferences()
        model_coordinator = current_app.model_coordinator
        routes = Route.search_nearby(**params)
        
        enriched_routes = []
        for route in routes:
            try:
                predictions = model_coordinator.get_route_predictions(
                    route.id,
                    user_preferences
                )
                route_data = route.to_dict()
                route_data.update(predictions)
                enriched_routes.append(route_data)
            except Exception as e:
                logger.error(f"Error enriching route {route.id}: {str(e)}")
                continue
        
        return jsonify(enriched_routes)
        
    except Exception as e:
        logger.error(f"Error in route search: {e}")
        raise

@api_bp.route('/routes/<int:route_id>', methods=['GET'])
@handle_errors
def get_route_details(route_id: int):
    route = Route.query.get_or_404(route_id)
    
    try:
        user_preferences = get_user_preferences()
        model_coordinator = current_app.model_coordinator
        predictions = model_coordinator.get_route_predictions(
            route_id,
            user_preferences
        )
        
        route_data = route.to_dict()
        route_data.update(predictions)
        
        return jsonify(route_data)
    except Exception as e:
        logger.error(f"Error getting route details for {route_id}: {e}")
        raise

@api_bp.route('/feedback', methods=['POST'])
@handle_errors
def submit_feedback():
    data = request.get_json()
    
    # Validate input
    required_fields = ['route_id', 'user_id', 'rating']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if not isinstance(data['rating'], int) or not 1 <= data['rating'] <= 5:
        return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
    
    try:
        # Save feedback
        feedback = Feedback(
            route_id=data['route_id'],
            user_id=data['user_id'],
            rating=data['rating'],
            comment=data.get('comment')
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        # Update model predictions cache
        model_coordinator = current_app.model_coordinator
        model_coordinator.get_route_predictions.cache_clear()
        
        return jsonify({'message': 'Feedback submitted successfully'})
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise

def get_user_preferences() -> Dict[str, Any]:
    """Get current user preferences or defaults"""
    # TODO: Implement user authentication and get actual user preferences
    return {
        'traffic_preference': 'neutral',
        'surface_preference': 'asphalt',
        'require_lighting': False,
        'require_sidewalks': True
    }

# Initialize model coordinator
def init_api_routes(app):
    with app.app_context():
        try:
            app.model_coordinator = ModelCoordinator()
            success = app.model_coordinator.initialize_models()
            if not success:
                logger.error("Failed to initialize model coordinator")
                raise RuntimeError("Model coordinator initialization failed")
            logger.info("Model coordinator initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing model coordinator: {str(e)}")
            raise