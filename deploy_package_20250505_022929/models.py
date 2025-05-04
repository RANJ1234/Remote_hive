from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine import Document, StringField, EmailField, DateTimeField, BooleanField, ReferenceField, ListField, IntField, FloatField, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField, CASCADE

class Skill(Document):
    name = StringField(required=True, unique=True)
    category = StringField()

    meta = {'collection': 'skills'}

    def __str__(self):
        return self.name

class User(Document, UserMixin):
    username = StringField(max_length=64, required=True, unique=True)
    email = EmailField(required=True, unique=True)
    password_hash = StringField(required=True)
    role = StringField(required=True, default='jobseeker')  # 'admin', 'employer', 'jobseeker'
    created_at = DateTimeField(default=datetime.utcnow)
    last_login = DateTimeField()
    is_active = BooleanField(default=True)
    skills = ListField(ReferenceField(Skill))

    meta = {'collection': 'users'}

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

    def get_id(self):
        return str(self.id)

    def __str__(self):
        return self.username

class JobseekerProfile(Document):
    user = ReferenceField(User, required=True, unique=True)
    full_name = StringField(max_length=100)
    phone = StringField(max_length=20)
    resume_path = StringField(max_length=255)
    profile_picture = StringField(max_length=255)
    headline = StringField(max_length=200)
    summary = StringField()
    experience_years = IntField(default=0)
    current_salary = IntField()
    expected_salary = IntField()
    location = StringField(max_length=100)
    remote_preference = StringField(max_length=50)  # 'remote', 'hybrid', 'on-site'

    meta = {'collection': 'jobseeker_profiles'}

    def __str__(self):
        return f'{self.full_name}'

class Company(Document):
    user = ReferenceField(User, required=True, unique=True)
    name = StringField(max_length=100, required=True)
    logo_path = StringField(max_length=255)
    website = StringField(max_length=255)
    description = StringField()
    industry = StringField(max_length=100)
    company_size = StringField(max_length=50)
    founded_year = IntField()
    headquarters = StringField(max_length=100)
    company_type = StringField(max_length=50)  # 'MNC', 'Startup', 'Product', etc.
    is_featured = BooleanField(default=False)
    rating = FloatField(default=0.0)
    review_count = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'companies'}

    def __str__(self):
        return self.name

class CompanyReview(Document):
    company = ReferenceField(Company, required=True)
    user = ReferenceField(User, required=True)
    rating = IntField(required=True, min_value=1, max_value=5)  # 1-5
    title = StringField(max_length=100, required=True)
    review_text = StringField(required=True)
    pros = StringField()
    cons = StringField()
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'company_reviews'}

    def __str__(self):
        return self.title

class Job(Document):
    company = ReferenceField(Company, required=True)
    title = StringField(max_length=100, required=True)
    location = StringField(max_length=100)
    is_remote = BooleanField(default=False)
    job_type = StringField(max_length=50, required=True)  # 'Full-time', 'Part-time', 'Contract', etc.
    description = StringField(required=True)
    requirements = StringField()
    salary_min = IntField()
    salary_max = IntField()
    experience_required = StringField(max_length=50)  # '0-1 years', '1-3 years', etc.
    education_required = StringField(max_length=100)
    posted_date = DateTimeField(default=datetime.utcnow)
    deadline = DateTimeField()
    is_active = BooleanField(default=True)
    views_count = IntField(default=0)
    applications_count = IntField(default=0)
    skills = ListField(ReferenceField(Skill))

    meta = {'collection': 'jobs'}

    def __str__(self):
        return self.title

class JobApplication(Document):
    job = ReferenceField(Job, required=True)
    user = ReferenceField(User, required=True)
    resume_path = StringField(max_length=255)
    cover_letter = StringField()
    status = StringField(max_length=20, default='applied')  # 'applied', 'reviewed', 'shortlisted', 'rejected', 'hired'
    applied_date = DateTimeField(default=datetime.utcnow)
    last_updated = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'job_applications'}

    def __str__(self):
        return f'Application for {self.job.title} by {self.user.username}'

class CompanyCategory(Document):
    name = StringField(max_length=50, required=True, unique=True)
    description = StringField()
    active_companies_count = IntField(default=0)

    meta = {'collection': 'company_categories'}

    def __str__(self):
        return self.name

class CompanyCategoryAssociation(Document):
    company = ReferenceField(Company, required=True)
    category = ReferenceField(CompanyCategory, required=True)

    meta = {
        'collection': 'company_category_associations',
        'indexes': [
            {'fields': ['company', 'category'], 'unique': True}
        ]
    }

    def __str__(self):
        return f'{self.company.name} - {self.category.name}'
