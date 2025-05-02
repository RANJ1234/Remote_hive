import logging
import os
import json
import random
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import app, db
from models import User, Job, Company, JobseekerProfile, JobApplication, CompanyReview, CompanyCategory, CompanyCategoryAssociation, Skill
from forms import AdminUserForm, AdminCompanyCategoryForm, CompanyForm, JobPostForm
from web_scraper import get_website_text_content

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
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_jobs = Job.query.count()
    total_companies = Company.query.count()
    total_applications = JobApplication.query.count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_jobs = Job.query.order_by(Job.posted_date.desc()).limit(5).all()
    
    # Job statistics
    active_jobs = Job.query.filter_by(is_active=True).count()
    remote_jobs = Job.query.filter_by(is_remote=True).count()
    
    # Top companies by job count
    top_companies_by_jobs = db.session.query(
        Company, db.func.count(Job.id).label('job_count')
    ).join(Job).group_by(Company).order_by(db.text('job_count DESC')).limit(5).all()
    
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
@app.route('/admin/users')
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/user/new', methods=['GET', 'POST'])
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
        
        db.session.add(user)
        db.session.flush()  # Get user ID before committing
        
        # Create profile based on role
        if user.is_jobseeker():
            profile = JobseekerProfile(user_id=user.id)
            db.session.add(profile)
        
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('admin/user_form.html', form=form, title='Add User')

@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminUserForm(obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('admin/user_form.html', form=form, user=user, title='Edit User')

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('manage_users'))

# Job Management
@app.route('/admin/jobs')
@admin_required
def manage_jobs():
    page = request.args.get('page', 1, type=int)
    jobs = Job.query.order_by(Job.posted_date.desc()).paginate(page=page, per_page=20)
    return render_template('admin/manage_jobs.html', jobs=jobs)

@app.route('/admin/job/new', methods=['GET', 'POST'])
@admin_required
def add_job():
    form = JobPostForm()
    companies = Company.query.all()
    
    if not companies:
        flash('Please create a company first before adding a job.', 'warning')
        return redirect(url_for('add_company'))
    
    if form.validate_on_submit():
        company_id = request.form.get('company_id')
        company = Company.query.get(company_id)
        
        if not company:
            flash('Invalid company selected.', 'danger')
            return render_template('admin/job_form.html', form=form, companies=companies, title='Add Job')
        
        job = Job(
            company_id=company.id,
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
        
        db.session.add(job)
        db.session.commit()
        flash('Job created successfully!', 'success')
        return redirect(url_for('manage_jobs'))
    
    return render_template('admin/job_form.html', form=form, companies=companies, title='Add Job')

@app.route('/admin/job/<int:job_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    form = JobPostForm(obj=job)
    companies = Company.query.all()
    
    if form.validate_on_submit():
        company_id = request.form.get('company_id')
        company = Company.query.get(company_id)
        
        if not company:
            flash('Invalid company selected.', 'danger')
            return render_template('admin/job_form.html', form=form, job=job, companies=companies, title='Edit Job')
        
        job.company_id = company.id
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
        
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('manage_jobs'))
    
    return render_template('admin/job_form.html', form=form, job=job, companies=companies, title='Edit Job')

@app.route('/admin/job/<int:job_id>/toggle', methods=['POST'])
@admin_required
def toggle_job_status(job_id):
    job = Job.query.get_or_404(job_id)
    job.is_active = not job.is_active
    db.session.commit()
    status = 'activated' if job.is_active else 'deactivated'
    flash(f'Job {status} successfully!', 'success')
    return redirect(url_for('manage_jobs'))

@app.route('/admin/job/<int:job_id>/delete', methods=['POST'])
@admin_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('manage_jobs'))

# Company Management
@app.route('/admin/companies')
@admin_required
def manage_companies():
    page = request.args.get('page', 1, type=int)
    companies = Company.query.paginate(page=page, per_page=20)
    return render_template('admin/manage_companies.html', companies=companies)

