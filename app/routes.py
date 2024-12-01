from flask import Blueprint, request, jsonify, render_template, current_app
from app.models import search_routes, save_preferences, submit_feedback, get_route_details
from app.ml.ann_model import PathfinderANN, prepare_route_features
from sqlalchemy.exc import SQLAlchemyError
import numpy as np

bp = Blueprint('routes', __name__)
ann_model = None

def get_ann_model():
    global ann_model
    if ann_model is None:
        ann_model = PathfinderANN()
        ann_model.load_model()
    return ann_model

# Web Routes (HTML Templates)
@bp.route('/', methods=['GET'])
def homepage():
    return render_template('home.html')

@bp.route('/search', methods=['GET'])
def search_page():
    return render_template('search.html')

@bp.route('/preferences', methods=['GET'])
def preferences_page():
    return render_template('preferences.html')

@bp.route('/route/<int:route_id>', methods=['GET'])
def route_detail_page(route_id):
    route = get_route_details(route_id)
    if not route:
        return render_template('404.html'), 404
    return render_template('route_detail.html', route=route)

@bp.route('/search-results', methods=['GET'])
def search_results_page():
    return render_template('search_results.html')

# API Routes (JSON Responses)
@bp.route('/api/routes/search', methods=['GET'])
def api_search():
    try:
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)
        max_distance = request.args.get('max_distance', type=float)
        route_type = request.args.get('route_type', type=str)
        elevation_preference = request.args.get('elevation_preference', type=str)

        if not all([latitude, longitude, max_distance]):
            return jsonify({
                'error': 'Missing required parameters: latitude, longitude, max_distance'
            }), 400

        routes = search_routes(latitude, longitude, max_distance, route_type, elevation_preference)
        model = get_ann_model()
        
        route_list = []
        for route in routes:
            try:
                features = prepare_route_features({
                    'distance': float(route.distance),
                    'elevation_gain': float(route.elevation_gain) if route.elevation_gain else 0,
                    'traffic_level': 0.5,  # Default values for missing features
                    'surface_quality': 0.7,
                    'safety_score': 0.8
                })
                quality_score = float(model.predict_route_quality(features)[0][0])
            except Exception as e:
                quality_score = None
                
            route_list.append({
                'id': route.id,
                'name': route.name,
                'distance': float(route.distance),
                'latitude': float(route.latitude),
                'longitude': float(route.longitude),
                'elevation_gain': float(route.elevation_gain) if route.elevation_gain else None,
                'average_rating': route.average_rating,
                'quality_score': quality_score
            })
        
        return jsonify(route_list)

    except ValueError as e:
        return jsonify({'error': 'Invalid parameter format'}), 400
    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/routes/<int:route_id>', methods=['GET'])
def api_route_details(route_id):
    try:
        route = get_route_details(route_id)
        if not route:
            return jsonify({'error': 'Route not found'}), 404
            
        model = get_ann_model()
        try:
            features = prepare_route_features({
                'distance': float(route['distance']),
                'elevation_gain': float(route['elevation_gain']) if route['elevation_gain'] else 0,
                'traffic_level': 0.5,
                'surface_quality': 0.7,
                'safety_score': 0.8
            })
            route['quality_score'] = float(model.predict_route_quality(features)[0][0])
        except Exception as e:
            route['quality_score'] = None
            
        return jsonify(route)

    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/preferences', methods=['POST'])
def api_preferences():
    try:
        data = request.get_json()
        required_fields = ['user_id', 'route_type', 'elevation_preference', 
                         'surface_preference', 'traffic_preference', 'crowd_preference']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        save_preferences(
            user_id=data['user_id'],
            route_type=data['route_type'],
            elevation_preference=data['elevation_preference'],
            surface_preference=data['surface_preference'],
            traffic_preference=data['traffic_preference'],
            crowd_preference=data['crowd_preference']
        )
        return jsonify({'message': 'Preferences saved successfully'})

    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/api/feedback', methods=['POST'])
def api_feedback():
    try:
        data = request.get_json()
        required_fields = ['route_id', 'user_id', 'rating']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        if not isinstance(data['rating'], int) or not 1 <= data['rating'] <= 5:
            return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400

        submit_feedback(
            route_id=data['route_id'],
            user_id=data['user_id'],
            rating=data['rating'],
            comment=data.get('comment')
        )
        return jsonify({'message': 'Feedback submitted successfully'})

    except SQLAlchemyError as e:
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400