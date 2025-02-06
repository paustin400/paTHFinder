import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

def inspect_databases():
    load_dotenv()
    
    # Get credentials from environment variables or use defaults
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', '')
    }
    
    try:
        # First connect without specifying a database
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # List all databases
        cursor.execute("SHOW DATABASES")
        print("\n=== Available Databases ===")
        databases = [db[0] for db in cursor.fetchall()]
        for db in databases:
            print(f"- {db}")
            
        # Ask which database to inspect
        db_name = input("\nEnter the database name to inspect (or press Enter to exit): ")
        if not db_name:
            return
            
        if db_name not in databases:
            print(f"Database '{db_name}' not found!")
            return
            
        # Connect to specific database
        config['database'] = db_name
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Show tables
        cursor.execute("SHOW TABLES")
        print(f"\n=== Tables in {db_name} ===")
        tables = [table[0] for table in cursor.fetchall()]
        for table in tables:
            print(f"\nTable: {table}")
            # Show table schema
            cursor.execute(f"DESCRIBE {table}")
            print("Columns:")
            for column in cursor.fetchall():
                print(f"  - {column[0]}: {column[1]}")
                
            # Show foreign keys
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM
                    INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE
                    TABLE_SCHEMA = '{db_name}'
                    AND TABLE_NAME = '{table}'
                    AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            foreign_keys = cursor.fetchall()
            if foreign_keys:
                print("Foreign Keys:")
                for fk in foreign_keys:
                    print(f"  - {fk[0]} -> {fk[1]}({fk[2]})")
                    
    except Error as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    inspect_databases()