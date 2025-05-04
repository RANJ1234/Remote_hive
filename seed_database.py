"""
Seed database script for Remote Hive

This script populates the database with initial data for testing and development.
"""

import datetime
from app import app
from models import User, JobseekerProfile, Company, CompanyCategory, CompanyCategoryAssociation, Job, Skill

def seed_database():
    """Seed the database with initial data."""
    print("Seeding database...")

    # Clear existing data
    User.objects.delete()
    JobseekerProfile.objects.delete()
    Company.objects.delete()
    CompanyCategory.objects.delete()
    CompanyCategoryAssociation.objects.delete()
    Job.objects.delete()
    Skill.objects.delete()

    # Create skills
    skills = [
        "Python", "JavaScript", "React", "Angular", "Vue.js", "Django", "Flask",
        "Node.js", "Express.js", "PostgreSQL", "MySQL", "MongoDB", "Redis",
        "AWS", "Docker", "Kubernetes", "CI/CD", "DevOps", "Linux", "Git",
        "HTML/CSS", "TypeScript", "Java", "C#", "PHP", "Ruby", "Go", "Swift",
        "UI/UX Design", "Product Management", "Agile", "Scrum", "Data Science",
        "Machine Learning", "AI", "Blockchain", "IoT", "Cloud Computing"
    ]

    skill_objects = []
    for skill_name in skills:
        skill = Skill(name=skill_name)
        skill.save()
        print(f"Created skill: {skill_name}")
        skill_objects.append(skill)

    # Create company categories
    categories = [
        {"name": "Technology", "description": "Software, hardware, and IT companies"},
        {"name": "Finance", "description": "Banks, investment firms, and financial services"},
        {"name": "Healthcare", "description": "Hospitals, clinics, and health tech"},
        {"name": "Education", "description": "Schools, universities, and e-learning platforms"},
        {"name": "E-commerce", "description": "Online retail and marketplace businesses"},
        {"name": "Entertainment", "description": "Media, gaming, and creative industries"}
    ]

    category_objects = []
    for cat_data in categories:
        category = CompanyCategory(
            name=cat_data["name"],
            description=cat_data["description"]
        )
        category.save()
        print(f"Created category: {cat_data['name']}")
        category_objects.append(category)

    # Create admin user
    admin = User(
        username="admin",
        email="admin@remotehive.com",
        role="admin",
        is_active=True
    )
    admin.set_password("admin123")
    admin.save()
    print("Created admin user")

    # Create employer user with company
    employer = User(
        username="employer1",
        email="employer@example.com",
        role="employer",
        is_active=True
    )
    employer.set_password("password123")
    employer.save()

    company = Company(
        user=employer,
        name="TechGrowth Solutions",
        website="https://techgrowth.example.com",
        description="TechGrowth Solutions is a leading software development company specializing in cloud solutions and digital transformation. We help businesses leverage technology to scale and innovate.",
        industry="Information Technology",
        company_size="51-200",
        founded_year=2010,
        headquarters="San Francisco, CA",
        company_type="Product",
        is_featured=True,
        rating=4.5,
        review_count=12
    )
    company.save()
    print("Created employer user with company")

    # Associate company with categories
    for category in category_objects[:2]:  # Technology and Finance
        association = CompanyCategoryAssociation(
            company=company,
            category=category
        )
        association.save()

    # Create jobs for this company
    job1 = Job(
        company=company,
        title="Senior Python Developer",
        location="San Francisco, CA",
        is_remote=True,
        job_type="Full-time",
        description="We're looking for a Senior Python Developer to join our growing team. You'll be responsible for designing, developing, and maintaining scalable Python applications.",
        requirements="- 5+ years of experience with Python\n- Experience with Django or Flask\n- Strong understanding of RESTful APIs\n- Knowledge of database systems",
        salary_min=120000,
        salary_max=160000,
        experience_required="5-10 years",
        education_required="Bachelor's degree in Computer Science or related field",
        posted_date=datetime.datetime.utcnow() - datetime.timedelta(days=5),
        deadline=datetime.datetime.utcnow() + datetime.timedelta(days=25),
        is_active=True,
        views_count=142,
        applications_count=15
    )
    job1.save()

    job2 = Job(
        company=company,
        title="Frontend React Developer",
        location="Remote",
        is_remote=True,
        job_type="Full-time",
        description="Join our frontend team and help build beautiful, responsive web applications using React. You'll collaborate with designers, backend developers, and product managers to create seamless user experiences.",
        requirements="- 3+ years of experience with React\n- Strong JavaScript skills\n- Experience with modern frontend tools\n- Understanding of UI/UX principles",
        salary_min=90000,
        salary_max=120000,
        experience_required="3-5 years",
        education_required="Bachelor's degree or equivalent experience",
        posted_date=datetime.datetime.utcnow() - datetime.timedelta(days=2),
        deadline=datetime.datetime.utcnow() + datetime.timedelta(days=28),
        is_active=True,
        views_count=87,
        applications_count=8
    )
    job2.save()
    print("Created jobs for the company")

    # Add skills to jobs
    python_skill = next((s for s in skill_objects if s.name == "Python"), None)
    django_skill = next((s for s in skill_objects if s.name == "Django"), None)
    flask_skill = next((s for s in skill_objects if s.name == "Flask"), None)

    if python_skill:
        job1.skills.append(python_skill)
    if django_skill:
        job1.skills.append(django_skill)
    if flask_skill:
        job1.skills.append(flask_skill)
    job1.save()

    react_skill = next((s for s in skill_objects if s.name == "React"), None)
    js_skill = next((s for s in skill_objects if s.name == "JavaScript"), None)
    typescript_skill = next((s for s in skill_objects if s.name == "TypeScript"), None)
    html_skill = next((s for s in skill_objects if s.name == "HTML/CSS"), None)

    if react_skill:
        job2.skills.append(react_skill)
    if js_skill:
        job2.skills.append(js_skill)
    if typescript_skill:
        job2.skills.append(typescript_skill)
    if html_skill:
        job2.skills.append(html_skill)
    job2.save()

    # Create jobseeker user with profile
    jobseeker = User(
        username="jobseeker1",
        email="jobseeker@example.com",
        role="jobseeker",
        is_active=True
    )
    jobseeker.set_password("password123")
    jobseeker.save()

    profile = JobseekerProfile(
        user=jobseeker,
        full_name="Alex Johnson",
        phone="+1 (555) 123-4567",
        headline="Full Stack Developer with React and Python Expertise",
        summary="Experienced full stack developer with a passion for creating elegant, efficient solutions. Specializing in React for frontend and Python (Django/Flask) for backend development.",
        experience_years=5,
        current_salary=95000,
        expected_salary=115000,
        location="Chicago, IL",
        remote_preference="remote"
    )
    profile.save()
    print("Created jobseeker user with profile")

    # Add skills to jobseeker
    for skill_name in ["Python", "JavaScript", "React", "Django", "Node.js", "PostgreSQL", "Git"]:
        skill = next((s for s in skill_objects if s.name == skill_name), None)
        if skill:
            jobseeker.skills.append(skill)
    jobseeker.save()

    print("Database seeding completed successfully!")

if __name__ == "__main__":
    with app.app_context():
        seed_database()