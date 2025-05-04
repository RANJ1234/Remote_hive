import os
from app import app as application

# Set environment to production
os.environ['FLASK_ENV'] = 'production'

# This file is used by production WSGI servers (Gunicorn, uWSGI, etc.)
if __name__ == "__main__":
    application.run()
