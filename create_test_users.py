from app import app
from models import User, JobseekerProfile, Company

def create_test_users():
    # Check if employer user exists
    employer_user = User.objects(email="employer@example.com").first()
    if not employer_user:
        # Create a test employer user
        employer_user = User(
            username="employer",
            email="employer@example.com",
            role="employer"
        )
        employer_user.set_password("password")
        employer_user.save()
        print(f"Created employer user: {employer_user.email} with password: password")
    else:
        print(f"Employer user already exists: {employer_user.email}")

    # Check if company exists
    company = Company.objects(user=employer_user).first()
    if not company:
        # Create a company for the employer
        company = Company(
            user=employer_user,
            name="Test Company",
            description="A test company for testing purposes",
            industry="Technology",
            company_size="1-10",
            founded_year=2023,
            headquarters="Test City",
            company_type="Startup"
        )
        company.save()
        print(f"Created company: {company.name}")
    else:
        print(f"Company already exists: {company.name}")

    # Check if jobseeker user exists
    jobseeker_user = User.objects(email="jobseeker@example.com").first()
    if not jobseeker_user:
        # Create a test jobseeker user
        jobseeker_user = User(
            username="jobseeker",
            email="jobseeker@example.com",
            role="jobseeker"
        )
        jobseeker_user.set_password("password")
        jobseeker_user.save()
        print(f"Created jobseeker user: {jobseeker_user.email} with password: password")
    else:
        print(f"Jobseeker user already exists: {jobseeker_user.email}")

    # Check if profile exists
    profile = JobseekerProfile.objects(user=jobseeker_user).first()
    if not profile:
        # Create a profile for the jobseeker
        profile = JobseekerProfile(
            user=jobseeker_user,
            full_name="Test Jobseeker",
            headline="Software Developer",
            summary="A test jobseeker for testing purposes",
            experience_years=5,
            location="Test City",
            remote_preference="remote"
        )
        profile.save()
        print(f"Created jobseeker profile for: {jobseeker_user.email}")
    else:
        print(f"Jobseeker profile already exists for: {jobseeker_user.email}")

    # Check if admin user exists
    admin_user = User.objects(email="admin@example.com").first() or User.objects(username="admin").first()
    if not admin_user:
        # Create an admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            role="admin"
        )
        admin_user.set_password("password")
        admin_user.save()
        print(f"Created admin user: {admin_user.email} with password: password")
    else:
        print(f"Admin user already exists: {admin_user.email}")

if __name__ == "__main__":
    with app.app_context():
        create_test_users()
