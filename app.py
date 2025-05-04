import os
import logging
import logging.handlers
from flask import Flask, request, g
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from mongoengine import connect
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
login_manager = LoginManager()
compress = Compress()

def create_app(config_name=None):
    # Create Flask app
    app = Flask(__name__)

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
        default_limits=app.config.get('RATELIMIT_DEFAULT', "200 per day;50 per hour"),
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL', "memory://")
    )

    # Request timing middleware
    @app.before_request
    def before_request():
        g.start_time = request.environ.get('REQUEST_TIME', 0)

    @app.after_request
    def after_request(response):
        # Add security headers
        for header, value in app.config.get('SECURITY_HEADERS', {}).items():
            if header != 'Content-Security-Policy':  # Already handled by Talisman
                response.headers[header] = value

        # Log request timing for slow requests
        if hasattr(g, 'start_time'):
            elapsed = request.environ.get('REQUEST_TIME', 0) - g.start_time
            if elapsed > 1.0:  # Log requests taking more than 1 second
                logging.warning(f"Slow request: {request.path} took {elapsed:.2f}s")

        return response

    return app

# Create the Flask app
app = create_app()

# Register blueprints
def register_blueprints(app):
    # Import blueprints
    from admin import admin_bp

    # Register blueprints
    app.register_blueprint(admin_bp)

    # Import routes after app is created to avoid circular imports
    with app.app_context():
        import routes
        import employer_routes
        import jobseeker_routes
        import admin_redirects

# Initialize extensions with the app
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Connect to MongoDB with MongoEngine
def init_db(app):
    try:
        connect(host=app.config["MONGODB_URI"])
        logging.info("Connected to MongoDB successfully")
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        # Create a fallback connection to a local MongoDB instance
        try:
            connect(db="remotehive", host="localhost", port=27017)
            logging.info("Connected to local MongoDB successfully")
        except Exception as e:
            logging.error(f"Failed to connect to local MongoDB: {e}")
            raise

# Create a compatibility layer for SQLAlchemy to MongoDB migration
# This is a temporary solution to make the existing code work with MongoDB
class DBSession:
    def add(self, obj):
        # In MongoDB, we just call save() on the object
        if hasattr(obj, 'save'):
            obj.save()
        pass

    def commit(self):
        # MongoDB saves are immediate, no commit needed
        pass

    def flush(self):
        # No equivalent in MongoDB
        pass

    def rollback(self):
        # No direct equivalent in MongoDB
        pass

# Create a db object with a session attribute for compatibility
class DB:
    def __init__(self):
        self.session = DBSession()

# Create the db object that's imported in other modules
db = DB()

# Initialize the database
init_db(app)

# Import models after initializing MongoDB connection
import models

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        from models import User
        from bson import ObjectId

        # Check if user_id is a valid ObjectId
        if ObjectId.is_valid(user_id):
            return User.objects(id=user_id).first()
        else:
            logging.error(f"Invalid user_id format: {user_id}")
            return None
    except Exception as e:
        logging.error(f"Error loading user: {e}")
        return None

# Register blueprints
register_blueprints(app)

logging.info("Application initialized")
