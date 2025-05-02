import os
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import app, db
from models import Company, Job, JobApplication, User, CompanyCategoryAssociation
from forms import CompanyForm, JobPostForm

# Employer access decorator
def employer_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_employer():
            abort(403)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Dashboard
@app.route('/employer/dashboard')
@employer_required
def employer_dashboard():
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if not company:
        flash('Please set up your company profile first.', 'info')
        return redirect(url_for('employer_company_profile'))
    
    jobs = Job.query.filter_by(company_id=company.id).all()
    
    # Get application statistics
    total_jobs = len(jobs)
    active_jobs = len([j for j in jobs if j.is_active])
    total_applications = sum(j.applications_count for j in jobs)
    
    # Get recent applications
    recent_applications = db.session.query(JobApplication, Job).join(
        Job, JobApplication.job_id == Job.id
    ).filter(
        Job.company_id == company.id
    ).order_by(
        JobApplication.applied_date.desc()
    ).limit(5).all()
    
    # Get application statistics by status
    application_stats = db.session.query(
        JobApplication.status, db.func.count(JobApplication.id)
    ).join(
        Job, JobApplication.job_id == Job.id
    ).filter(
        Job.company_id == company.id
    ).group_by(
        JobApplication.status
    ).all()
    
    stats_data = {status: count for status, count in application_stats}
    
    return render_template('employer/dashboard.html',
                           company=company,
                           total_jobs=total_jobs,
                           active_jobs=active_jobs,
                           total_applications=total_applications,
                           recent_applications=recent_applications,
                           stats_data=stats_data)

# Company Profile
@app.route('/employer/company-profile', methods=['GET', 'POST'])
@employer_required
def employer_company_profile():
    company = Company.query.filter_by(user_id=current_user.id).first()
    form = CompanyForm(obj=company)
    
    if form.validate_on_submit():
        if not company:
            company = Company(user_id=current_user.id)
            db.session.add(company)
        
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
        
        db.session.commit()
        flash('Company profile updated successfully!', 'success')
        return redirect(url_for('employer_dashboard'))
    
    from models import CompanyCategory
    categories = CompanyCategory.query.all()
    company_categories = []
    
    if company:
        company_categories = [assoc.category_id for assoc in CompanyCategoryAssociation.query.filter_by(company_id=company.id).all()]
    
    return render_template('employer/company_profile.html', 
                          form=form, 
                          company=company,
                          categories=categories,
                          company_categories=company_categories)

@app.route('/employer/company-profile/categories', methods=['POST'])
@employer_required
def update_company_categories():
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if not company:
        flash('Please create your company profile first.', 'warning')
        return redirect(url_for('employer_company_profile'))
    
    # Delete existing associations
    CompanyCategoryAssociation.query.filter_by(company_id=company.id).delete()
    
    # Add new associations
    category_ids = request.form.getlist('categories')
    for cat_id in category_ids:
        assoc = CompanyCategoryAssociation(company_id=company.id, category_id=cat_id)
        db.session.add(assoc)
    
    db.session.commit()
    flash('Company categories updated successfully!', 'success')
    return redirect(url_for('employer_company_profile'))

# Job Management
@app.route('/employer/jobs')
@employer_required
def employer_jobs():
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if not company:
        flash('Please set up your company profile first.', 'info')
        return redirect(url_for('employer_company_profile'))
    
    jobs = Job.query.filter_by(company_id=company.id).order_by(Job.posted_date.desc()).all()
    return render_template('employer/jobs.html', jobs=jobs, company=company)

@app.route('/employer/job/new', methods=['GET', 'POST'])
@employer_required
def employer_post_job():
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if not company:
        flash('Please set up your company profile first.', 'info')
        return redirect(url_for('employer_company_profile'))
    
    form = JobPostForm()
    
    if form.validate_on_submit():
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
        flash('Job posted successfully!', 'success')
        return redirect(url_for('employer_jobs'))
    
    return render_template('employer/post_job.html', form=form, company=company)

@app.route('/employer/job/<int:job_id>/edit', methods=['GET', 'POST'])
@employer_required
def employer_edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    # Ensure job belongs to this employer
    if job.company_id != company.id:
        abort(403)
    
    form = JobPostForm(obj=job)
    
    if form.validate_on_submit():
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
        return redirect(url_for('employer_jobs'))
    
    return render_template('employer/post_job.html', form=form, job=job, company=company)

@app.route('/employer/job/<int:job_id>/toggle', methods=['POST'])
@employer_required
def employer_toggle_job(job_id):
    job = Job.query.get_or_404(job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    # Ensure job belongs to this employer
    if job.company_id != company.id:
        abort(403)
    
    job.is_active = not job.is_active
    db.session.commit()
    
    status = 'activated' if job.is_active else 'deactivated'
    flash(f'Job {status} successfully!', 'success')
    return redirect(url_for('employer_jobs'))

@app.route('/employer/job/<int:job_id>/delete', methods=['POST'])
@employer_required
def employer_delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    # Ensure job belongs to this employer
    if job.company_id != company.id:
        abort(403)
    
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('employer_jobs'))

# Applications
@app.route('/employer/applications')
@employer_required
def employer_applications():
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if not company:
        flash('Please set up your company profile first.', 'info')
        return redirect(url_for('employer_company_profile'))
    
    status_filter = request.args.get('status', '')
    
    # Get all applications for this employer's jobs
    applications_query = db.session.query(
        JobApplication, Job, User
    ).join(
        Job, JobApplication.job_id == Job.id
    ).join(
        User, JobApplication.user_id == User.id
    ).filter(
        Job.company_id == company.id
    )
    
    if status_filter:
        applications_query = applications_query.filter(JobApplication.status == status_filter)
    
    applications = applications_query.order_by(JobApplication.applied_date.desc()).all()
    
    return render_template('employer/applications.html', 
                           applications=applications, 
                           company=company,
                           status_filter=status_filter)

@app.route('/employer/application/<int:application_id>/update', methods=['POST'])
@employer_required
def employer_update_application(application_id):
    application = JobApplication.query.get_or_404(application_id)
    job = Job.query.get(application.job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    # Ensure application belongs to this employer's job
    if job.company_id != company.id:
        abort(403)
    
    new_status = request.form.get('status')
    
    if new_status in ['applied', 'reviewed', 'shortlisted', 'rejected', 'hired']:
        application.status = new_status
        application.last_updated = datetime.utcnow()
        db.session.commit()
        flash('Application status updated successfully!', 'success')
    else:
        flash('Invalid status provided.', 'danger')
    
    return redirect(url_for('employer_applications'))

@app.route('/employer/application/<int:application_id>/view')
@employer_required
def employer_view_application(application_id):
    application = JobApplication.query.get_or_404(application_id)
    job = Job.query.get(application.job_id)
    company = Company.query.filter_by(user_id=current_user.id).first()
    applicant = User.query.get(application.user_id)
    
    # Ensure application belongs to this employer's job
    if job.company_id != company.id:
        abort(403)
    
    return render_template('employer/view_application.html',
                           application=application,
                           job=job,
                           applicant=applicant,
                           company=company)

# Helper functions
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

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
