import requests
import os
import random
from math import radians, cos, sin, asin, sqrt, pi
from flask import current_app
from . import mysql

def generate_and_store_routes(location, proximity, desired_distance):
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={api_key}"
    response = requests.get(geocode_url)
    if response.status_code != 200:
        current_app.logger.error("Error fetching geocode data; status code: " + str(response.status_code))
        return []
    location_data = response.json()
    if location_data.get('status') != 'OK':
        current_app.logger.error("Geocode API error: " + location_data.get('status', 'Unknown error'))
        return []
    loc_lat = location_data['results'][0]['geometry']['location']['lat']
    loc_lng = location_data['results'][0]['geometry']['location']['lng']
    
    routes = generate_routes(loc_lat, loc_lng, proximity, desired_distance)
    store_routes(routes)
    return routes

def generate_routes(lat, lng, proximity, distance_km):
    routes = []
    num_points = 8
    for i in range(5):
        start_lat, start_lng = lat, lng
        waypoints = []
        radius = distance_km * 1000 / (2 * pi)
        for j in range(num_points):
            angle = (2 * pi * j) / num_points
            point_lat = start_lat + (radius * cos(angle)) / 111111
            point_lng = start_lng + (radius * sin(angle)) / (111111 * cos(radians(start_lat)))
            waypoints.append((point_lat, point_lng))
        actual_distance = calculate_route_distance(waypoints)
        routes.append({
            'name': f'Route {i+1}',
            'description': f'{distance_km}km {get_route_description()}',
            'latitude': start_lat,
            'longitude': start_lng,
            'distance': actual_distance,
            'waypoints': waypoints
        })
    return routes

def calculate_route_distance(waypoints):
    total_distance = 0
    for i in range(len(waypoints) - 1):
        lat1, lon1 = waypoints[i]
        lat2, lon2 = waypoints[i + 1]
        total_distance += haversine_distance(lat1, lon1, lat2, lon2)
    return total_distance

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def get_route_description():
    terrains = ['Urban', 'Park', 'Waterfront', 'Suburban', 'Trail']
    features = ['scenic views', 'well-lit paths', 'tree-lined streets', 'quiet neighborhoods']
    return f"{random.choice(terrains)} route with {random.choice(features)}"

def store_routes(routes):
    cursor = mysql.connection.cursor()
    for route in routes:
        cursor.execute(
            """INSERT INTO Routes (name, description, latitude, longitude, distance) 
               VALUES (%s, %s, %s, %s, %s)""",
            (route['name'], route['description'], route['latitude'], 
             route['longitude'], route['distance'])
        )
    mysql.connection.commit()
    cursor.close()
