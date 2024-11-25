# models.py: Defines functions that interact with the MySQL database.
# Handles operations like searching for routes, saving preferences, and submitting feedback.
# Imports are placed inside functions to avoid circular imports.

from flask import current_app  # Access the current app instance for logging.
from . import mysql  # This ensures `mysql` is properly referenced.

def get_db_connection():
    """
    Establishes a connection to the MySQL database.
    Returns a cursor that allows executing SQL queries.
    """
    from . import mysql  # Import inside the function to avoid circular import issues.
    return mysql.connection.cursor()  # Return a MySQL cursor for executing queries.

def search_routes(search_term, max_distance):
    """
    Searches for routes in the database based on a location and maximum distance.
    
    Parameters:
    - search_term: The location (or part of it) the user is searching for.
    - max_distance: The maximum distance (in km) the user is willing to travel.
    
    Returns:
    - All matching routes from the database.
    """
    with get_db_connection() as cur:
        query = "SELECT * FROM Routes WHERE location LIKE %s AND distance <= %s"
        cur.execute(query, ('%' + search_term + '%', max_distance))
        return cur.fetchall()  # Return all the results from the query.

def save_preferences(user_id, route_type):
    """
    Saves the user's preferred route type in the database.
    
    Parameters:
    - user_id: The ID of the user saving their preferences.
    - route_type: The type of route preferred by the user.
    """
    with get_db_connection() as cur:
        cur.execute(
            "INSERT INTO Preferences(user_id, route_type) VALUES(%s, %s)", 
            (user_id, route_type)
        )
        mysql.connection.commit()  # Commit the transaction to save preferences.

def submit_feedback(route_id, user_id, rating, comment):
    """
    Submits feedback for a specific route.
    
    Parameters:
    - route_id: The ID of the route being reviewed.
    - user_id: The ID of the user submitting feedback.
    - rating: The user's rating for the route (e.g., 1-5).
    - comment: Additional comments from the user.
    """
    with get_db_connection() as cur:
        cur.execute(
            "INSERT INTO Feedback(route_id, user_id, rating, comment) VALUES(%s, %s, %s, %s)", 
            (route_id, user_id, rating, comment)
        )
        mysql.connection.commit()  # Commit the transaction to save feedback.

def get_route_details(route_id):
    """
    Retrieves detailed information about a specific route from the database.

    Parameters:
    - route_id: The ID of the route for which details are fetched.

    Returns:
    - The details of the route, or None if not found.
    """
    with get_db_connection() as cur:
        cur.execute("SELECT * FROM Routes WHERE id = %s", (route_id,))
        return cur.fetchone()  # Return the first matching route, as IDs are unique.
