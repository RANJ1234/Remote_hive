"""
Setup and run script for Remote Hive application

This script:
1. Installs required dependencies
2. Seeds the database with initial data
3. Runs the application
"""

import os
import sys
import subprocess
import time

def run_command(command):
    """Run a shell command and print output"""
    print(f"Running: {command}")
    process = subprocess.Popen(
        command, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        universal_newlines=True
    )
    
    for line in process.stdout:
        print(line.strip())
    
    process.wait()
    return process.returncode

def install_dependencies():
    """Install required Python dependencies"""
    print("\n=== Installing dependencies ===")
    
    # Install MongoDB dependencies
    run_command("pip install pymongo==3.12.0 mongoengine==0.24.0 dnspython==2.3.0")
    
    # Install Flask and other dependencies
    run_command("pip install flask==3.1.0 flask-login==0.6.3 flask-wtf==1.2.2 werkzeug==3.1.3 wtforms==3.2.1")
    
    # Install other required packages
    run_command("pip install email-validator==2.2.0 gunicorn==23.0.0")
    
    print("Dependencies installed successfully!")

def check_mongodb():
    """Check if MongoDB is running"""
    print("\n=== Checking MongoDB ===")
    
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()  # Will raise an exception if MongoDB is not running
        print("MongoDB is running!")
        return True
    except Exception as e:
        print(f"MongoDB is not running: {e}")
        print("\nPlease make sure MongoDB is installed and running.")
        print("You can download MongoDB from: https://www.mongodb.com/try/download/community")
        print("Or use MongoDB Atlas: https://www.mongodb.com/cloud/atlas")
        return False

def seed_database():
    """Seed the database with initial data"""
    print("\n=== Seeding database ===")
    run_command("python seed_database.py")

def run_application():
    """Run the Flask application"""
    print("\n=== Starting application ===")
    run_command("python main.py")

if __name__ == "__main__":
    print("=== Remote Hive Setup and Run Script ===")
    
    # Install dependencies
    install_dependencies()
    
    # Check if MongoDB is running
    if not check_mongodb():
        print("\nPlease start MongoDB and run this script again.")
        sys.exit(1)
    
    # Seed database
    seed_database()
    
    # Run application
    run_application()
