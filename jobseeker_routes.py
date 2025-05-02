import os
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import app, db
from models import JobseekerProfile, Job, JobApplication, Company, Skill, user_skills, job_skills
from forms import JobseekerProfileForm, JobApplicationForm

# Jobseeker access decorator
def jobseeker_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_jobseeker():
            abort(403)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Dashboard
@app.route('/jobseeker/dashboard')
@jobseeker_required
def jobseeker_dashboard():
    profile = JobseekerProfile.query.filter_by(user_id=current_user.id).first()
    
    # Get applied jobs
    applications = JobApplication.query.filter_by(user_id=current_user.id).order_by(JobApplication.applied_date.desc()).all()
    
    # Get recommended jobs (based on user skills if they exist)
    recommended_jobs = []
    if current_user.skills:
        user_skill_ids = [skill.id for skill in current_user.skills]
        
        # Get jobs matching user skills, ordered by number of matching skills
        skill_matching_jobs = db.session.query(
            Job, db.func.count(job_skills.c.skill_id).label('matching_skills')
        ).join(
            job_skills, Job.id == job_skills.c.job_id
        ).filter(
            job_skills.c.skill_id.in_(user_skill_ids),
            Job.is_active == True
        ).group_by(
            Job
        ).order_by(
            db.desc('matching_skills')
        ).limit(5).all()
        
        recommended_jobs = [job for job, _ in skill_matching_jobs]
    
    # If not enough recommended jobs, fill with recent jobs
    if len(recommended_jobs) < 5:
        recent_jobs = Job.query.filter_by(is_active=True).order_by(Job.posted_date.desc()).limit(5-len(recommended_jobs)).all()
        recommended_jobs.extend(recent_jobs)
    
    return render_template('jobseeker/dashboard.html',
                          profile=profile,
                          applications=applications,
                          recommended_jobs=recommended_jobs)

# Profile management
@app.route('/jobseeker/profile', methods=['GET', 'POST'])
@jobseeker_required
def jobseeker_profile():
    profile = JobseekerProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        profile = JobseekerProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    form = JobseekerProfileForm(obj=profile)
    
    if form.validate_on_submit():
        profile.full_name = form.full_name.data
        profile.phone = form.phone.data
        profile.headline = form.headline.data
        profile.summary = form.summary.data
        profile.experience_years = form.experience_years.data
        profile.current_salary = form.current_salary.data
        profile.expected_salary = form.expected_salary.data
        profile.location = form.location.data
        profile.remote_preference = form.remote_preference.data
        
        # Handle resume upload
        if form.resume.data:
            resume_path = save_file(form.resume.data, 'resumes')
            if resume_path:
                # Delete old resume if exists
                if profile.resume_path:
                    old_resume_path = os.path.join(app.config['UPLOAD_FOLDER'], profile.resume_path)
                    if os.path.exists(old_resume_path):
                        os.remove(old_resume_path)
                profile.resume_path = resume_path
        
        # Handle profile picture upload
        if form.profile_picture.data:
            picture_path = save_file(form.profile_picture.data, 'profile_pictures')
            if picture_path:
                # Delete old picture if exists
                if profile.profile_picture:
                    old_picture_path = os.path.join(app.config['UPLOAD_FOLDER'], profile.profile_picture)
                    if os.path.exists(old_picture_path):
                        os.remove(old_picture_path)
                profile.profile_picture = picture_path
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('jobseeker_dashboard'))
    
    # Get all skills for the form
    all_skills = Skill.query.order_by(Skill.name).all()
    
    return render_template('jobseeker/profile.html', form=form, profile=profile, all_skills=all_skills)

