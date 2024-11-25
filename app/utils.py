# This file contains helper functions used across the application.
# It handles generating random running routes based on user input (location, distance, proximity).
# It also interacts with external APIs (like Google Maps) to get data and store routes in the database.

import requests
import os
import random
from math import radians, cos, sin, asin, sqrt, pi
from app import mysql

# This function generates and stores routes based on user inputs: location, proximity, and desired distance.
# It uses the Google Maps API to get the latitude and longitude of the provided location.
def generate_and_store_routes(location, proximity, desired_distance):
    # Retrieve the Google Maps API key from environment variables.
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    # Construct the URL to call the Google Maps Geocode API to get latitude and longitude from the location.
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={api_key}"
    
    # Make a request to the Geocode API.
    location_response = requests.get(geocode_url)
    
    # Parse the response from the API to extract location data.
    location_data = location_response.json()

    # If the API response status is not 'OK', return an empty list, indicating the location wasn't valid.
    if location_data['status'] != 'OK':
        return []  # No valid location found.

    # Extract latitude and longitude from the API response.
    loc_lat = location_data['results'][0]['geometry']['location']['lat']
    loc_lng = location_data['results'][0]['geometry']['location']['lng']
    
    # Generate routes based on the latitude, longitude, proximity, and desired distance.
    routes = generate_routes(loc_lat, loc_lng, proximity, desired_distance)
    
    # Store the generated routes in the MySQL database.
    store_routes(routes)
    
    # Return the generated routes.
    return routes

# This function generates a list of random running routes based on a starting latitude and longitude.
# Parameters:
# - lat: The latitude of the starting location.
# - lng: The longitude of the starting location.
# - proximity: The radius around the starting location within which the routes should be generated.
# - distance_km: The target distance for the generated routes.
def generate_routes(lat, lng, proximity, distance_km):
    routes = []  # Initialize an empty list to store the generated routes.
    
    # Generate 10 random routes.
    for i in range(10):
        # Generate a random angle in radians (0 to 2π) for the direction of the route.
        angle = random.uniform(0, 2 * pi)
        
        # Apply a random variation to the distance (up to 20% of the desired distance).
        distance_variation = random.uniform(-0.2, 0.2) * distance_km
        actual_distance = distance_km + distance_variation
        
        # Calculate the change in latitude and longitude based on the proximity and the angle.
        d_lat = sin(angle) * (proximity / 111)  # Change in latitude.
        d_lng = cos(angle) * (proximity / (111 * cos(radians(lat))))  # Change in longitude.
        
        # Calculate the new latitude and longitude for this route.
        new_lat = lat + d_lat
        new_lng = lng + d_lng
        
        # Append the generated route information to the list of routes.
        routes.append({
            'name': f'Route {i+1}',  # Name each route with a unique identifier.
            'description': 'Generated route',  # Add a generic description for the generated routes.
            'latitude': new_lat,  # The latitude of the route's starting point.
            'longitude': new_lng,  # The longitude of the route's starting point.
            'distance': actual_distance  # The distance of the route (with variation applied).
        })
    
    # Return the list of generated routes.
    return routes

# This function stores the generated routes in the MySQL database.
# It inserts each route into the 'Routes' table with its name, description, latitude, longitude, and distance.
def store_routes(routes):
    # Get a cursor to execute SQL queries.
    cursor = mysql.connection.cursor()
    
    # Loop through each route and insert it into the database.
    for route in routes:
        cursor.execute(
            "INSERT INTO Routes (name, description, latitude, longitude, distance) VALUES (%s, %s, %s, %s, %s)",
            (route['name'], route['description'], route['latitude'], route['longitude'], route['distance'])
        )
    
    # Commit the transaction to save the changes in the database.
    mysql.connection.commit()
    
    # Close the cursor after the routes are inserted.
    cursor.close()