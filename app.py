import os
import logging
import logging.handlers
import threading
import time
from datetime import datetime
from flask import Flask, request, g, render_template, jsonify, session
from werkzeug.middleware.proxy_fix import ProxyFix
from mongoengine import connect, disconnect_all
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from flask_talisman import Talisman
from config import get_config

# Configure logging
def setup_logging(app):
    log_level = getattr(logging, app.config['LOG_LEVEL'])
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    # File handler for errors
    if not os.path.exists('logs'):
        os.makedirs('logs')
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/remotehive.log', maxBytes=10485760, backupCount=10
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.ERROR)

    # Set root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Set werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(log_level)

# Initialize Flask extensions
compress = Compress()

# Global connection status
mongodb_connected = False
connection_lock = threading.Lock()

def create_app(config_name=None):
    # Create Flask app with explicit template folder
    app = Flask(__name__, template_folder='templates')

    # Load configuration
    config_obj = get_config()
    app.config.from_object(config_obj)

    # Set up logging
    setup_logging(app)

    # Set up security middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize Talisman for security headers (but disable content security policy for now)
    csp = app.config.get('SECURITY_HEADERS', {}).get('Content-Security-Policy', None)
    Talisman(app,
             content_security_policy=csp,
             content_security_policy_nonce_in=['script-src'],
             force_https=app.config.get('SESSION_COOKIE_SECURE', True),
             strict_transport_security=True,
             strict_transport_security_preload=True,
             session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE', True),
             session_cookie_http_only=app.config.get('SESSION_COOKIE_HTTPONLY', True))

    # Initialize Compress for response compression
    compress.init_app(app)

    # Initialize rate limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL', "memory://")
    )

    # Request timing middleware
    @app.before_request
    def before_request():
        g.start_time = datetime.now()
        # Check MongoDB connection before each request
        check_mongodb_connection()

    @app.after_request
    def after_request(response):
        # Add security headers
        for header, value in app.config.get('SECURITY_HEADERS', {}).items():
            if header != 'Content-Security-Policy':  # Already handled by Talisman
                response.headers[header] = value

        # Log request timing for slow requests
        if hasattr(g, 'start_time'):
            elapsed = (datetime.now() - g.start_time).total_seconds()
            if elapsed > 1.0:  # Log requests taking more than 1 second
                logging.warning(f"Slow request: {request.path} took {elapsed:.2f}s")

        return response

    return app

# Create the Flask app
app = create_app()

# Add Jinja2 filters
@app.template_filter('format_date')
def format_date(value, format='%Y-%m-%d'):
    """Format a date."""
    if value is None:
        return ""
    return value.strftime(format)

# MongoDB connection function with improved reliability
def connect_to_mongodb():
    global mongodb_connected

    with connection_lock:
        try:
            # Disconnect any existing connections first
            disconnect_all()
            logging.info("Disconnected any existing MongoDB connections")

            # Connect with MongoDB Atlas connection string
            connect(
                db="remotehive",
                host=app.config.get('MONGODB_URI', 'mongodb+srv://ranjeettiwary589:BvNj0KznHubQSCrM@cluster0.qrrpagr.mongodb.net/remotehive?retryWrites=true&w=majority'),
                alias="default",  # Use default alias
                connect=True,     # Force connection at startup
                maxPoolSize=5,    # Reduced pool size for better stability
                serverSelectionTimeoutMS=3000,
                socketTimeoutMS=5000,
                connectTimeoutMS=3000,
                heartbeatFrequencyMS=10000,  # More frequent heartbeats
                retryWrites=True,
                retryReads=True
            )

            # Test the connection with a simple command
            from mongoengine.connection import get_connection
            conn = get_connection()
            conn.admin.command('ping')

            logging.info("Connected to MongoDB Atlas successfully")
            mongodb_connected = True
            return True
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB Atlas: {e}")
            try:
                # Try connecting to local MongoDB as fallback
                disconnect_all()
                # Use MongoDB Atlas connection string as fallback
                connect(
                    db="remotehive",
                    host=app.config.get('MONGODB_URI', 'mongodb+srv://ranjeettiwary589:BvNj0KznHubQSCrM@cluster0.qrrpagr.mongodb.net/remotehive?retryWrites=true&w=majority'),
                    alias="default",
                    connect=True,
                    serverSelectionTimeoutMS=3000,
                    socketTimeoutMS=5000,
                    connectTimeoutMS=3000,
                    retryWrites=True,
                    retryReads=True
                )
                logging.info("Connected to local MongoDB successfully")
                mongodb_connected = True
                return True
            except Exception as local_e:
                logging.error(f"Failed to connect to local MongoDB: {local_e}")
                mongodb_connected = False
                return False