@app.route('/jobseeker/skills', methods=['GET', 'POST'])
@jobseeker_required
def jobseeker_skills():
    profile = JobseekerProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('jobseeker_profile'))
    
    if request.method == 'POST':
        # Clear existing skills
        current_user.skills = []
        
        # Get selected skill IDs from form
        skill_ids = request.form.getlist('skills')
        
        # Add skills to user
        for skill_id in skill_ids:
            skill = Skill.query.get(skill_id)
            if skill:
                current_user.skills.append(skill)
        
        # Handle new skill creation
        new_skill_name = request.form.get('new_skill', '').strip()
        if new_skill_name:
            # Check if skill already exists
            existing_skill = Skill.query.filter(Skill.name.ilike(new_skill_name)).first()
            if existing_skill:
                if existing_skill not in current_user.skills:
                    current_user.skills.append(existing_skill)
            else:
                new_skill = Skill(name=new_skill_name)
                db.session.add(new_skill)
                db.session.flush()  # Get skill ID
                current_user.skills.append(new_skill)
        
        db.session.commit()
        flash('Skills updated successfully!', 'success')
        return redirect(url_for('jobseeker_dashboard'))
    
    # Get all skills for the form
    all_skills = Skill.query.order_by(Skill.name).all()
    user_skill_ids = [skill.id for skill in current_user.skills]
    
    return render_template('jobseeker/skills.html', 
                           profile=profile, 
                           all_skills=all_skills,
                           user_skill_ids=user_skill_ids)

# Job applications
@app.route('/jobseeker/apply/<int:job_id>', methods=['GET', 'POST'])
@jobseeker_required
def apply_for_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if job is active
    if not job.is_active:
        flash('This job is no longer active.', 'warning')
        return redirect(url_for('job_details', job_id=job.id))
    
    # Check if user already applied
    existing_application = JobApplication.query.filter_by(
        job_id=job.id, 
        user_id=current_user.id
    ).first()
    
    if existing_application:
        flash('You have already applied for this job.', 'info')
        return redirect(url_for('job_details', job_id=job.id))
    
    form = JobApplicationForm()
    
    if form.validate_on_submit():
        # Get profile for resume
        profile = JobseekerProfile.query.filter_by(user_id=current_user.id).first()
        resume_path = profile.resume_path if profile else None
        
        # Handle resume upload if provided
        if form.resume.data:
            resume_path = save_file(form.resume.data, 'resumes')
        
        if not resume_path:
            flash('Please upload a resume or update your profile with a resume.', 'warning')
            return render_template('jobseeker/apply.html', form=form, job=job)
        
        application = JobApplication(
            job_id=job.id,
            user_id=current_user.id,
            resume_path=resume_path,
            cover_letter=form.cover_letter.data
        )
        
        db.session.add(application)
        
        # Update application count on job
        job.applications_count += 1
        
        db.session.commit()
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('jobseeker_applications'))
    
    return render_template('jobseeker/apply.html', form=form, job=job)

@app.route('/jobseeker/applications')
@jobseeker_required
def jobseeker_applications():
    applications = db.session.query(
        JobApplication, Job, Company
    ).join(
        Job, JobApplication.job_id == Job.id
    ).join(
        Company, Job.company_id == Company.id
    ).filter(
        JobApplication.user_id == current_user.id
    ).order_by(
        JobApplication.applied_date.desc()
    ).all()
    
    return render_template('jobseeker/applications.html', applications=applications)

@app.route('/jobseeker/application/<int:application_id>/withdraw', methods=['POST'])
@jobseeker_required
def withdraw_application(application_id):
    application = JobApplication.query.get_or_404(application_id)
    
    # Ensure application belongs to this user
    if application.user_id != current_user.id:
        abort(403)
    
    # Only allow withdrawal if application is in 'applied' or 'reviewed' state
    if application.status in ['applied', 'reviewed']:
        job = Job.query.get(application.job_id)
        job.applications_count -= 1
        
        db.session.delete(application)
        db.session.commit()
        flash('Application withdrawn successfully.', 'success')
    else:
        flash('Cannot withdraw application in its current state.', 'warning')
    
    return redirect(url_for('jobseeker_applications'))

# Saved Jobs
@app.route('/jobseeker/saved-jobs')
@jobseeker_required
def saved_jobs():
    # This would require extending the model with a SavedJob table
    # For simplicity, we'll return a placeholder
    return render_template('jobseeker/saved_jobs.html')

# Helper functions
def save_file(file, folder):
    if file and allowed_file(file.filename, {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}):
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
