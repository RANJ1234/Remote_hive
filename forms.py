from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, IntegerField, FileField, BooleanField, DateField, MultipleFileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange, URL
from models import User
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Register as', choices=[('jobseeker', 'Job Seeker'), ('employer', 'Employer')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one or login.')

class JobseekerProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    headline = StringField('Professional Headline', validators=[Length(max=200)])
    summary = TextAreaField('Professional Summary')
    experience_years = IntegerField('Years of Experience', validators=[NumberRange(min=0, max=50)])
    current_salary = IntegerField('Current Salary (Annual)', validators=[Optional()])
    expected_salary = IntegerField('Expected Salary (Annual)', validators=[Optional()])
    location = StringField('Location', validators=[Length(max=100)])
    remote_preference = SelectField('Work Type Preference', 
                                    choices=[('remote', 'Remote'), ('hybrid', 'Hybrid'), ('on-site', 'On-Site')])
    resume = FileField('Upload Resume', validators=[FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents allowed!')])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Only JPG and PNG images allowed!')])
    submit = SubmitField('Save Profile')

class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    website = StringField('Website', validators=[URL(), Length(max=255)])
    description = TextAreaField('Company Description', validators=[DataRequired()])
    industry = StringField('Industry', validators=[DataRequired(), Length(max=100)])
    company_size = SelectField('Company Size', 
                              choices=[('1-10', '1-10 employees'), 
                                       ('11-50', '11-50 employees'),
                                       ('51-200', '51-200 employees'),
                                       ('201-500', '201-500 employees'),
                                       ('501-1000', '501-1000 employees'),
                                       ('1001-5000', '1001-5000 employees'),
                                       ('5001+', '5001+ employees')])
    founded_year = IntegerField('Founded Year', validators=[Optional(), NumberRange(min=1800, max=2030)])
    headquarters = StringField('Headquarters', validators=[Length(max=100)])
    company_type = SelectField('Company Type', 
                              choices=[('MNC', 'MNC'), 
                                       ('Startup', 'Startup'),
                                       ('Product', 'Product'),
                                       ('Service', 'Service'),
                                       ('Consulting', 'Consulting'),
                                       ('Government', 'Government'),
                                       ('Other', 'Other')])
    logo = FileField('Company Logo', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'svg'], 'Images only!')])
    submit = SubmitField('Save Company')

class JobPostForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired(), Length(max=100)])
    location = StringField('Location', validators=[Length(max=100)])
    is_remote = BooleanField('Remote Job')
    job_type = SelectField('Job Type', 
                          choices=[('Full-time', 'Full-time'), 
                                   ('Part-time', 'Part-time'),
                                   ('Contract', 'Contract'),
                                   ('Internship', 'Internship'),
                                   ('Freelance', 'Freelance')])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    requirements = TextAreaField('Requirements')
    salary_min = IntegerField('Minimum Salary', validators=[Optional()])
    salary_max = IntegerField('Maximum Salary', validators=[Optional()])
    experience_required = SelectField('Experience Required',
                                     choices=[('0-1 years', '0-1 years'),
                                              ('1-3 years', '1-3 years'),
                                              ('3-5 years', '3-5 years'),
                                              ('5-10 years', '5-10 years'),
                                              ('10+ years', '10+ years')])
    education_required = StringField('Education Required', validators=[Length(max=100)])
    deadline = DateField('Application Deadline', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Post Job')

class JobApplicationForm(FlaskForm):
    resume = FileField('Upload Resume', validators=[FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents allowed!')])
    cover_letter = TextAreaField('Cover Letter')
    submit = SubmitField('Apply Now')

class CompanyReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], coerce=int)
    title = StringField('Review Title', validators=[DataRequired(), Length(max=100)])
    review_text = TextAreaField('Your Review', validators=[DataRequired()])
    pros = TextAreaField('Pros')
    cons = TextAreaField('Cons')
    submit = SubmitField('Submit Review')

class SearchForm(FlaskForm):
    query = StringField('Search for jobs, companies, or keywords', validators=[DataRequired()])
    location = StringField('Location')
    submit = SubmitField('Search')

class AdminUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('employer', 'Employer'), ('jobseeker', 'Job Seeker')])
    is_active = BooleanField('Active')
    password = PasswordField('Password', validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    submit = SubmitField('Save User')

class AdminCompanyCategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description')
    submit = SubmitField('Save Category')