@app.route('/admin/company/new', methods=['GET', 'POST'])
@admin_required
def add_company():
    form = CompanyForm()
    
    if form.validate_on_submit():
        # Find or create an employer user
        employer_email = request.form.get('employer_email')
        employer = User.query.filter_by(email=employer_email).first()
        
        if not employer:
            # Create new employer user
            employer = User(
                username=employer_email.split('@')[0],
                email=employer_email,
                role='employer',
                is_active=True
            )
            employer.set_password('password123')  # Default password
            db.session.add(employer)
            db.session.flush()
        
        # Check if employer already has a company
        if Company.query.filter_by(user_id=employer.id).first():
            flash('This employer already has a company.', 'danger')
            return render_template('admin/company_form.html', form=form, title='Add Company')
        
        # Create company
        company = Company(
            user_id=employer.id,
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
            logo_path = save_file(form.logo.data, 'company_logos')
            if logo_path:
                company.logo_path = logo_path
        
        db.session.add(company)
        
        # Add company to selected categories
        category_ids = request.form.getlist('categories')
        for cat_id in category_ids:
            assoc = CompanyCategoryAssociation(company_id=company.id, category_id=cat_id)
            db.session.add(assoc)
        
        db.session.commit()
        flash('Company created successfully!', 'success')
        return redirect(url_for('manage_companies'))
    
    categories = CompanyCategory.query.all()
    return render_template('admin/company_form.html', form=form, categories=categories, title='Add Company')

@app.route('/admin/company/<int:company_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_company(company_id):
    company = Company.query.get_or_404(company_id)
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
            logo_path = save_file(form.logo.data, 'company_logos')
            if logo_path:
                # Delete old logo if exists
                if company.logo_path:
                    old_logo_path = os.path.join(app.config['UPLOAD_FOLDER'], company.logo_path)
                    if os.path.exists(old_logo_path):
                        os.remove(old_logo_path)
                company.logo_path = logo_path
        
        # Update company categories
        CompanyCategoryAssociation.query.filter_by(company_id=company.id).delete()
        
        category_ids = request.form.getlist('categories')
        for cat_id in category_ids:
            assoc = CompanyCategoryAssociation(company_id=company.id, category_id=cat_id)
            db.session.add(assoc)
        
        # Update featured status
        company.is_featured = 'featured' in request.form
        
        db.session.commit()
        flash('Company updated successfully!', 'success')
        return redirect(url_for('manage_companies'))
    
    categories = CompanyCategory.query.all()
    company_categories = [assoc.category_id for assoc in CompanyCategoryAssociation.query.filter_by(company_id=company.id).all()]
    
    return render_template('admin/company_form.html', 
                           form=form, 
                           company=company, 
                           categories=categories,
                           company_categories=company_categories,
                           title='Edit Company')

@app.route('/admin/company/<int:company_id>/toggle_featured', methods=['POST'])
@admin_required
def toggle_company_featured(company_id):
    company = Company.query.get_or_404(company_id)
    company.is_featured = not company.is_featured
    db.session.commit()
    status = 'featured' if company.is_featured else 'unfeatured'
    flash(f'Company {status} successfully!', 'success')
    return redirect(url_for('manage_companies'))

@app.route('/admin/company/<int:company_id>/delete', methods=['POST'])
@admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    
    # Delete logo file if exists
    if company.logo_path:
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], company.logo_path)
        if os.path.exists(logo_path):
            os.remove(logo_path)
    
    db.session.delete(company)
    db.session.commit()
    flash('Company deleted successfully!', 'success')
    return redirect(url_for('manage_companies'))

# Company Categories Management
@app.route('/admin/categories')
@admin_required
def manage_categories():
    categories = CompanyCategory.query.all()
    return render_template('admin/manage_categories.html', categories=categories)

@app.route('/admin/category/new', methods=['GET', 'POST'])
@admin_required
def add_category():
    form = AdminCompanyCategoryForm()
    
    if form.validate_on_submit():
        category = CompanyCategory(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('manage_categories'))
    
    return render_template('admin/category_form.html', form=form, title='Add Category')

@app.route('/admin/category/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    category = CompanyCategory.query.get_or_404(category_id)
    form = AdminCompanyCategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('manage_categories'))
    
    return render_template('admin/category_form.html', form=form, category=category, title='Edit Category')

@app.route('/admin/category/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    category = CompanyCategory.query.get_or_404(category_id)
    
    # Delete associations first
    CompanyCategoryAssociation.query.filter_by(category_id=category.id).delete()
    
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('manage_categories'))

