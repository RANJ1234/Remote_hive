import os
from flask import Blueprint, Flask

# Create Blueprint
admin_bp = Blueprint(
    'admin', 
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/admin'
)

# Import routes after creating the blueprint to avoid circular imports
from admin.routes import *

def create_admin_app():
    """Create a standalone admin app for development purposes"""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-replace-in-production")
    
    # Register the blueprint
    app.register_blueprint(admin_bp)
    
    return app
