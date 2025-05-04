import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Set development environment if not specified
if 'FLASK_ENV' not in os.environ:
    os.environ['FLASK_ENV'] = 'development'

# Import the app after environment variables are loaded
from app import app

if __name__ == '__main__':
    # Run the app with appropriate debug setting
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=debug_mode
    )
