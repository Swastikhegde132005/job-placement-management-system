import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from app.core.database import engine, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.entities import User, UserRole, StudentProfile, Company, Job

async def seed_database():
    print("Seeding database with initial placement data...")
    async with AsyncSessionLocal() as db:
        # 1. Verify if already seeded
        admin_check = await db.execute(select(User).where(User.email == "admin@campus.edu"))
        if admin_check.scalar_one_or_none():
            print("Database already contains seed data. Skipping.")
            return

        # 2. Create Users
        admin = User(
            email="admin@campus.edu",
            hashed_password=get_password_hash("Admin123!"),
            role=UserRole.ADMIN
        )
        recruiter = User(
            email="recruiter@google.com",
            hashed_password=get_password_hash("Recruiter123!"),
            role=UserRole.RECRUITER
        )
        student_eligible = User(
            email="arun.eligible@campus.edu",
            hashed_password=get_password_hash("Student123!"),
            role=UserRole.STUDENT
        )
        student_ineligible = User(
            email="rahul.backlog@campus.edu",
            hashed_password=get_password_hash("Student123!"),
            role=UserRole.STUDENT
        )
        db.add_all([admin, recruiter, student_eligible, student_ineligible])
        await db.commit()

        # 3. Create Student Profiles
        profile_eligible = StudentProfile(
            user_id=student_eligible.id,
            full_name="Arun Kumar",
            department="Computer Science & Engineering",
            cgpa=Decimal("8.85"),
            tenth_pct=Decimal("92.5"),
            twelfth_pct=Decimal("89.0"),
            active_backlogs=0,
            skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Algorithms"],
            resume_url="https://example.com/resumes/arun_kumar.pdf"
        )
        profile_ineligible = StudentProfile(
            user_id=student_ineligible.id,
            full_name="Rahul Verma",
            department="Information Technology",
            cgpa=Decimal("6.40"),
            tenth_pct=Decimal("74.0"),
            twelfth_pct=Decimal("68.5"),
            active_backlogs=2,
            skills=["HTML", "CSS", "JavaScript"],
            resume_url="https://example.com/resumes/rahul_verma.pdf"
        )
        db.add_all([profile_eligible, profile_ineligible])

        # 4. Create Companies
        company_google = Company(
            name="Google",
            website="https://careers.google.com",
            created_by=recruiter.id
        )
        company_amazon = Company(
            name="Amazon",
            website="https://amazon.jobs",
            created_by=recruiter.id
        )
        db.add_all([company_google, company_amazon])
        await db.commit()

        # 5. Create Job Openings
        deadline_date = datetime.now(timezone.utc) + timedelta(days=30)

        job_sde = Job(
            company_id=company_google.id,
            title="Software Development Engineer I",
            description="Build scalable distributed systems using Python and cloud technologies.",
            min_cgpa=Decimal("8.0"),
            min_tenth_pct=Decimal("80.0"),
            min_twelfth_pct=Decimal("80.0"),
            max_backlogs=0,
            required_skills=["Python", "Algorithms", "PostgreSQL"],
            deadline=deadline_date,
            is_active=True
        )
        job_web = Job(
            company_id=company_amazon.id,
            title="Associate Cloud Support Engineer",
            description="Troubleshoot cloud infrastructure and automate internal processes.",
            min_cgpa=Decimal("6.0"),
            min_tenth_pct=Decimal("60.0"),
            min_twelfth_pct=Decimal("60.0"),
            max_backlogs=3,
            required_skills=["HTML", "JavaScript"],
            deadline=deadline_date,
            is_active=True
        )
        db.add_all([job_sde, job_web])
        await db.commit()

        print("Successfully seeded users, profiles, companies, and jobs!")

if __name__ == "__main__":
    asyncio.run(seed_database())
