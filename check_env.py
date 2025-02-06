import os
import sys
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

def check_environment():
    # Load environment variables
    env_path = Path('.') / '.env'
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    load_dotenv()
    
    # Required environment variables
    required_vars = {
        'FLASK_APP': 'Flask application entry point',
        'SECRET_KEY': 'Flask secret key',
        'GOOGLE_MAPS_API_KEY': 'Google Maps API key',
        'MYSQL_HOST': 'MySQL host',
        'MYSQL_USER': 'MySQL username',
        'MYSQL_PASSWORD': 'MySQL password',
        'MYSQL_DB': 'MySQL database name'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    # Check MySQL connection
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            port=int(os.getenv('MYSQL_PORT', 3306))
        )
        print("✅ MySQL connection successful")
        conn.close()
    except Exception as e:
        print(f"❌ MySQL connection failed: {str(e)}")
        return False
    
    # Check model directory
    model_dir = os.getenv('MODEL_DIR', 'models')
    if not os.path.exists(model_dir):
        print(f"❌ Model directory '{model_dir}' not found")
        os.makedirs(model_dir)
        print(f"✅ Created model directory '{model_dir}'")
    else:
        print(f"✅ Model directory '{model_dir}' exists")
    
    # Check static directory
    static_dir = Path('app/static')
    if not static_dir.exists():
        print("❌ Static directory not found")
        return False
    print("✅ Static directory exists")
    
    # All checks passed
    print("\n✅ Environment configuration is valid")
    return True

if __name__ == "__main__":
    if not check_environment():
        print("\n❌ Environment check failed! Please fix the issues above.")
        sys.exit(1)
    print("\n🚀 Ready to run the application!")