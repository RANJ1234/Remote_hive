import os
import sys
import logging

# Set environment to production
os.environ['FLASK_ENV'] = 'production'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Import the Flask application
from app import app as application

# Start MongoDB connection monitor
from app import mongodb_connection_monitor
import threading
monitor_thread = threading.Thread(target=mongodb_connection_monitor, daemon=True)
monitor_thread.start()
logging.info("Started MongoDB connection monitor thread in WSGI")

# This file is used by production WSGI servers (Gunicorn, uWSGI, etc.)
if __name__ == "__main__":
    # This should only be used for testing the WSGI file
    application.run(host="0.0.0.0", port=5000)