# Function to check MongoDB connection and reconnect if needed
def check_mongodb_connection():
    global mongodb_connected

    try:
        # Only check if we think we're connected
        if mongodb_connected:
            # Try a simple operation to verify connection
            from mongoengine.connection import get_connection
            conn = get_connection()
            conn.admin.command('ping')
            return True
    except Exception as e:
        logging.error(f"MongoDB connection check failed: {e}")
        # Connection is lost, try to reconnect
        with connection_lock:
            mongodb_connected = False
            return connect_to_mongodb()

    # If we're not connected, try to connect
    if not mongodb_connected:
        return connect_to_mongodb()

    return mongodb_connected

# Create a compatibility layer for MongoDB
class DB:
    def __init__(self):
        self.session = DBSession()

# MongoDB session compatibility layer
class DBSession:
    def add(self, obj):
        # In MongoDB, we just call save() on the object
        if hasattr(obj, 'save'):
            obj.save()

    def commit(self):
        # MongoDB saves are immediate, no commit needed
        pass

    def flush(self):
        # No equivalent in MongoDB
        pass

    def rollback(self):
        # No direct equivalent in MongoDB
        pass

# Create the db object that's imported in other modules
db = DB()

# Connect to MongoDB
mongodb_connected = connect_to_mongodb()

# Import models after initializing MongoDB connection
if mongodb_connected:
    try:
        import models
        # Import and create MongoDB indexes
        from services.mongodb_helpers import create_indexes
        create_indexes(models)
    except Exception as e:
        logging.error(f"Error importing models: {e}")
        import mock_models as models
        logging.warning("Using mock models due to model import error")
else:
    # Use mock models if MongoDB is not available
    import mock_models as models
    logging.warning("Using mock models due to MongoDB connection failure")

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Test route to verify server is working
@app.route('/test-server')
def test_server():
    logging.info("Test server route accessed")
    return render_template('server_test.html',
                          mongodb_connected=mongodb_connected,
                          server_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# MongoDB status check route
@app.route('/api/mongo-status')
def mongo_status():
    try:
        if not mongodb_connected:
            return jsonify({
                'status': 'disconnected',
                'message': 'MongoDB is not connected'
            }), 500

        # Check connection with a simple operation
        from mongoengine.connection import get_connection
        conn = get_connection()
        conn.admin.command('ping')

        # Count documents in a collection to verify connection
        doc_count = models.User.objects.count() if hasattr(models, 'User') else 0

        return jsonify({
            'status': 'connected',
            'message': 'MongoDB connection is active',
            'document_count': doc_count
        })
    except Exception as e:
        logging.error(f"MongoDB status check failed: {e}")

        # Try to reconnect
        reconnect_success = connect_to_mongodb()

        if reconnect_success:
            return jsonify({
                'status': 'reconnected',
                'message': 'MongoDB connection was restored'
            })
        else:
            return jsonify({
                'status': 'disconnected',
                'message': f'MongoDB connection failed: {str(e)}'
            }), 500

# Register blueprints
def register_blueprints(app):
    # Import routes after app is created to avoid circular imports
    with app.app_context():
        try:
            # Import admin blueprint and register it first
            from admin_clean import admin_bp
            app.register_blueprint(admin_bp)
            logging.info("Registered admin blueprint")

            # Import routes module - this will register all routes directly with the app
            # since routes.py uses @app.route decorators
            import routes

            # Create a simple index route
            @app.route('/')
            def index():
                # Render the index template directly
                from flask import render_template
                from models import Company, Job, CompanyCategory

                featured_companies = Company.objects(is_featured=True).limit(12)
                recent_jobs = Job.objects(is_active=True).order_by('-posted_date').limit(10)
                company_categories = CompanyCategory.objects.all()

                from forms import SearchForm
                search_form = SearchForm()

                return render_template('index.html',
                                    featured_companies=featured_companies,
                                    recent_jobs=recent_jobs,
                                    company_categories=company_categories,
                                    search_form=search_form)

            # Define the utility_processor function directly
            @app.context_processor
            def utility_processor():
                from datetime import datetime, timezone

                def format_date(date):
                    if not date:
                        return ""
                    return date.strftime("%B %d, %Y")

                def time_since(date):
                    if not date:
                        return ""

                    now = datetime.now(timezone.utc)
                    if not date.tzinfo:
                        # If date is not timezone-aware, assume it's UTC
                        date = date.replace(tzinfo=timezone.utc)

                    diff = now - date

                    days = diff.days
                    if days == 0:
                        hours = diff.seconds // 3600
                        if hours == 0:
                            minutes = diff.seconds // 60
                            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                        return f"{hours} hour{'s' if hours != 1 else ''} ago"
                    elif days < 7:
                        return f"{days} day{'s' if days != 1 else ''} ago"
                    elif days < 30:
                        weeks = days // 7
                        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
                    elif days < 365:
                        months = days // 30
                        return f"{months} month{'s' if months != 1 else ''} ago"
                    else:
                        years = days // 365
                        return f"{years} year{'s' if years != 1 else ''} ago"

                return dict(format_date=format_date, time_since=time_since)

            logging.info("Imported and registered main routes")

            # Import and register employer blueprint
            from employer_routes import employer_bp
            app.register_blueprint(employer_bp)
            logging.info("Registered employer blueprint")

            # Import and register jobseeker blueprint
            from jobseeker_routes import jobseeker_bp
            app.register_blueprint(jobseeker_bp)
            logging.info("Registered jobseeker blueprint")

            # Import admin redirects after registering the blueprint
            import admin_redirects
            logging.info("Imported admin redirects")

            # Import and register scraper API blueprint
            try:
                # Import the scraper_api blueprint directly from the routes directory
                from routes.scraper_api import scraper_api
                app.register_blueprint(scraper_api)
                logging.info("Registered scraper API blueprint")
            except ImportError as e:
                logging.error(f"Error importing scraper API blueprint: {e}")
                logging.info("Attempting fallback import for scraper_api...")

                # Try direct import as fallback
                try:
                    # Make sure Python can find the routes directory
                    import sys
                    import os
                    routes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'routes')
                    if routes_dir not in sys.path:
                        sys.path.append(routes_dir)

                    # Now try to import again
                    from scraper_api import scraper_api
                    app.register_blueprint(scraper_api)
                    logging.info("Registered scraper API blueprint (fallback)")
                except ImportError as e2:
                    logging.error(f"Error importing scraper API blueprint (fallback): {e2}")

            # Import and register admin scraper blueprint
            try:
                from routes.admin_scraper import admin_scraper
                app.register_blueprint(admin_scraper)
                logging.info("Registered admin scraper blueprint")
            except ImportError as e:
                logging.error(f"Error importing admin scraper blueprint: {e}")
                logging.info("Attempting fallback import for admin_scraper...")

                # Try direct import as fallback
                try:
                    # Make sure Python can find the routes directory
                    import sys
                    import os
                    routes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'routes')
                    if routes_dir not in sys.path:
                        sys.path.append(routes_dir)

                    # Now try to import again
                    from admin_scraper import admin_scraper
                    app.register_blueprint(admin_scraper)
                    logging.info("Registered admin scraper blueprint (fallback)")
                except ImportError as e2:
                    logging.error(f"Error importing admin scraper blueprint (fallback): {e2}")

            # Import and register job scraper route
            try:
                from job_scraper_routes import job_scraper_bp
                app.register_blueprint(job_scraper_bp)
                logging.info("Registered job scraper blueprint")
            except ImportError as e:
                logging.error(f"Error importing job scraper blueprint: {e}")

            # Import and register Google Sheets routes
            try:
                from sheets_routes import sheets_bp
                app.register_blueprint(sheets_bp)
                logging.info("Registered Google Sheets blueprint")
            except ImportError as e:
                logging.error(f"Error importing Google Sheets blueprint: {e}")
        except Exception as e:
            logging.error(f"Error registering blueprints: {e}")

