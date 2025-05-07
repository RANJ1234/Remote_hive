import os
from datetime import timedelta

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-replace-in-production')
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    DEBUG = False
    TESTING = False
    # MongoDB Atlas connection
    # This will be updated with the new connection string
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://ranjeettiwary589:BvNj0KznHubQSCrM@cluster0.qrrpagr.mongodb.net/remotehive?retryWrites=true&w=majority')

    # Database name - will be used if not specified in the connection string
    MONGODB_DB = os.environ.get('MONGODB_DB', 'remotehive')

    # Local MongoDB connection (fallback)
    MONGODB_LOCAL_URI = 'mongodb+srv://ranjeettiwary589:BvNj0KznHubQSCrM@cluster0.qrrpagr.mongodb.net/remotehive?retryWrites=true&w=majority'

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@remotehive.com')

    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Rate limiting
    RATELIMIT_DEFAULT = ["200 per day", "50 per hour", "10 per minute"]
    RATELIMIT_STORAGE_URL = "memory://"

    # Security headers
    SECURITY_HEADERS = {
        'Content-Security-Policy': "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net https://accounts.google.com; style-src 'self' https://cdn.jsdelivr.net; img-src 'self' data:; font-src 'self' https://cdn.jsdelivr.net; connect-src 'self' https://accounts.google.com https://oauth2.googleapis.com;",
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }

    # Google Sheets API configuration
    GOOGLE_SHEETS_CLIENT_ID = os.environ.get('GOOGLE_SHEETS_CLIENT_ID', '')
    GOOGLE_SHEETS_CLIENT_SECRET = os.environ.get('GOOGLE_SHEETS_CLIENT_SECRET', '')
    GOOGLE_SHEETS_REDIRECT_URI = os.environ.get('GOOGLE_SHEETS_REDIRECT_URI', 'http://localhost:5000/')
    GOOGLE_SHEETS_SPREADSHEET_ID = os.environ.get('GOOGLE_SHEETS_SPREADSHEET_ID', '1MD3t0g8GZQ8G-7sLut68br9feU7vbjQQ1ytVO4ahkxc')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    MONGODB_URI = 'mongodb+srv://ranjeettiwary589:BvNj0KznHubQSCrM@cluster0.qrrpagr.mongodb.net/remotehive_test?retryWrites=true&w=majority'

class ProductionConfig(Config):
    """Production configuration."""
    # Production-specific settings
    # Ensure all secrets are loaded from environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-replace-in-production')

    # Use a more robust rate limit storage in production
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')

# Select configuration based on environment
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Return the appropriate configuration object based on the environment."""
    env = os.environ.get('FLASK_ENV', 'development')  # Changed default to 'development'
    return config.get(env, config['development'])
