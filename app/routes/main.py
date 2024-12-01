# app/routes/main.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models import get_route_details
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET'])
def homepage():
    return render_template('home.html')

@bp.route('/search', methods=['GET'])
def search_page():
    return render_template('search.html')

@bp.route('/preferences', methods=['GET'])
def preferences_page():
    # Initialize default preferences
    preferences = {
        'route_type': 'road',  # default value
        'elevation': 'flat',   # default value
        'surface': 'pavement', # default value
        'traffic': 'low',      # default value
        'crowd': 'quiet',      # default value
        'well_lit': True,      # default value
        'sidewalks': True      # default value
    }
    return render_template('preferences.html', preferences=preferences)

@bp.route('/route/<int:route_id>', methods=['GET'])
def route_detail_page(route_id):
    try:
        route = get_route_details(route_id)
        if not route:
            logger.warning(f"Route not found: {route_id}")
            return render_template('404.html'), 404
        return render_template('route_detail.html', route=route)
    except Exception as e:
        logger.error(f"Error retrieving route {route_id}: {e}")
        return render_template('error.html'), 500

@bp.route('/search-results', methods=['GET'])
def search_results_page():
    return render_template('search_results.html')