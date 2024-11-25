import os  # Ensure 'os' is imported at the top.
import requests  # Assuming other imports are correct.
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# Constants
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
OSM_ENDPOINT = "https://overpass-api.de/api/interpreter"

def fetch_route_data(location, proximity_km=10):
    """
    Fetch route data from OSM and extract relevant features.
    """
    query = f"""
    [out:json];
    (
      way["highway"](around:{proximity_km * 1000}, {location['lat']}, {location['lng']});
    );
    out body;
    """
    response = requests.post(OSM_ENDPOINT, data={'data': query})
    data = response.json()

    routes = []
    for element in data['elements']:
        if 'tags' in element:
            routes.append({
                'name': element['tags'].get('name', 'Unnamed'),
                'distance': float(element['tags'].get('distance', np.random.uniform(1, 10))),
                'surface': element['tags'].get('surface', 'unknown'),
                'highway': element['tags'].get('highway', 'road'),
                'elevation': np.random.uniform(10, 100),  # Placeholder for elevation data
            })

    return pd.DataFrame(routes)

def preprocess_data(routes_df):
    """
    Preprocess route data: scale numerical features and encode categorical features.
    """
    # One-hot encode surface and highway types
    enc = OneHotEncoder()
    encoded_features = enc.fit_transform(routes_df[['surface', 'highway']]).toarray()

    # Standardize numerical features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(routes_df[['distance', 'elevation']])

    # Combine all features into a single array
    X = np.hstack((scaled_features, encoded_features))

    return X, scaler, enc
