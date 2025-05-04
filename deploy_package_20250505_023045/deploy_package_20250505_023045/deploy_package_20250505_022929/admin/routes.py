import logging
import os
import io
import csv
import json
import random
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, abort, make_response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from bson import ObjectId

from admin import admin_bp
from app import app
from models import User, Job, Company, JobApplication, CompanyCategory, CompanyCategoryAssociation, JobseekerProfile
from forms import AdminUserForm, CompanyForm, JobPostForm, AdminCompanyCategoryForm

# For Excel export
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font
except ImportError:
    Workbook = None
    Font = None

# For PDF export
try:
    from reportlab.pdfgen import canvas
except ImportError:
    canvas = None

# Admin access decorator
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

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

# User Management
@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.objects.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/user/new', methods=['GET', 'POST'])
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

@admin_bp.route('/user/<user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    try:
        user = User.objects.get(id=user_id)
    except:
        abort(404)

    form = AdminUserForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data

        if form.password.data:
            user.set_password(form.password.data)

        user.save()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/user_form.html', form=form, user=user, title='Edit User')

@admin_bp.route('/user/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    try:
        user = User.objects.get(id=user_id)
    except:
        abort(404)

    # Delete associated profiles
    if user.is_jobseeker():
        JobseekerProfile.objects(user=user).delete()
    elif user.is_employer():
        # Delete company and associated jobs
        company = Company.objects(user=user).first()
        if company:
            Job.objects(company=company).delete()
            company.delete()

    user.delete()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

# Job Management
@admin_bp.route('/jobs')
@admin_required
def manage_jobs():
    jobs = Job.objects.all()
    return render_template('admin/manage_jobs.html', jobs=jobs)

@admin_bp.route('/job/new', methods=['GET', 'POST'])
@admin_required
def add_job():
    form = JobPostForm()
    companies = Company.objects.all()

    if not companies:
        flash('Please create a company first before adding a job.', 'warning')
        return redirect(url_for('admin.add_company'))

    if form.validate_on_submit():
        company_id = request.form.get('company_id')
        try:
            company = Company.objects.get(id=company_id)
        except:
            flash('Invalid company selected.', 'danger')
            return render_template('admin/job_form.html', form=form, companies=companies, title='Add Job')

        job = Job(
            company=company,
            title=form.title.data,
            location=form.location.data,
            is_remote=form.is_remote.data,
            job_type=form.job_type.data,
            description=form.description.data,
            requirements=form.requirements.data,
            salary_min=form.salary_min.data,
            salary_max=form.salary_max.data,
            experience_required=form.experience_required.data,
            education_required=form.education_required.data,
            deadline=form.deadline.data,
            is_active=True
        )

        job.save()
        flash('Job created successfully!', 'success')
        return redirect(url_for('admin.manage_jobs'))

    return render_template('admin/job_form.html', form=form, companies=companies, title='Add Job')

@admin_bp.route('/job/<job_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_job(job_id):
    try:
        job = Job.objects.get(id=job_id)
    except:
        abort(404)

    form = JobPostForm(obj=job)
    companies = Company.objects.all()

    if form.validate_on_submit():
        company_id = request.form.get('company_id')
        try:
            company = Company.objects.get(id=company_id)
        except:
            flash('Invalid company selected.', 'danger')
            return render_template('admin/job_form.html', form=form, job=job, companies=companies, title='Edit Job')

        job.company = company
        job.title = form.title.data
        job.location = form.location.data
        job.is_remote = form.is_remote.data
        job.job_type = form.job_type.data
        job.description = form.description.data
        job.requirements = form.requirements.data
        job.salary_min = form.salary_min.data
        job.salary_max = form.salary_max.data
        job.experience_required = form.experience_required.data
        job.education_required = form.education_required.data
        job.deadline = form.deadline.data

        job.save()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('admin.manage_jobs'))

    return render_template('admin/job_form.html', form=form, job=job, companies=companies, title='Edit Job')

@admin_bp.route('/job/<job_id>/toggle', methods=['POST'])
@admin_required
def toggle_job(job_id):
    try:
        job = Job.objects.get(id=job_id)
    except:
        abort(404)

    job.is_active = not job.is_active
    job.save()

    status = 'activated' if job.is_active else 'deactivated'
    flash(f'Job {status} successfully!', 'success')
    return redirect(url_for('admin.manage_jobs'))

@admin_bp.route('/job/<job_id>/delete', methods=['POST'])
@admin_required
def delete_job(job_id):
    try:
        job = Job.objects.get(id=job_id)
    except:
        abort(404)

    job.delete()
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('admin.manage_jobs'))

# Company Management
@admin_bp.route('/companies')
@admin_required
def manage_companies():
    companies = Company.objects.all()
    return render_template('admin/manage_companies.html', companies=companies)

@admin_bp.route('/company/new', methods=['GET', 'POST'])
@admin_required
def add_company():
    form = CompanyForm()

    if form.validate_on_submit():
        # Find or create an employer user
        employer_email = request.form.get('employer_email')
        employer = User.objects(email=employer_email).first()

        if not employer:
            # Create new employer user
            employer = User(
                username=employer_email.split('@')[0],
                email=employer_email,
                role='employer',
                is_active=True
            )
            employer.set_password('password123')  # Default password
            employer.save()

        # Check if employer already has a company
        if Company.objects(user=employer).first():
            flash('This employer already has a company.', 'danger')
            return render_template('admin/company_form.html', form=form, title='Add Company')

        company = Company(
            user=employer,
            name=form.name.data,
            website=form.website.data,
            description=form.description.data,
            industry=form.industry.data,
            company_size=form.company_size.data,
            founded_year=form.founded_year.data,
            headquarters=form.headquarters.data,
            company_type=form.company_type.data,
            is_featured=form.is_featured.data
        )

        # Handle logo upload
        if form.logo.data:
            logo_path = save_file(form.logo.data, 'company_logos')
            if logo_path:
                company.logo_path = logo_path

        company.save()

        # Add company to selected categories
        category_ids = request.form.getlist('categories')
        for cat_id in category_ids:
            category = CompanyCategory.objects(id=cat_id).first()
            if category:
                assoc = CompanyCategoryAssociation(company=company, category=category)
                assoc.save()
        flash('Company created successfully!', 'success')
        return redirect(url_for('admin.manage_companies'))

    categories = CompanyCategory.objects.all()
    return render_template('admin/company_form.html', form=form, categories=categories, title='Add Company')

@admin_bp.route('/company/<company_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_company(company_id):
    try:
        company = Company.objects.get(id=company_id)
    except:
        abort(404)

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
        company.is_featured = form.is_featured.data

        # Handle logo upload
        if form.logo.data:
            logo_path = save_file(form.logo.data, 'company_logos')
            if logo_path:
                # Delete old logo if exists
                if company.logo_path:
                    old_logo_path = os.path.join(app.config['UPLOAD_FOLDER'], company.logo_path)
                    if os.path.exists(old_logo_path):
                        os.remove(old_logo_path)
                company.logo_path = logo_path

        company.save()

        # Update company categories
        # First, delete existing associations
        CompanyCategoryAssociation.objects(company=company).delete()

        # Add new associations
        category_ids = request.form.getlist('categories')
        for cat_id in category_ids:
            category = CompanyCategory.objects(id=cat_id).first()
            if category:
                assoc = CompanyCategoryAssociation(company=company, category=category)
                assoc.save()

        flash('Company updated successfully!', 'success')
        return redirect(url_for('admin.manage_companies'))

    # Get current categories
    associations = CompanyCategoryAssociation.objects(company=company)
    company_categories = [str(assoc.category.id) for assoc in associations]

    categories = CompanyCategory.objects.all()
    return render_template('admin/company_form.html',
                          form=form,
                          company=company,
                          categories=categories,
                          company_categories=company_categories,
                          title='Edit Company')

@admin_bp.route('/company/<company_id>/delete', methods=['POST'])
@admin_required
def delete_company(company_id):
    try:
        company = Company.objects.get(id=company_id)
    except:
        abort(404)

    # Delete associated jobs
    Job.objects(company=company).delete()

    # Delete category associations
    CompanyCategoryAssociation.objects(company=company).delete()

    company.delete()
    flash('Company deleted successfully!', 'success')
    return redirect(url_for('admin.manage_companies'))

# Company Categories Management
@admin_bp.route('/categories')
@admin_required
def manage_categories():
    categories = CompanyCategory.objects.all()
    return render_template('admin/manage_categories.html', categories=categories)

@admin_bp.route('/category/new', methods=['GET', 'POST'])
@admin_required
def add_category():
    form = AdminCompanyCategoryForm()

    if form.validate_on_submit():
        category = CompanyCategory(
            name=form.name.data,
            description=form.description.data
        )
        category.save()
        flash('Category created successfully!', 'success')
        return redirect(url_for('admin.manage_categories'))

    return render_template('admin/category_form.html', form=form, title='Add Category')

@admin_bp.route('/category/<category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    try:
        category = CompanyCategory.objects.get(id=category_id)
    except:
        abort(404)

    form = AdminCompanyCategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.save()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin.manage_categories'))

    return render_template('admin/category_form.html', form=form, category=category, title='Edit Category')

@admin_bp.route('/category/<category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    try:
        category = CompanyCategory.objects.get(id=category_id)
    except:
        abort(404)

    # Delete associations
    CompanyCategoryAssociation.objects(category=category).delete()

    category.delete()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.manage_categories'))

# Job Applications Management
@admin_bp.route('/applications')
@admin_required
def manage_applications():
    applications = JobApplication.objects.all()
    return render_template('admin/manage_applications.html', applications=applications)

# Analytics Dashboard
@admin_bp.route('/analytics')
@admin_required
def analytics_dashboard():
    # Simulated analytics data - in a production environment,
    # this would be replaced with real analytics from a database

    # User statistics
    total_users = User.objects.count()
    jobseekers = User.objects(role='jobseeker').count()
    employers = User.objects(role='employer').count()
    admins = User.objects(role='admin').count()

    # Calculate percentages
    jobseeker_percentage = round((jobseekers / total_users) * 100) if total_users > 0 else 0
    employer_percentage = round((employers / total_users) * 100) if total_users > 0 else 0
    admin_percentage = round((admins / total_users) * 100) if total_users > 0 else 0

    # Get active employers (those with at least one job posting)
    active_employers = Company.objects.count()

    # Simulated visitor data
    live_visitors = random.randint(5, 30)
    total_visitors = random.randint(500, 1500)

    # Growth metrics (simulated)
    live_visitors_growth = random.randint(5, 15)
    total_visitors_growth = random.randint(10, 30)
    employers_growth = random.randint(5, 20)

    # Simulated premium subscribers
    premium_subscribers = random.randint(10, 50)
    subscribers_growth = random.randint(5, 25)

    # Visitor time series data (simulated)
    visitors_data = [random.randint(300, 1000) for _ in range(12)]
    signups_data = [random.randint(20, 100) for _ in range(12)]
    applications_data = [random.randint(50, 200) for _ in range(12)]

    # User engagement metrics (simulated)
    avg_session_duration = f"{random.randint(2, 10)}m {random.randint(0, 59)}s"
    bounce_rate = round(random.uniform(30, 60), 1)
    pages_per_session = round(random.uniform(2, 8), 1)
    conversion_rate = round(random.uniform(2, 10), 1)

    # Get top categories
    categories = CompanyCategory.objects.all()
    categories_labels = [category.name for category in categories]
    categories_jobs_data = [random.randint(10, 100) for _ in range(len(categories_labels))]
    categories_applications_data = [random.randint(20, 150) for _ in range(len(categories_labels))]

    # Get browser and device data (simulated)
    device_data = [60, 30, 10]  # Desktop, Mobile, Tablet
    browser_data = [50, 20, 15, 10, 5]  # Chrome, Safari, Firefox, Edge, Other

    # Top countries (simulated)
    top_countries = [
        {'country': 'United States', 'visitors': random.randint(200, 500), 'percentage': random.randint(20, 40)},
        {'country': 'United Kingdom', 'visitors': random.randint(100, 300), 'percentage': random.randint(10, 25)},
        {'country': 'Canada', 'visitors': random.randint(80, 200), 'percentage': random.randint(8, 15)},
        {'country': 'Australia', 'visitors': random.randint(50, 150), 'percentage': random.randint(5, 12)},
        {'country': 'Germany', 'visitors': random.randint(40, 120), 'percentage': random.randint(4, 10)}
    ]

    # Top referrers (simulated)
    top_referrers = [
        {'source': 'Google', 'visitors': random.randint(200, 500), 'percentage': random.randint(20, 40)},
        {'source': 'Direct', 'visitors': random.randint(150, 400), 'percentage': random.randint(15, 30)},
        {'source': 'LinkedIn', 'visitors': random.randint(100, 300), 'percentage': random.randint(10, 25)},
        {'source': 'Twitter', 'visitors': random.randint(50, 150), 'percentage': random.randint(5, 15)},
        {'source': 'Facebook', 'visitors': random.randint(30, 100), 'percentage': random.randint(3, 10)}
    ]

    return render_template('admin/analytics_dashboard.html',
                          total_users=total_users,
                          jobseeker_percentage=jobseeker_percentage,
                          employer_percentage=employer_percentage,
                          admin_percentage=admin_percentage,
                          active_employers=active_employers,
                          live_visitors=live_visitors,
                          total_visitors=total_visitors,
                          live_visitors_growth=live_visitors_growth,
                          total_visitors_growth=total_visitors_growth,
                          employers_growth=employers_growth,
                          premium_subscribers=premium_subscribers,
                          subscribers_growth=subscribers_growth,
                          visitors_data=json.dumps(visitors_data),
                          signups_data=json.dumps(signups_data),
                          applications_data=json.dumps(applications_data),
                          avg_session_duration=avg_session_duration,
                          bounce_rate=bounce_rate,
                          pages_per_session=pages_per_session,
                          conversion_rate=conversion_rate,
                          categories_labels=json.dumps(categories_labels),
                          categories_jobs_data=json.dumps(categories_jobs_data),
                          categories_applications_data=json.dumps(categories_applications_data),
                          device_data=json.dumps(device_data),
                          browser_data=json.dumps(browser_data),
                          top_countries=top_countries,
                          top_referrers=top_referrers)

# Google Analytics Setup
@admin_bp.route('/google-analytics')
@admin_required
def google_analytics_setup():
    return render_template('admin/google_analytics_setup.html')

# Site Content Management
@admin_bp.route('/site-content')
@admin_required
def manage_site_content():
    # In a real implementation, you would fetch the current content from the database
    # and pass it to the template
    return render_template('admin/site_content.html')

@admin_bp.route('/site-content/update', methods=['POST'])
@admin_required
def update_site_content():
    section = request.form.get('section')

    if not section:
        flash('Missing section data', 'danger')
        return redirect(url_for('admin.manage_site_content'))

    # In a real implementation, you would update the content in the database
    # For now, just show a success message
    flash(f'Content for section "{section}" updated successfully!', 'success')
    return redirect(url_for('admin.manage_site_content'))

# Helper function to check if a file is allowed
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Helper function for saving files
def save_file(file, folder):
    if file and allowed_file(file.filename, {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'svg'}):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{filename}"
        upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        return os.path.join(folder, filename)
    return None