# Job Scraper
@app.route('/admin/job-scraper', methods=['GET', 'POST'])
@admin_required
def job_scraper():
    companies = Company.query.all()
    recent_imported_jobs = Job.query.filter(Job.description.like('%[Imported from%')).order_by(Job.posted_date.desc()).limit(5).all()
    scraped_jobs = None
    job_data = None
    
    if request.method == 'POST':
        source_url = request.form.get('source_url')
        source_site = request.form.get('source_site')
        company_id = request.form.get('company_id')
        job_type = request.form.get('job_type')
        is_remote = True if request.form.get('is_remote') else False
        
        try:
            # Get company
            company = Company.query.get(company_id)
            if not company:
                flash('Company not found', 'danger')
                return redirect(url_for('job_scraper'))
            
            # Use web scraper to extract job content
            content = get_website_text_content(source_url)
            
            if not content:
                flash('Failed to scrape content from the URL', 'danger')
                return redirect(url_for('job_scraper'))
            
            # Process content to extract jobs
            # This is a simplified implementation
            # In a real system, we would use NLP and more sophisticated parsing
            lines = content.split('\n')
            job_titles = []
            descriptions = []
            
            # Extract potential job titles (lines that might be job titles)
            for i, line in enumerate(lines):
                line = line.strip()
                if len(line) > 10 and len(line) < 100 and not line.endswith('.'):
                    if any(keyword in line.lower() for keyword in ['developer', 'engineer', 'designer', 'manager', 'specialist', 'analyst']):
                        job_titles.append((line, i))
            
            # Extract descriptions for each job title
            scraped_jobs = []
            for title, position in job_titles[:5]:  # Limit to 5 jobs
                # Get text after job title as description (limited to next 20 lines)
                description = '\n'.join(lines[position+1:position+20])
                
                # Create a dictionary for each job
                job_dict = {
                    'title': title,
                    'company_name': company.name,
                    'company_id': company.id,
                    'description': description,
                    'job_type': job_type,
                    'is_remote': is_remote,
                    'source': source_site,
                    'source_url': source_url,
                    'status': 'new'
                }
                
                # Check if job already exists
                if Job.query.filter_by(title=title, company_id=company.id).first():
                    job_dict['status'] = 'exists'
                
                scraped_jobs.append(job_dict)
            
            job_data = json.dumps(scraped_jobs)
            
            if not scraped_jobs:
                flash('No jobs could be extracted from the content', 'warning')
        
        except Exception as e:
            logging.error(f"Error scraping jobs: {str(e)}")
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('admin/job_scraper.html', 
                          companies=companies, 
                          scraped_jobs=scraped_jobs, 
                          job_data=job_data,
                          recent_imported_jobs=recent_imported_jobs)

@app.route('/admin/import-scraped-jobs', methods=['POST'])
@admin_required
def import_scraped_jobs():
    job_data = request.form.get('job_data')
    
    if not job_data:
        flash('No job data to import', 'danger')
        return redirect(url_for('job_scraper'))
    
    try:
        jobs = json.loads(job_data)
        imported_count = 0
        
        for job_dict in jobs:
            if job_dict['status'] != 'exists':
                # Create new job
                job = Job(
                    company_id=job_dict['company_id'],
                    title=job_dict['title'],
                    description=f"{job_dict['description']}\n\n[Imported from {job_dict['source']} on {datetime.now().strftime('%Y-%m-%d')}]",
                    job_type=job_dict['job_type'],
                    is_remote=job_dict['is_remote'],
                    is_active=True,
                    location="Remote" if job_dict['is_remote'] else "Not specified",
                    requirements="Not specified",
                    posted_date=datetime.now()
                )
                
                db.session.add(job)
                imported_count += 1
        
        db.session.commit()
        flash(f'Successfully imported {imported_count} jobs', 'success')
    
    except Exception as e:
        logging.error(f"Error importing jobs: {str(e)}")
        db.session.rollback()
        flash(f'Error importing jobs: {str(e)}', 'danger')
    
    return redirect(url_for('job_scraper'))

