import os
import logging
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, jsonify, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from bson import ObjectId
from app import app
from models import User, Job, Company, JobseekerProfile, JobApplication, CompanyReview, CompanyCategory, CompanyCategoryAssociation
from forms import LoginForm, RegisterForm, SearchForm, JobApplicationForm, CompanyReviewForm

# Helper functions
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def iter_pages(current_page, total_pages, left_edge=2, right_edge=2, left_current=2, right_current=2):
    """
    Implements SQLAlchemy's Pagination.iter_pages method for MongoDB pagination
    """
    last = 0
    for num in range(1, total_pages + 1):
        if (num <= left_edge or
            (num > current_page - left_current - 1 and
             num < current_page + right_current) or
            num > total_pages - right_edge):
            if last + 1 != num:
                yield None
            yield num
            last = num

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
    featured_companies = Company.objects(is_featured=True).limit(12)
    recent_jobs = Job.objects(is_active=True).order_by('-posted_date').limit(10)
    company_categories = CompanyCategory.objects.all()

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
        user = User.objects(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.now(timezone.utc)
            user.save()

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
        user.save()

        # Create profile based on role
        if user.is_jobseeker():
            profile = JobseekerProfile(user=user)
            profile.save()

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

    # Start with all active jobs
    jobs_filter = {'is_active': True}

    # Add filters based on search parameters
    if query:
        jobs_filter['title__icontains'] = query

    if location:
        jobs_filter['location__icontains'] = location

    if job_type:
        jobs_filter['job_type'] = job_type

    if remote == 'true':
        jobs_filter['is_remote'] = True

    # Execute the query
    jobs = Job.objects(**jobs_filter).order_by('-posted_date')

    search_form = SearchForm()
    search_form.query.data = query
    search_form.location.data = location

    return render_template('job_listing.html', jobs=jobs, search_form=search_form)

@app.route('/jobs')
def jobs():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    skip = (page - 1) * per_page

    jobs = Job.objects(is_active=True).order_by('-posted_date').skip(skip).limit(per_page)
    total_jobs = Job.objects(is_active=True).count()

    # Create a simple pagination object
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_jobs,
        'pages': (total_jobs + per_page - 1) // per_page,  # Ceiling division
        'has_prev': page > 1,
        'has_next': page * per_page < total_jobs
    }

    search_form = SearchForm()
    return render_template('job_listing.html', jobs=jobs, pagination=pagination, search_form=search_form)

