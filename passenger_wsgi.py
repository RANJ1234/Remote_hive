import os
import sys
import logging

# Configure logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'passenger_wsgi.log'),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Add the application directory to the Python path
    INTERP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'bin', 'python')
    if sys.executable != INTERP:
        logger.info(f"Setting Python interpreter to: {INTERP}")
        os.execl(INTERP, INTERP, *sys.argv)

    # Add the current directory to the Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Adding directory to path: {current_dir}")
    sys.path.insert(0, current_dir)

    # Set environment variables
    os.environ['FLASK_ENV'] = 'production'
    
    # Import the WSGI application
    logger.info("Importing application from wsgi.py")
    from wsgi import application
    
    logger.info("Application imported successfully")
    
except Exception as e:
    logger.error(f"Error in passenger_wsgi.py: {str(e)}", exc_info=True)
    
    # Create a simple error application
    def application(environ, start_response):
        status = '500 Internal Server Error'
        output = b'An error occurred while loading the application.'
        response_headers = [('Content-type', 'text/plain'),
                           ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]
