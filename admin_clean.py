"""
This file provides a clean implementation of the admin panel with properly configured routes.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, make_response, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from datetime import datetime
import json
from models import User, Job, Company, JobApplication, JobseekerProfile
from forms import LoginForm, AdminUserForm, JobPostForm, CompanyForm, AdminCompanyCategoryForm

# Create admin blueprint with correct template folder
admin_bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates/admin',
    static_folder='static',
    url_prefix='/admin'
)

# Add context processors for the admin blueprint
@admin_bp.context_processor
def utility_processor():
    def format_date(date):
        if not date:
            return ""
        return date.strftime("%B %d, %Y")

    def time_since(date):
        if not date:
            return ""

        from datetime import datetime, timezone
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

# Admin access decorator
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Admin Index - Redirects to dashboard
@admin_bp.route('/')
def index():
    # Check if user is already logged in and is admin
    if current_user.is_authenticated and current_user.is_admin():
        return redirect(url_for('admin.admin_dashboard'))
    else:
        return redirect(url_for('admin.admin_login'))

# Admin Login
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin():
        return redirect(url_for('admin.admin_dashboard'))

    form = LoginForm()
    error_message = None

    # Handle POST request
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'y'

        user = User.objects(email=email).first()
        if user and user.check_password(password) and user.is_admin():
            login_user(user, remember=remember_me)
            user.last_login = datetime.now()
            user.save()

            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.admin_dashboard'))
        else:
            error_message = 'Invalid email or password, or you do not have admin privileges'

    # Use the login.html template in the admin folder
    response = make_response(render_template('admin/login.html', form=form, error_message=error_message))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Admin Logout
@admin_bp.route('/admin_logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out from the admin panel', 'info')
    return redirect(url_for('admin.admin_login'))

# Admin Dashboard
@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    # Get basic statistics
    total_users = User.objects.count()
    total_jobs = Job.objects.count()
    total_companies = Company.objects.count()
    total_applications = JobApplication.objects.count()

    # Get recent users and jobs
    recent_users = User.objects.order_by('-created_at').limit(5)
    recent_jobs = Job.objects.order_by('-posted_date').limit(5)

    # Job statistics
    active_jobs = Job.objects(is_active=True).count()
    remote_jobs = Job.objects(is_remote=True).count()

    # Get companies with most jobs
    companies = Company.objects.all()
    company_job_counts = []
    for company in companies:
        job_count = Job.objects(company=company).count()
        if job_count > 0:
            company_job_counts.append((company, job_count))

    # Sort by job count and take top 5
    top_companies_by_jobs = sorted(company_job_counts, key=lambda x: x[1], reverse=True)[:5]

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_jobs=total_jobs,
                           total_companies=total_companies,
                           total_applications=total_applications,
                           recent_users=recent_users,
                           recent_jobs=recent_jobs,
                           active_jobs=active_jobs,
                           remote_jobs=remote_jobs,
                           top_companies_by_jobs=top_companies_by_jobs)

# Analytics Dashboard
@admin_bp.route('/analytics_dashboard')
@admin_required
def analytics_dashboard():
    # Monthly job postings data (last 12 months)
    current_month = datetime.now().month
    current_year = datetime.now().year

    monthly_jobs_data = []
    monthly_users_data = []
    month_labels = []

    for i in range(11, -1, -1):
        # Calculate month and year
        month = (current_month - i) % 12
        if month == 0:
            month = 12
        year = current_year - ((current_month - i) // 12)

        # Get start and end date for the month
        if month == 12:
            start_date = datetime(year, month, 1)
            end_date = datetime(year + 1, 1, 1)
        else:
            start_date = datetime(year, month, 1)
            end_date = datetime(year, month + 1, 1)

        # Count jobs and users created in this month
        jobs_count = Job.objects(posted_date__gte=start_date, posted_date__lt=end_date).count()
        users_count = User.objects(created_at__gte=start_date, created_at__lt=end_date).count()

        # Add to data arrays
        monthly_jobs_data.append(jobs_count)
        monthly_users_data.append(users_count)

        # Format month label
        month_name = start_date.strftime('%b')
        month_labels.append(f"{month_name} {year}")

    # Job type distribution
    job_types = {}
    for job in Job.objects.all():
        job_type = job.job_type
        if job_type in job_types:
            job_types[job_type] += 1
        else:
            job_types[job_type] = 1

    # User role distribution
    user_roles = {
        'admin': User.objects(role='admin').count(),
        'employer': User.objects(role='employer').count(),
        'jobseeker': User.objects(role='jobseeker').count()
    }

    # Application status distribution
    application_statuses = {}
    for app in JobApplication.objects.all():
        status = app.status
        if status in application_statuses:
            application_statuses[status] += 1
        else:
            application_statuses[status] = 1

    return render_template('admin/dashboard.html',
                          month_labels=month_labels,
                          monthly_jobs_data=monthly_jobs_data,
                          monthly_users_data=monthly_users_data,
                          job_types=job_types,
                          user_roles=user_roles,
                          application_statuses=application_statuses)

# MongoDB Pagination Helper Class
class MongoDBPagination:
    def __init__(self, items, page=1, per_page=10):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = len(items)
        self.pages = (self.total + self.per_page - 1) // self.per_page
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1 if self.has_prev else None
        self.next_num = page + 1 if self.has_next else None

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge or
                (self.page - left_current - 1 < num < self.page + right_current) or
                num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num

# Manage Users
@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.objects.all()

    # Get page from query parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Create a list of all users
    all_users = list(users)

    # Calculate start and end indices for the current page
    start = (page - 1) * per_page
    end = start + per_page

    # Create pagination object
    pagination = MongoDBPagination(all_users, page, per_page)

    # Set items to only the current page's items
    pagination.items = all_users[start:end]

    return render_template('admin/manage_users.html', users=pagination)

# Add User
@admin_bp.route('/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    form = AdminUserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            is_active=form.is_active.data
        )
        if form.password.data:
            user.set_password(form.password.data)
        else:
            user.set_password('password123')  # Default password

        # Save user to MongoDB
        user.save()

        # Create profile based on role
        if user.is_jobseeker():
            profile = JobseekerProfile(user=user)
            profile.save()
        flash('User created successfully!', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/user_form.html', form=form, title='Add User')

# Edit User
@admin_bp.route('/edit_user/<user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    try:
        user = User.objects.get(id=user_id)
    except:
        flash('User not found', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    form = AdminUserForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data

        if form.password.data:
            user.set_password(form.password.data)

        user.save()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/user_form.html', form=form, user=user, title='Edit User')

# Manage Jobs
@admin_bp.route('/jobs')
@admin_required
def manage_jobs():
    jobs = Job.objects.all()

    # Get page from query parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Create a list of all jobs
    all_jobs = list(jobs)

    # Calculate start and end indices for the current page
    start = (page - 1) * per_page
    end = start + per_page

    # Create pagination object
    pagination = MongoDBPagination(all_jobs, page, per_page)

    # Set items to only the current page's items
    pagination.items = all_jobs[start:end]

    return render_template('admin/manage_jobs.html', jobs=pagination)

# Add Job
@admin_bp.route('/add_job', methods=['GET', 'POST'])
@admin_required
def add_job():
    form = JobPostForm()

    # Get companies for the dropdown
    companies = Company.objects.all()
    form.company.choices = [(str(company.id), company.name) for company in companies]

    if form.validate_on_submit():
        company = Company.objects.get(id=form.company.data)

        job = Job(
            title=form.title.data,
            company=company,
            location=form.location.data,
            is_remote=form.is_remote.data,
            job_type=form.job_type.data,
            description=form.description.data,
            requirements=form.requirements.data,
            benefits=form.benefits.data,
            salary_min=form.salary_min.data,
            salary_max=form.salary_max.data,
            experience_required=form.experience_required.data,
            education_required=form.education_required.data,
            application_deadline=form.application_deadline.data,
            is_active=form.is_active.data,
            is_featured=form.is_featured.data,
            posted_date=datetime.now()
        )

        job.save()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('admin.manage_jobs'))

    return render_template('admin/job_form.html', form=form, title='Add Job')

# Edit Job
@admin_bp.route('/edit_job/<job_id>', methods=['GET', 'POST'])
@admin_required
def edit_job(job_id):
    try:
        job = Job.objects.get(id=job_id)
    except:
        flash('Job not found', 'danger')
        return redirect(url_for('admin.manage_jobs'))

    form = JobPostForm(obj=job)

    # Get companies for the dropdown
    companies = Company.objects.all()
    form.company.choices = [(str(company.id), company.name) for company in companies]

    # Set the selected company
    if request.method == 'GET':
        form.company.data = str(job.company.id)

    if form.validate_on_submit():
        company = Company.objects.get(id=form.company.data)

        job.title = form.title.data
        job.company = company
        job.location = form.location.data
        job.is_remote = form.is_remote.data
        job.job_type = form.job_type.data
        job.description = form.description.data
        job.requirements = form.requirements.data
        job.benefits = form.benefits.data
        job.salary_min = form.salary_min.data
        job.salary_max = form.salary_max.data
        job.experience_required = form.experience_required.data
        job.education_required = form.education_required.data
        job.application_deadline = form.application_deadline.data
        job.is_active = form.is_active.data
        job.is_featured = form.is_featured.data

        job.save()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('admin.manage_jobs'))

    return render_template('admin/job_form.html', form=form, job=job, title='Edit Job')

# Manage Companies
@admin_bp.route('/companies')
@admin_required
def manage_companies():
    companies = Company.objects.all()

    # Get page from query parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Create a list of all companies
    all_companies = list(companies)

    # Calculate start and end indices for the current page
    start = (page - 1) * per_page
    end = start + per_page

    # Create pagination object
    pagination = MongoDBPagination(all_companies, page, per_page)

    # Set items to only the current page's items
    pagination.items = all_companies[start:end]

    # Pass the Job model to the template
    return render_template('admin/manage_companies.html', companies=pagination, Job=Job)

# Add Company
@admin_bp.route('/add_company', methods=['GET', 'POST'])
@admin_required
def add_company():
    form = CompanyForm()

    if form.validate_on_submit():
        # Create new company
        company = Company(
            name=form.name.data,
            website=form.website.data,
            description=form.description.data,
            industry=form.industry.data,
            company_size=form.company_size.data,
            founded_year=form.founded_year.data,
            headquarters=form.headquarters.data,
            company_type=form.company_type.data
        )

        # Handle logo upload
        if form.logo.data:
            # Save logo to appropriate location
            # This is a placeholder - implement actual file saving logic
            company.logo = 'path/to/logo.jpg'

        company.save()
        flash('Company added successfully!', 'success')
        return redirect(url_for('admin.manage_companies'))

    return render_template('admin/company_form.html', form=form, title='Add Company')

# Edit Company
@admin_bp.route('/edit_company/<company_id>', methods=['GET', 'POST'])
@admin_required
def edit_company(company_id):
    try:
        company = Company.objects.get(id=company_id)
    except:
        flash('Company not found', 'danger')
        return redirect(url_for('admin.manage_companies'))

    form = CompanyForm(obj=company)

    if form.validate_on_submit():
        company.name = form.name.data
        company.website = form.website.data
        company.description = form.description.data
        company.industry = form.industry.data
        company.company_size = form.company_size.data
        company.founded_year = form.founded_year.data
        company.headquarters = form.headquarters.data
        company.company_type = form.company_type.data

        # Handle logo upload
        if form.logo.data:
            # Save logo to appropriate location
            # This is a placeholder - implement actual file saving logic
            company.logo = 'path/to/logo.jpg'

        company.save()
        flash('Company updated successfully', 'success')
        return redirect(url_for('admin.manage_companies'))

    return render_template('admin/company_form.html', form=form, company=company, title='Edit Company')

# Manage Applications
@admin_bp.route('/applications')
@admin_required
def manage_applications():
    applications = JobApplication.objects.all()

    # Get page from query parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Create a list of all applications
    all_applications = list(applications)

    # Calculate start and end indices for the current page
    start = (page - 1) * per_page
    end = start + per_page

    # Create pagination object
    pagination = MongoDBPagination(all_applications, page, per_page)

    # Set items to only the current page's items
    pagination.items = all_applications[start:end]

    return render_template('admin/manage_applications.html', applications=pagination)

# Manage Categories
@admin_bp.route('/categories')
@admin_required
def manage_categories():
    # Get page from query parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # For this example, we'll create a simple Category model
    # In a real application, you would have a proper Category model
    class Category:
        def __init__(self, id, name, description):
            self.id = id
            self.name = name
            self.description = description

    # Sample categories
    categories = [
        Category('1', 'Technology', 'Technology and IT related jobs'),
        Category('2', 'Healthcare', 'Healthcare and medical jobs'),
        Category('3', 'Finance', 'Finance and accounting jobs'),
        Category('4', 'Education', 'Education and teaching jobs'),
        Category('5', 'Marketing', 'Marketing and advertising jobs')
    ]

    # Create a list of all categories
    all_categories = list(categories)

    # Calculate start and end indices for the current page
    start = (page - 1) * per_page
    end = start + per_page

    # Create pagination object
    pagination = MongoDBPagination(all_categories, page, per_page)

    # Set items to only the current page's items
    pagination.items = all_categories[start:end]

    return render_template('admin/manage_categories.html', categories=pagination)

# Add Category
@admin_bp.route('/add_category', methods=['GET', 'POST'])
@admin_required
def add_category():
    form = AdminCompanyCategoryForm()

    if form.validate_on_submit():
        # In a real application, you would save the category to the database
        flash('Category added successfully!', 'success')
        return redirect(url_for('admin.manage_categories'))

    return render_template('admin/category_form.html', form=form, title='Add Category')

# Edit Category
@admin_bp.route('/edit_category/<category_id>', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    # In a real application, you would fetch the category from the database
    # For this example, we'll create a dummy category
    category = {
        'id': category_id,
        'name': 'Sample Category',
        'description': 'Sample description'
    }

    form = AdminCompanyCategoryForm()

    # Pre-populate the form with the category data
    if request.method == 'GET':
        form.name.data = category['name']
        form.description.data = category['description']

    if form.validate_on_submit():
        # In a real application, you would update the category in the database
        flash('Category updated successfully', 'success')
        return redirect(url_for('admin.manage_categories'))

    return render_template('admin/category_form.html', form=form, category=category, title='Edit Category')

# Google Analytics Setup
@admin_bp.route('/google_analytics_setup', methods=['GET', 'POST'])
@admin_required
def google_analytics_setup():
    # In a real application, you would have a Google Analytics service
    # For this example, we'll use dummy data

    if request.method == 'POST':
        # Process form data
        tracking_id = request.form.get('tracking_id')
        enable_analytics = request.form.get('enable_analytics') == 'on'
        anonymize_ip = request.form.get('anonymize_ip') == 'on'

        # Update Google Analytics settings
        # In a real application, you would save these settings to the database
        flash('Google Analytics settings updated successfully!', 'success')
        return redirect(url_for('admin.google_analytics_setup'))

    # Get current settings
    # In a real application, you would fetch these from the database
    tracking_id = 'UA-XXXXXXXX-X'
    enable_analytics = True
    anonymize_ip = True

    return render_template('admin/google_analytics_setup.html',
                          tracking_id=tracking_id,
                          enable_analytics=enable_analytics,
                          anonymize_ip=anonymize_ip)

# Manage Site Content
@admin_bp.route('/manage_site_content', methods=['GET', 'POST'])
@admin_required
def manage_site_content():
    # In a real application, you would have a form to update site content
    if request.method == 'POST':
        # Process form data
        # Save content to database
        flash('Site content updated successfully!', 'success')
        return redirect(url_for('admin.manage_site_content'))

    # For this example, we'll use dummy content
    site_content = {
        'home_title': 'Welcome to Remote Hive',
        'home_subtitle': 'Find your dream remote job',
        'about_content': 'Remote Hive is a job portal for remote workers.',
        'contact_email': 'contact@remotehive.com',
        'footer_text': '© 2023 Remote Hive. All rights reserved.'
    }

    return render_template('admin/site_content.html', content=site_content)

# Import/Export Data
@admin_bp.route('/import_export_data')
@admin_required
def import_export_data():
    # Dummy history data
    history = [
        {'type': 'Export', 'data_type': 'Users', 'format': 'CSV', 'date': '2025-05-01 14:30', 'status': 'Success'},
        {'type': 'Import', 'data_type': 'Jobs', 'format': 'Excel', 'date': '2025-04-28 10:15', 'status': 'Success'},
        {'type': 'Export', 'data_type': 'Companies', 'format': 'JSON', 'date': '2025-04-25 16:45', 'status': 'Success'},
        {'type': 'Import', 'data_type': 'Skills', 'format': 'CSV', 'date': '2025-04-20 09:30', 'status': 'Failed'},
        {'type': 'Export', 'data_type': 'Applications', 'format': 'PDF', 'date': '2025-04-15 11:20', 'status': 'Success'}
    ]

    return render_template('admin/import_export.html', history=history)

# Payment Settings
@admin_bp.route('/payment_settings', methods=['GET', 'POST'])
@admin_required
def payment_settings():
    if request.method == 'POST':
        payment_gateway = request.form.get('payment_gateway')
        api_key = request.form.get('api_key')
        secret_key = request.form.get('secret_key')

        # In a real application, you would save these settings securely
        flash(f'{payment_gateway} integration settings updated successfully!', 'success')
        return redirect(url_for('admin.payment_settings'))

    # For this example, we'll use dummy payment gateways
    payment_gateways = ['Stripe', 'PayPal', 'Razorpay', 'Braintree']

    # Dummy payment plans
    payment_plans = [
        {'id': '1', 'name': 'Basic', 'price': 29, 'features': ['Post up to 5 jobs', 'Basic analytics', 'Email support']},
        {'id': '2', 'name': 'Pro', 'price': 99, 'features': ['Post up to 20 jobs', 'Advanced analytics', 'Priority support', 'Featured listings']},
        {'id': '3', 'name': 'Enterprise', 'price': 299, 'features': ['Unlimited job postings', 'Custom analytics', 'Dedicated support', 'Featured listings', 'API access']}
    ]

    return render_template('admin/payment_settings.html',
                          payment_gateways=payment_gateways,
                          payment_plans=payment_plans)

# Job Scraper
@admin_bp.route('/job_scraper', methods=['GET', 'POST'])
@admin_required
def job_scraper():
    # In a real application, you would have a job scraper service
    # For this example, we'll use dummy data

    # Get all companies for the dropdown
    companies = Company.objects.all()

    # Initialize variables
    scraped_jobs = []
    job_data = None

    if request.method == 'POST':
        source_url = request.form.get('source_url')
        job_type = request.form.get('job_type', 'Full-time')
        is_remote = 'is_remote' in request.form

        if source_url:
            # In a real application, you would scrape job information
            # For this example, we'll use dummy data
            job_info = {
                'title': 'Software Engineer',
                'company_name': 'Example Company',
                'location': 'Remote' if is_remote else 'New York, NY',
                'description': 'Example job description',
                'requirements': '',
                'skills': ['Python', 'JavaScript', 'React'],
                'job_type': job_type,
                'is_remote': is_remote,
                'source': 'Example',
                'source_url': source_url,
                'status': 'new'
            }

            # Add to scraped jobs list
            scraped_jobs = [job_info]

            # Convert scraped jobs to JSON for form submission
            job_data = json.dumps(scraped_jobs)

            flash(f'Successfully scraped job from {job_info["source"]}', 'success')
        else:
            flash('Please provide a job URL to scrape.', 'warning')

    # Get recent imported jobs
    recent_jobs = Job.objects.order_by('-posted_date').limit(5)

    # If this is an AJAX request, return the job data as JSON or HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not scraped_jobs:
            return jsonify({
                'success': False,
                'message': 'Failed to scrape job from the provided URL. Please check the URL and try again.'
            }), 400

        # Create a table for display in the response
        table_html = f"""
        <table class="table">
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Company</th>
                    <th>Location</th>
                    <th>Job Type</th>
                    <th>Remote</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{scraped_jobs[0]['title']}</td>
                    <td>{scraped_jobs[0]['company_name']}</td>
                    <td>{scraped_jobs[0]['location']}</td>
                    <td>{scraped_jobs[0]['job_type']}</td>
                    <td>{'Yes' if scraped_jobs[0]['is_remote'] else 'No'}</td>
                </tr>
            </tbody>
        </table>
        <input type="hidden" name="job_data" value='{job_data}'>
        """

        return table_html

    # For regular requests, render the template with the scraped data
    return render_template('admin/job_scraper.html',
                          companies=companies,
                          scraped_jobs=scraped_jobs,
                          job_data=job_data,
                          recent_imported_jobs=recent_jobs)

# Export Data
@admin_bp.route('/export_data')
@admin_required
def export_data():
    """Export data to CSV, Excel, or JSON format"""
    data_type = request.args.get('data_type', 'users')
    export_format = request.args.get('export_format', 'csv')

    # In a real implementation, this would query the database and generate the export file
    # For now, just show a success message
    flash(f'Successfully exported {data_type} data as {export_format.upper()}', 'success')

    # Redirect back to the referring page
    return redirect(request.referrer or url_for('admin.admin_dashboard'))

# Company Details
@admin_bp.route('/company_details/<company_id>')
@admin_required
def company_details(company_id):
    """View detailed information about a company"""
    try:
        company = Company.objects.get(id=company_id)
    except:
        flash('Company not found', 'danger')
        return redirect(url_for('admin.manage_companies'))

    # Get jobs for this company
    company_jobs = Job.objects(company=company).order_by('-posted_date')

    return render_template('admin/company_details.html',
                          company=company,
                          company_jobs=company_jobs)

# Toggle Company Featured Status
@admin_bp.route('/toggle_company_featured/<company_id>', methods=['POST'])
@admin_required
def toggle_company_featured(company_id):
    """Toggle whether a company is featured"""
    try:
        company = Company.objects.get(id=company_id)
        company.is_featured = not company.is_featured
        company.save()

        status = "featured" if company.is_featured else "unfeatured"
        flash(f'Company {company.name} is now {status}', 'success')
    except:
        flash('Company not found', 'danger')

    # Redirect back to the referring page
    return redirect(request.referrer or url_for('admin.manage_companies'))
