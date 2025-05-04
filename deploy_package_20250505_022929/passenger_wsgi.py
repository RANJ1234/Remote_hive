
import os
import sys

# Add the application directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the WSGI application
from wsgi import application
