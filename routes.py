import os
import logging
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Job, Company, JobseekerProfile, JobApplication, CompanyReview, CompanyCategory, CompanyCategoryAssociation
from forms import LoginForm, RegisterForm, SearchForm, JobApplicationForm, CompanyReviewForm

# Helper functions
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

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

# Basic routes
@app.route('/')
def index():
    featured_companies = Company.query.filter_by(is_featured=True).limit(12).all()
    recent_jobs = Job.query.filter_by(is_active=True).order_by(Job.posted_date.desc()).limit(10).all()
    company_categories = CompanyCategory.query.all()
    
    search_form = SearchForm()
    return render_template('index.html', 
                           featured_companies=featured_companies,
                           recent_jobs=recent_jobs,
                           company_categories=company_categories,
                           search_form=search_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if user.is_admin():
                return redirect(next_page or url_for('admin_dashboard'))
            elif user.is_employer():
                return redirect(next_page or url_for('employer_dashboard'))
            else:
                return redirect(next_page or url_for('jobseeker_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.flush()  # Get user ID before committing
        
        # Create profile based on role
        if user.is_jobseeker():
            profile = JobseekerProfile(user_id=user.id)
            db.session.add(profile)
        
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('query', '')
    location = request.args.get('location', '')
    job_type = request.args.get('job_type', '')
    remote = request.args.get('remote', '')
    
    jobs_query = Job.query.filter_by(is_active=True)
    
    if query:
        jobs_query = jobs_query.filter(Job.title.ilike(f'%{query}%'))
    
    if location:
        jobs_query = jobs_query.filter(Job.location.ilike(f'%{location}%'))
    
    if job_type:
        jobs_query = jobs_query.filter(Job.job_type == job_type)
    
    if remote == 'true':
        jobs_query = jobs_query.filter(Job.is_remote == True)
    
    jobs = jobs_query.order_by(Job.posted_date.desc()).all()
    
    search_form = SearchForm()
    search_form.query.data = query
    search_form.location.data = location
    
    return render_template('job_listing.html', jobs=jobs, search_form=search_form)

@app.route('/jobs')
def jobs():
    page = request.args.get('page', 1, type=int)
    jobs = Job.query.filter_by(is_active=True).order_by(Job.posted_date.desc()).paginate(page=page, per_page=20)
    search_form = SearchForm()
    return render_template('job_listing.html', jobs=jobs, search_form=search_form)

@app.route('/job/<int:job_id>')
def job_details(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Increment view count
    job.views_count += 1
    db.session.commit()
    
    similar_jobs = Job.query.filter(
        Job.company_id == job.company_id,
        Job.id != job.id,
        Job.is_active == True
    ).limit(3).all()
    
    application_form = None
    has_applied = False
    
    if current_user.is_authenticated and current_user.is_jobseeker():
        application_form = JobApplicationForm()
        has_applied = JobApplication.query.filter_by(
            job_id=job.id, 
            user_id=current_user.id
        ).first() is not None
    
    return render_template('job_details.html', 
                           job=job, 
                           similar_jobs=similar_jobs,
                           application_form=application_form,
                           has_applied=has_applied)

@app.route('/companies')
def companies():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    
    companies_query = Company.query
    
    if category_id:
        companies_query = companies_query.join(
            CompanyCategoryAssociation, 
            Company.id == CompanyCategoryAssociation.company_id
        ).filter(CompanyCategoryAssociation.category_id == category_id)
    
    companies = companies_query.paginate(page=page, per_page=20)
    categories = CompanyCategory.query.all()
    
    return render_template('company_listing.html', 
                           companies=companies, 
                           categories=categories,
                           selected_category=category_id)

@app.route('/company/<int:company_id>')
def company_details(company_id):
    company = Company.query.get_or_404(company_id)
    active_jobs = Job.query.filter_by(company_id=company.id, is_active=True).all()
    reviews = CompanyReview.query.filter_by(company_id=company.id).order_by(CompanyReview.created_at.desc()).all()
    
    review_form = None
    if current_user.is_authenticated and current_user.is_jobseeker():
        review_form = CompanyReviewForm()
    
    return render_template('company_details.html', 
                           company=company, 
                           active_jobs=active_jobs,
                           reviews=reviews,
                           review_form=review_form)

@app.route('/company/<int:company_id>/review', methods=['POST'])
@login_required
def submit_company_review(company_id):
    if not current_user.is_jobseeker():
        flash('Only job seekers can submit reviews.', 'warning')
        return redirect(url_for('company_details', company_id=company_id))
    
    company = Company.query.get_or_404(company_id)
    form = CompanyReviewForm()
    
    if form.validate_on_submit():
        # Check if user already submitted a review
        existing_review = CompanyReview.query.filter_by(
            company_id=company.id, 
            user_id=current_user.id
        ).first()
        
        if existing_review:
            flash('You have already submitted a review for this company.', 'warning')
        else:
            review = CompanyReview(
                company_id=company.id,
                user_id=current_user.id,
                rating=form.rating.data,
                title=form.title.data,
                review_text=form.review_text.data,
                pros=form.pros.data,
                cons=form.cons.data
            )
            
            db.session.add(review)
            
            # Update company rating
            reviews = CompanyReview.query.filter_by(company_id=company.id).all()
            total_rating = sum(review.rating for review in reviews) + form.rating.data
            company.review_count += 1
            company.rating = total_rating / company.review_count
            
            db.session.commit()
            flash('Your review has been submitted. Thank you!', 'success')
    
    return redirect(url_for('company_details', company_id=company_id))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.context_processor
def utility_processor():
    def format_date(date):
        if not date:
            return ""
        return date.strftime("%B %d, %Y")
    
    def time_since(date):
        if not date:
            return ""
        
        now = datetime.utcnow()
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
