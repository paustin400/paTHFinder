
# Pathfinder

Pathfinder is a web application designed to provide runners with customized routes based on their location and preferences. The project aims to eventually integrate AI capabilities for personalized route recommendations.

---

## Table of Contents

1. [Overview](#overview)
2. [Setup Instructions](#setup-instructions)
3. [Running the Application](#running-the-application)
4. [Directory Structure](#directory-structure)
5. [Broad Focus and Next Steps](#broad-focus-and-next-steps)
6. [Future Goals](#future-goals)

---

## Overview

Pathfinder allows users to:
- Search for running routes based on location.
- Save preferences for a personalized experience.
- Explore route details through an interactive UI.

This project is currently in development, with the primary focus on building a stable, functional web app.

---

## Setup Instructions

To run Pathfinder locally, follow these steps:

### 1. Clone the Repository
```bash
git clone <repository-url>
cd pathfinder_code
```

### 2. Create a Virtual Environment
Create a Python virtual environment to manage dependencies:
```bash
python -m venv venv
```

Activate the environment:
- On Windows:
  ```bash
  venv\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies
Install all required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Initialize the Database
Run the SQL scripts in the `database` folder to set up your database schema and populate any necessary initial data.

```bash
# Example for running SQL scripts
sqlite3 pathfinder.db < database/sql_script.sql
```

### 5. Start the Application
Run the app using the `run.py` file:
```bash
python run.py
```

By default, the app runs at `http://127.0.0.1:5000`.

---

## Running the Application

1. After starting the application, open a web browser and navigate to `http://127.0.0.1:5000`.
2. Explore the following features:
   - Home page
   - Search for routes
   - Save preferences

---

## Directory Structure

Below is an overview of the project directory:

```
pathfinder_code/
│
├── app/
│   ├── static/          # Static assets (CSS, JavaScript)
│   ├── templates/       # HTML templates
│   ├── __init__.py      # App initialization
│   ├── ai_model.py      # Placeholder for AI-related logic
│   ├── ann_model.py     # Placeholder for additional AI models
│   ├── models.py        # Database models
│   ├── routes.py        # Flask routes
│   ├── utils.py         # Helper functions
│
├── database/            # SQL scripts
│   ├── sql_data_fetch.sql
│   ├── sql_script.sql
│
├── venv/                # Virtual environment (not tracked in Git)
├── .env                 # Environment variables (not tracked in Git)
├── requirements.txt     # Python dependencies
├── run.py               # Entry point
├── .gitignore           # Git ignored files
├── README.md            # Project documentation
```

---

## Broad Focus and Next Steps

**Last Updated:** [Insert Date]

### Current Broad Focus
- Refactoring `routes.py` to improve code readability and modularity.
- Improving database queries for faster route search results.
- Testing user preference saving logic.

### Next Steps
- Explore integration of AI for personalized route recommendations.
- Optimize the HTML templates in the `templates` folder for better user experience.
- Add unit tests to validate critical components.

---

## Future Goals

- **AI Integration**: Leverage machine learning to recommend running routes based on user preferences and historical data.
- **Mobile Responsiveness**: Improve UI for better usability on mobile devices.
- **Cloud Deployment**: Deploy Pathfinder on a cloud platform (e.g., Heroku, AWS).
- **User Authentication**: Add secure login and user management features.

---