# Analytics Dashboard
@app.route('/admin/analytics')
@admin_required
def analytics_dashboard():
    # Simulated analytics data - in a production environment, 
    # this would be replaced with real analytics from a database
    
    # User statistics
    total_users = User.query.count()
    jobseekers = User.query.filter_by(role='jobseeker').count()
    employers = User.query.filter_by(role='employer').count()
    admins = User.query.filter_by(role='admin').count()
    
    # Calculate percentages
    jobseeker_percentage = round((jobseekers / total_users) * 100) if total_users > 0 else 0
    employer_percentage = round((employers / total_users) * 100) if total_users > 0 else 0
    admin_percentage = round((admins / total_users) * 100) if total_users > 0 else 0
    
    # Get active employers (those with at least one job posting)
    active_employers = db.session.query(Company.user_id).distinct().count()
    
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
    categories = CompanyCategory.query.all()
    categories_labels = [category.name for category in categories]
    categories_jobs_data = [random.randint(10, 100) for _ in range(len(categories_labels))]
    categories_applications_data = [random.randint(20, 150) for _ in range(len(categories_labels))]
    
    # Get browser and device data (simulated)
    device_data = [60, 30, 10]  # Desktop, Mobile, Tablet
    browser_data = [50, 20, 15, 10, 5]  # Chrome, Safari, Firefox, Edge, Other
    
    # Geographic data (simulated)
    top_countries = [
        {'name': 'United States', 'visitors': random.randint(300, 800), 'percentage': random.randint(30, 50)},
        {'name': 'India', 'visitors': random.randint(100, 400), 'percentage': random.randint(10, 30)},
        {'name': 'United Kingdom', 'visitors': random.randint(50, 200), 'percentage': random.randint(5, 15)},
        {'name': 'Germany', 'visitors': random.randint(30, 150), 'percentage': random.randint(3, 10)},
        {'name': 'Canada', 'visitors': random.randint(20, 100), 'percentage': random.randint(2, 8)}
    ]
    
    # Referrer data (simulated)
    top_referrers = [
        {'source': 'Google', 'visitors': random.randint(200, 600), 'conversion': round(random.uniform(2, 8), 1)},
        {'source': 'Direct', 'visitors': random.randint(100, 400), 'conversion': round(random.uniform(5, 15), 1)},
        {'source': 'LinkedIn', 'visitors': random.randint(50, 300), 'conversion': round(random.uniform(8, 20), 1)},
        {'source': 'Facebook', 'visitors': random.randint(30, 200), 'conversion': round(random.uniform(1, 10), 1)},
        {'source': 'Twitter', 'visitors': random.randint(20, 100), 'conversion': round(random.uniform(1, 5), 1)}
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
@app.route('/admin/google-analytics')
@admin_required
def google_analytics_setup():
    return render_template('admin/google_analytics_setup.html')

@app.route('/admin/google-analytics/save', methods=['POST'])
@admin_required
def save_google_analytics():
    tracking_id = request.form.get('tracking_id')
    # In a production environment, we would save this to database
    # or environment variables
    # For now, just simulate success
    flash('Google Analytics tracking ID saved successfully!', 'success')
    return redirect(url_for('google_analytics_setup'))

# Application Management
@app.route('/admin/applications')
@admin_required
def manage_applications():
    page = request.args.get('page', 1, type=int)
    applications = JobApplication.query.order_by(JobApplication.applied_date.desc()).paginate(page=page, per_page=20)
    return render_template('admin/manage_applications.html', applications=applications)

@app.route('/admin/application/<int:application_id>/status', methods=['POST'])
@admin_required
def update_application_status(application_id):
    application = JobApplication.query.get_or_404(application_id)
    new_status = request.form.get('status')
    
    if new_status in ['applied', 'reviewed', 'shortlisted', 'rejected', 'hired']:
        application.status = new_status
        application.last_updated = datetime.utcnow()
        db.session.commit()
        flash('Application status updated successfully!', 'success')
    else:
        flash('Invalid status provided.', 'danger')
    
    return redirect(url_for('manage_applications'))

@app.route('/admin/application/<int:application_id>/delete', methods=['POST'])
@admin_required
def delete_application(application_id):
    application = JobApplication.query.get_or_404(application_id)
    
    # Delete resume file if exists
    if application.resume_path:
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], application.resume_path)
        if os.path.exists(resume_path):
            os.remove(resume_path)
    
    db.session.delete(application)
    db.session.commit()
    flash('Application deleted successfully!', 'success')
    return redirect(url_for('manage_applications'))

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

# Helper function for allowed file types
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