@app.route('/job-feed')
def job_feed():
    """
    LinkedIn-style job feed with personalized recommendations and advanced filtering.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page

    # Start with all active jobs
    jobs_filter = {'is_active': True}

    # Apply filters from query parameters
    job_type = request.args.get('job_type')
    experience = request.args.get('experience')
    remote = request.args.get('remote')
    salary_min = request.args.get('salary_min')
    salary_max = request.args.get('salary_max')

    if job_type:
        jobs_filter['job_type'] = job_type

    if experience:
        jobs_filter['experience_required'] = experience

    if remote:
        jobs_filter['is_remote'] = True

    if salary_min:
        jobs_filter['salary_max__gte'] = int(salary_min)

    if salary_max:
        jobs_filter['salary_min__lte'] = int(salary_max)

    # Get featured jobs (limited to 3)
    # For random selection in MongoDB, we can use aggregate with $sample
    pipeline = [
        {'$match': {'is_active': True}},
        {'$sample': {'size': 3}}
    ]
    featured_jobs = list(Job.objects.aggregate(pipeline))

    # Get companies with most jobs
    # This is a more complex query in MongoDB
    # We'll use a simpler approach for now
    companies = Company.objects.all()
    company_job_counts = []
    for company in companies:
        job_count = Job.objects(company=company).count()
        if job_count > 0:
            company_job_counts.append((company, job_count))

    # Sort by job count and take top 5
    top_companies = sorted(company_job_counts, key=lambda x: x[1], reverse=True)[:5]

    # Order by specified sort parameter
    sort = request.args.get('sort', 'newest')
    if sort == 'newest':
        sort_field = '-posted_date'
    elif sort == 'oldest':
        sort_field = '+posted_date'
    elif sort == 'salary_high':
        sort_field = '-salary_max'
    elif sort == 'salary_low':
        sort_field = '+salary_min'
    else:
        sort_field = '-posted_date'

    # Get jobs with pagination
    jobs = Job.objects(**jobs_filter).order_by(sort_field).skip(skip).limit(per_page)
    total_jobs = Job.objects(**jobs_filter).count()

    # Create a simple pagination object
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_jobs,
        'pages': (total_jobs + per_page - 1) // per_page,
        'has_prev': page > 1,
        'has_next': page * per_page < total_jobs
    }

    # Get all categories for filter
    categories = CompanyCategory.objects.all()

    search_form = SearchForm()

    return render_template(
        'job_feed.html',
        jobs=jobs,
        pagination=pagination,
        featured_jobs=featured_jobs,
        top_companies=top_companies,
        categories=categories,
        search_form=search_form
    )

@app.route('/job/<job_id>')
def job_details(job_id):
    try:
        # Try to convert job_id to ObjectId
        from bson import ObjectId
        if ObjectId.is_valid(job_id):
            job = Job.objects(id=ObjectId(job_id)).first()
        else:
            job = None

        if not job:
            abort(404)

        # Increment view count
        job.views_count += 1
        job.save()
    except Exception as e:
        print(f"Error in job_details: {e}")
        abort(404)

    similar_jobs = Job.objects(
        company=job.company,
        id__ne=job.id,
        is_active=True
    ).limit(3)

    application_form = None
    has_applied = False

    if current_user.is_authenticated and current_user.is_jobseeker():
        application_form = JobApplicationForm()
        has_applied = JobApplication.objects(
            job=job,
            user=current_user
        ).first() is not None

    return render_template('job_details.html',
                           job=job,
                           similar_jobs=similar_jobs,
                           application_form=application_form,
                           has_applied=has_applied)

@app.route('/companies')
def companies():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    category_id = request.args.get('category_id')

    if category_id:
        # Find the category
        category = CompanyCategory.objects(id=category_id).first()
        if not category:
            abort(404)

        # Find associations for this category
        associations = CompanyCategoryAssociation.objects(category=category)

        # Get company IDs from associations
        company_ids = [assoc.company.id for assoc in associations]

        # Get companies with these IDs
        companies_query = Company.objects(id__in=company_ids)
        total_companies = companies_query.count()
        companies_list = companies_query.skip((page-1)*per_page).limit(per_page)
    else:
        companies_query = Company.objects
        total_companies = companies_query.count()
        companies_list = companies_query.skip((page-1)*per_page).limit(per_page)

    # Create a pagination object similar to SQLAlchemy's
    class Pagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page  # Ceiling division
            self.has_prev = page > 1
            self.has_next = page * per_page < total
            self.prev_num = page - 1 if page > 1 else None
            self.next_num = page + 1 if page * per_page < total else None

        def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=2):
            return iter_pages(
                self.page, self.pages,
                left_edge, right_edge, left_current, right_current
            )

    companies = Pagination(
        items=companies_list,
        page=page,
        per_page=per_page,
        total=total_companies
    )

    categories = CompanyCategory.objects.all()

    return render_template('company_listing.html',
                           companies=companies,
                           categories=categories,
                           selected_category=category_id)

@app.route('/company/<company_id>')
def company_details(company_id):
    try:
        # Try to convert company_id to ObjectId
        from bson import ObjectId
        if ObjectId.is_valid(company_id):
            company = Company.objects(id=ObjectId(company_id)).first()
        else:
            company = None

        if not company:
            abort(404)
        active_jobs = Job.objects(company=company, is_active=True)
        reviews = CompanyReview.objects(company=company).order_by('-created_at')
    except Exception as e:
        print(f"Error in company_details: {e}")
        abort(404)

    review_form = None
    if current_user.is_authenticated and current_user.is_jobseeker():
        review_form = CompanyReviewForm()

    return render_template('company_details.html',
                           company=company,
                           active_jobs=active_jobs,
                           reviews=reviews,
                           review_form=review_form)

@app.route('/company/<company_id>/review', methods=['POST'])
@login_required
def submit_company_review(company_id):
    if not current_user.is_jobseeker():
        flash('Only job seekers can submit reviews.', 'warning')
        return redirect(url_for('company_details', company_id=company_id))

    try:
        # Try to convert company_id to ObjectId
        from bson import ObjectId
        if ObjectId.is_valid(company_id):
            company = Company.objects(id=ObjectId(company_id)).first()
        else:
            company = None

        if not company:
            abort(404)
        form = CompanyReviewForm()
    except Exception as e:
        print(f"Error in submit_company_review: {e}")
        abort(404)

    if form.validate_on_submit():
        # Check if user already submitted a review
        existing_review = CompanyReview.objects(
            company=company,
            user=current_user
        ).first()

        if existing_review:
            flash('You have already submitted a review for this company.', 'warning')
        else:
            review = CompanyReview(
                company=company,
                user=current_user,
                rating=form.rating.data,
                title=form.title.data,
                review_text=form.review_text.data,
                pros=form.pros.data,
                cons=form.cons.data
            )
            review.save()

            # Update company rating
            reviews = CompanyReview.objects(company=company)
            total_rating = sum(review.rating for review in reviews) + form.rating.data
            company.review_count += 1
            company.rating = total_rating / company.review_count
            company.save()

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