# Initialize services
def initialize_services(app):
    """Initialize application services"""
    try:
        # Initialize Google Analytics service
        from services.google_analytics import google_analytics
        google_analytics.init_app(app)
        logging.info("Initialized Google Analytics service")

        # Initialize Google Sheets service
        try:
            # Set the spreadsheet ID from config if available
            from google_sheets_service import JobSheetManager
            if app.config.get('GOOGLE_SHEETS_SPREADSHEET_ID'):
                import google_sheets_service
                google_sheets_service.SPREADSHEET_ID = app.config.get('GOOGLE_SHEETS_SPREADSHEET_ID')
                logging.info(f"Set Google Sheets spreadsheet ID: {google_sheets_service.SPREADSHEET_ID}")
        except Exception as sheets_e:
            logging.error(f"Error initializing Google Sheets service: {sheets_e}")
    except Exception as e:
        logging.error(f"Error initializing services: {e}")

# Register blueprints
register_blueprints(app)

# Initialize services
initialize_services(app)

# MongoDB connection monitor thread
def mongodb_connection_monitor():
    """Background thread to monitor MongoDB connection and reconnect if needed"""
    # Initial delay to allow the application to start properly
    time.sleep(5)

    while True:
        try:
            # Check the connection and reconnect if needed
            connection_ok = check_mongodb_connection()

            if connection_ok:
                logging.info("MongoDB connection monitor: Connection is healthy")
            else:
                logging.warning("MongoDB connection monitor: Connection issue detected, attempting to reconnect")
                connect_to_mongodb()

            # Sleep before next check (15 seconds)
            time.sleep(15)
        except Exception as e:
            # Catch any exceptions to prevent the monitor thread from dying
            logging.error(f"Unexpected error in MongoDB connection monitor: {e}")
            # Sleep a bit before retrying
            time.sleep(5)

logging.info("Application initialized")

# Start MongoDB connection monitor in background thread
monitor_thread = threading.Thread(target=mongodb_connection_monitor, daemon=True)
monitor_thread.start()
logging.info("Started MongoDB connection monitor thread")

# Run the app if this file is executed directly (development only)
if __name__ == "__main__":
    # This should only be used for development
    # For production, use a WSGI server like Gunicorn or uWSGI with the wsgi.py file
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
