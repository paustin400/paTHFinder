@echo off
REM Create main application directory structure
mkdir app
mkdir app\templates
mkdir app\static

REM Create empty Python files
type nul > run.py
type nul > app\__init__.py
type nul > app\routes.py
type nul > app\models.py
type nul > app\utils.py
type nul > app\ai_model.py
type nul > app\ann_model.py

REM Create empty template files
type nul > app\templates\home.html
type nul > app\templates\search.html
type nul > app\templates\search_results.html
type nul > app\templates\preferences.html
type nul > app\templates\route_detail.html

REM Create empty static files
type nul > app\static\app.js
type nul > app\static\style.css

echo Project structure created successfully!
