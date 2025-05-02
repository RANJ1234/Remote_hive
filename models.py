from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Association table for job_skills
job_skills = db.Table('job_skills',
    db.Column('job_id', db.Integer, db.ForeignKey('job.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill.id'), primary_key=True)
)

# Association table for user_skills (linked to jobseeker_profile instead of user)
user_skills = db.Table('user_skills',
    db.Column('profile_id', db.Integer, db.ForeignKey('jobseeker_profile.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='jobseeker')  # 'admin', 'employer', 'jobseeker'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    profile = db.relationship('JobseekerProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    company = db.relationship('Company', backref='owner', uselist=False, cascade='all, delete-orphan')
    applications = db.relationship('JobApplication', backref='applicant', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_employer(self):
        return self.role == 'employer'
    
    def is_jobseeker(self):
        return self.role == 'jobseeker'
    
    def __repr__(self):
        return f'<User {self.username}>'

class JobseekerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    resume_path = db.Column(db.String(255), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    headline = db.Column(db.String(200), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    experience_years = db.Column(db.Integer, default=0)
    current_salary = db.Column(db.Integer, nullable=True)
    expected_salary = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    remote_preference = db.Column(db.String(50), nullable=True)  # 'remote', 'hybrid', 'on-site'
    skills = db.relationship('Skill', secondary=user_skills, backref=db.backref('users', lazy='dynamic'))
    
    def __repr__(self):
        return f'<JobseekerProfile {self.full_name}>'

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    logo_path = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    company_size = db.Column(db.String(50), nullable=True)
    founded_year = db.Column(db.Integer, nullable=True)
    headquarters = db.Column(db.String(100), nullable=True)
    company_type = db.Column(db.String(50), nullable=True)  # 'MNC', 'Startup', 'Product', etc.
    is_featured = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = db.relationship('Job', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('CompanyReview', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Company {self.name}>'

class CompanyReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(100), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    pros = db.Column(db.Text, nullable=True)
    cons = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('reviews', lazy='dynamic'))
    
    def __repr__(self):
        return f'<CompanyReview {self.title}>'

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    is_remote = db.Column(db.Boolean, default=False)
    job_type = db.Column(db.String(50), nullable=False)  # 'Full-time', 'Part-time', 'Contract', etc.
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=True)
    salary_min = db.Column(db.Integer, nullable=True)
    salary_max = db.Column(db.Integer, nullable=True)
    experience_required = db.Column(db.String(50), nullable=True)  # '0-1 years', '1-3 years', etc.
    education_required = db.Column(db.String(100), nullable=True)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    views_count = db.Column(db.Integer, default=0)
    applications_count = db.Column(db.Integer, default=0)
    
    # Relationships
    skills = db.relationship('Skill', secondary=job_skills, backref=db.backref('jobs', lazy='dynamic'))
    applications = db.relationship('JobApplication', backref='job', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Job {self.title}>'

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resume_path = db.Column(db.String(255), nullable=True)
    cover_letter = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='applied')  # 'applied', 'reviewed', 'shortlisted', 'rejected', 'hired'
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<JobApplication {self.id}>'

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    def __repr__(self):
        return f'<Skill {self.name}>'

class CompanyCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    active_companies_count = db.Column(db.Integer, default=0)
    
    # Relationships
    company_categories = db.relationship('CompanyCategoryAssociation', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CompanyCategory {self.name}>'

class CompanyCategoryAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('company_category.id'), nullable=False)
    
    # Relationship
    company = db.relationship('Company', backref=db.backref('categories', lazy='dynamic'))
