from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
mongo_uri = os.environ.get('MONGODB_URI', 'mongodb+srv://ranjeettiwary589:BvNj0KznHubQSCrM@cluster0.qrrpagr.mongodb.net/remotehive?retryWrites=true&w=majority')
client = MongoClient(mongo_uri)
db = client.remotehive
users_collection = db.users

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator - MODIFIED to allow all users to access admin features
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        # Allow access regardless of user role
        return f(*args, **kwargs)
    return decorated_function

# Routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate input
        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('auth/login.html')

        # Check if user exists
        user = users_collection.find_one({'email': email})

        # Check password
        if user:
            # Special case for admin login
            if email == 'admin@remotehive.in' and password == 'Ranjeet@1998':
                # Store user in session
                session['user_id'] = str(user['_id'])
                session['user_role'] = 'admin'
                flash('Login successful!', 'success')
                return redirect(url_for('admin.index'))

            # Regular user login
            if 'password' in user and check_password_hash(user['password'], password):
                # Store user in session
                session['user_id'] = str(user['_id'])
                session['user_role'] = user['role']

                flash('Login successful!', 'success')

                # Redirect based on role - but all users can access all features
                if user['role'] == 'admin':
                    return redirect(url_for('admin.index'))
                elif user['role'] == 'employer':
                    return redirect(url_for('employer.dashboard'))
                else:
                    return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate input
        if not username or not email or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        # Check if user already exists
        existing_user = users_collection.find_one({'$or': [{'username': username}, {'email': email}]})
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return render_template('auth/register.html')

        # Create new user
        hashed_password = generate_password_hash(password)
        role = request.form.get('role', 'candidate')  # Get role from form or default to candidate
        new_user = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'role': role,  # Use the role from the form
            'created_at': pymongo.datetime.datetime.utcnow()
        }

        # Insert user into database
        result = users_collection.insert_one(new_user)

        if result.inserted_id:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration failed. Please try again.', 'danger')

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Admin login route
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('username')  # Using username field from the form
        password = request.form.get('password')

        # Check if it's the admin
        if email == 'admin@remotehive.in' and password == 'Ranjeet@1998':
            # Create admin user if it doesn't exist
            admin_user = users_collection.find_one({'email': email})

            if not admin_user:
                admin_user = {
                    'username': 'admin',
                    'email': 'admin@remotehive.in',
                    'password': generate_password_hash('Ranjeet@1998'),
                    'role': 'admin',
                    'created_at': pymongo.datetime.datetime.utcnow()
                }
                users_collection.insert_one(admin_user)
                admin_user = users_collection.find_one({'email': email})

            # Store admin in session
            session['user_id'] = str(admin_user['_id'])
            session['user_role'] = 'admin'

            flash('Admin login successful!', 'success')
            return redirect(url_for('admin.index'))
        else:
            flash('Invalid admin credentials.', 'danger')

    return render_template('admin/login.html')
