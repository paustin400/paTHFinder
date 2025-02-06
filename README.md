# PathFinder

PathFinder is a web-based application that provides AI-driven route recommendations for runners, hikers, and walkers. The application integrates a Flask backend with a MySQL database, a responsive Google Maps interface, and machine learning components for enhanced route analytics.

## Features

### AI-Driven Recommendations
- Uses an Artificial Neural Network (MLP Regressor) along with a combined RandomForest and GradientBoosting model to provide route quality scores and additional insights.

### Interactive Map Interface
- Integrates the Google Maps API to display routes and geolocate users.
- The map interface features:
  - A draggable, resizable info window (sidebar) with search filters.
  - A full-screen map view that adjusts seamlessly to the browser window.

### User-Friendly Search
- Search for routes based on:
  - Starting location (via geolocation or manual input)
  - Proximity, route type, and elevation preferences
  - Optional filters like sidewalks/pedestrian paths

### Responsive Design
- The UI is built with Bootstrap and custom CSS, ensuring compatibility across devices (desktop-focused).

## Project Directory Structure

```
paTHFinder_code/
├── app/
│   ├── ml/
│   │   ├── ai_model.py           # Integration of RandomForest and GradientBoosting models
│   │   ├── ann_model.py          # ANN (MLP Regressor) model
│   │   ├── config.py             # Configuration for ML models
│   │   └── model_coordinator.py  # Coordinates predictions from multiple models
│   ├── routes/
│   │   ├── api.py                # API endpoints for external integration
│   │   └── main.py               # Main routing and page rendering
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css         # Custom CSS styling for the app (includes sidebar, map, etc.)
│   │   └── js/
│   │       ├── app.js            # Main JavaScript functionality (map initialization, sidebar behavior, etc.)
│   │       └── search.js         # Search page–specific JavaScript (e.g. autocomplete)
│   ├── templates/
│   │   ├── base.html             # Base template (includes common HTML structure, external CSS/JS links)
│   │   ├── home.html             # Homepage template
│   │   ├── map_base.html         # Base template for pages with the map
│   │   ├── preferences.html      # User preferences page
│   │   ├── route_detail.html     # Detailed view for a specific route
│   │   ├── search.html           # Search page (with the draggable, resizable sidebar)
│   │   └── search_results.html   # Displays search results
│   ├── __init__.py               # Flask application initialization
│   ├── config.py                 # Application configuration
│   └── models.py                 # Database models (User, Route, Preference, Feedback, etc.)
├── migrations/                   # Database migration files (Flask-Migrate)
├── tests/                        # Test suite for the project
├── run.py                        # Script to start the Flask app
├── requirements.txt              # Python dependencies list
└── ...                           # Other project files (logs, sample data, etc.)
```

## Installation

### Clone the Repository
```bash
git clone https://github.com/yourusername/new-pathfinder.git
cd new-pathfinder
```

### Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure Environment Variables
Create a `.env` file with the following (update with your actual API key and database settings):
```ini
GOOGLE_MAPS_API_KEY=your_api_key_here
DATABASE_URI=mysql://username:password@localhost/pathfinder_db
```

### Run the Application
```bash
flask run
```

## Usage
1. Visit the homepage to choose your preferred option.
2. Click on "Search for Routes" to access the interactive map.
3. Use the draggable and resizable sidebar to filter search criteria.
4. Enjoy AI-driven recommendations as you explore the best routes for your activities.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contributions
Contributions are welcome! Feel free to submit a pull request or open an issue if you have suggestions.

## Contact
For any questions or feedback, please reach out via GitHub Issues or email at `your-email@example.com`. 

---

Happy Running! 🏃‍♂️🚶‍♀️
