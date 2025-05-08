import os
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, send_from_directory, session
from auth import login_required
from werkzeug.utils import secure_filename

from app import app
from models import JobseekerProfile, Job, JobApplication, Company, Skill
from forms import JobseekerProfileForm, JobApplicationForm

# Create jobseeker blueprint
jobseeker_bp = Blueprint('jobseeker', __name__, url_prefix='/jobseeker', template_folder='templates')

# Jobseeker access decorator - MODIFIED to allow all users to access jobseeker features
def jobseeker_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        # Allow access regardless of user role
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Dashboard
@jobseeker_bp.route('/dashboard')
@jobseeker_required
def jobseeker_dashboard():
    user_id = session.get('user_id')
    profile = JobseekerProfile.objects(user=user_id).first()

    # Get applied jobs
    applications = JobApplication.objects(user=user_id).order_by('-applied_date')

    # Get recommended jobs (based on user skills if they exist)
    recommended_jobs = []
    # Get user from database to access skills
    from models import User
    user = User.objects(id=user_id).first()
    if user and hasattr(user, 'skills') and user.skills:
        user_skill_ids = [skill.id for skill in user.skills]

        # Get jobs matching user skills
        # This is a simplified approach - in a real app, you'd use a more sophisticated algorithm
        jobs_with_skills = Job.objects(skills__in=user_skill_ids, is_active=True).limit(5)
        recommended_jobs = list(jobs_with_skills)

    # If not enough recommended jobs, fill with recent jobs
    if len(recommended_jobs) < 5:
        # Exclude jobs already in recommended_jobs
        existing_job_ids = [job.id for job in recommended_jobs]
        recent_jobs = Job.objects(id__nin=existing_job_ids, is_active=True).order_by('-posted_date').limit(5-len(recommended_jobs))
        recommended_jobs.extend(recent_jobs)

    return render_template('jobseeker/dashboard.html',
                          profile=profile,
                          applications=applications,
                          recommended_jobs=recommended_jobs)

# Profile management
@jobseeker_bp.route('/profile', methods=['GET', 'POST'])
@jobseeker_required
def jobseeker_profile():
    user_id = session.get('user_id')
    profile = JobseekerProfile.objects(user=user_id).first()

    if not profile:
        profile = JobseekerProfile(user=user_id)
        profile.save()

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

        profile.save()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('jobseeker_dashboard'))

    # Get all skills for the form
    all_skills = Skill.objects.order_by('name')

    return render_template('jobseeker/profile.html', form=form, profile=profile, all_skills=all_skills)

@jobseeker_bp.route('/skills', methods=['GET', 'POST'])
@jobseeker_required
def jobseeker_skills():
    user_id = session.get('user_id')
    profile = JobseekerProfile.objects(user=user_id).first()

    if not profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('jobseeker_profile'))

    if request.method == 'POST':
        # Get user from database
        from models import User
        user = User.objects(id=user_id).first()
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('jobseeker_dashboard'))

        # Clear existing skills
        user.skills = []

        # Get selected skill IDs from form
        skill_ids = request.form.getlist('skills')

        # Add skills to user
        for skill_id in skill_ids:
            skill = Skill.objects(id=skill_id).first()
            if skill:
                user.skills.append(skill)

        # Handle new skill creation
        new_skill_name = request.form.get('new_skill', '').strip()
        if new_skill_name:
            # Check if skill already exists
            existing_skill = Skill.objects(name__iexact=new_skill_name).first()
            if existing_skill:
                if existing_skill not in user.skills:
                    user.skills.append(existing_skill)
            else:
                new_skill = Skill(name=new_skill_name)
                new_skill.save()
                user.skills.append(new_skill)

        user.save()
        flash('Skills updated successfully!', 'success')
        return redirect(url_for('jobseeker_dashboard'))

    # Get all skills for the form
    all_skills = Skill.objects.order_by('name')
    # Get user skills
    from models import User
    user = User.objects(id=user_id).first()
    user_skill_ids = []
    if user and hasattr(user, 'skills') and user.skills:
        user_skill_ids = [skill.id for skill in user.skills]

    return render_template('jobseeker/skills.html',
                           profile=profile,
                           all_skills=all_skills,
                           user_skill_ids=user_skill_ids)

# Job applications
@jobseeker_bp.route('/apply/<job_id>', methods=['GET', 'POST'])
@jobseeker_required
def apply_for_job(job_id):
    job = Job.objects(id=job_id).first()
    if not job:
        abort(404)

    # Check if job is active
    if not job.is_active:
        flash('This job is no longer active.', 'warning')
        return redirect(url_for('job_details', job_id=job.id))

    # Check if user already applied
    user_id = session.get('user_id')
    existing_application = JobApplication.objects(job=job, user=user_id).first()

    if existing_application:
        flash('You have already applied for this job.', 'info')
        return redirect(url_for('job_details', job_id=job.id))

    form = JobApplicationForm()

    if form.validate_on_submit():
        # Get profile for resume
        profile = JobseekerProfile.objects(user=user_id).first()
        resume_path = profile.resume_path if profile else None

        # Handle resume upload if provided
        if form.resume.data:
            resume_path = save_file(form.resume.data, 'resumes')

        if not resume_path:
            flash('Please upload a resume or update your profile with a resume.', 'warning')
            return render_template('jobseeker/apply.html', form=form, job=job)

        application = JobApplication(
            job=job,
            user=user_id,
            resume_path=resume_path,
            cover_letter=form.cover_letter.data
        )

        application.save()

        # Update application count on job
        job.applications_count += 1
        job.save()

        flash('Application submitted successfully!', 'success')
        return redirect(url_for('jobseeker_applications'))

    return render_template('jobseeker/apply.html', form=form, job=job)

@jobseeker_bp.route('/applications')
@jobseeker_required
def jobseeker_applications():
    user_id = session.get('user_id')
    applications = JobApplication.objects(user=user_id).order_by('-applied_date')

    # Create a list of tuples with application, job, and company
    application_data = []
    for app in applications:
        application_data.append((app, app.job, app.job.company))

    return render_template('jobseeker/applications.html', applications=application_data)

@jobseeker_bp.route('/application/<application_id>/withdraw', methods=['POST'])
@jobseeker_required
def withdraw_application(application_id):
    application = JobApplication.objects(id=application_id).first()
    if not application:
        abort(404)

    # Ensure application belongs to this user
    user_id = session.get('user_id')
    if str(application.user.id) != user_id:
        abort(403)

    # Only allow withdrawal if application is in 'applied' or 'reviewed' state
    if application.status in ['applied', 'reviewed']:
        job = application.job
        job.applications_count -= 1
        job.save()

        application.delete()
        flash('Application withdrawn successfully.', 'success')
    else:
        flash('Cannot withdraw application in its current state.', 'warning')

    return redirect(url_for('jobseeker_applications'))

# Saved Jobs
@jobseeker_bp.route('/saved-jobs')
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
