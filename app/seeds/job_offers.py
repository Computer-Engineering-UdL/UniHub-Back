import datetime
import random
import uuid
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from app.literals.job import JobCategory, JobType, JobWorkplace
from app.models import File, User
from app.models.file_association import FileAssociation
from app.models.job import JobApplication, JobOfferTableModel


def seed_job_offers(db: Session, users: List[User]) -> List[JobOfferTableModel]:
    """Create job offers with realistic data."""

    existing_jobs = db.query(JobOfferTableModel).first()
    if existing_jobs:
        jobs = db.query(JobOfferTableModel).limit(10).all()
        print(f"* Job offers already seeded ({len(jobs)} jobs)")
        return jobs

    print("Seeding job offers...")

    verified_users = [u for u in users if u.is_verified]
    if len(verified_users) < 2:
        print("ERROR: Not enough verified users found.")
        return []

    now = datetime.datetime.now(datetime.UTC)
    logos_path = Path(__file__).parent.parent / "static_photos" / "job-logos"

    jobs_data = [
        {
            "title": "Full-Stack Developer",
            "description": """We are seeking a talented Full-Stack Developer to join our growing tech team in Lleida.

Key Responsibilities:
• Develop and maintain web applications using modern frameworks
• Collaborate with UX/UI designers to implement responsive interfaces
• Write clean, maintainable, and efficient code
• Participate in code reviews and agile ceremonies

Requirements:
• Bachelor's degree in Computer Science or related field
• Proficiency in React, Node.js, and PostgreSQL
• Strong problem-solving skills
• Fluency in Spanish and English

We offer flexible working hours, professional development opportunities, and a dynamic work environment.""",
            "category": JobCategory.TECHNOLOGY,
            "job_type": JobType.FULL_TIME,
            "workplace_type": JobWorkplace.HYBRID,
            "location": "Lleida",
            "salary_min": 28000,
            "salary_max": 38000,
            "salary_period": "year",
            "company_name": "TechCat Solutions",
            "company_description": (
                "Leading software development company in Catalonia "
                "specializing in innovative digital solutions."
            ),
            "company_website": "https://techcat-solutions.example.com",
            "company_employee_count": "50-100",
            "user": verified_users[0],
            "logo_file": "techcat-solutions.jpg",
            "days_ago": 7,
        },
        {
            "title": "Marketing Intern",
            "description": """Exciting internship opportunity for marketing students!

Responsibilities:
• Assist in social media content creation and management
• Support email marketing campaigns
• Conduct market research and competitor analysis
• Help organize promotional events

Ideal Candidate:
• Currently enrolled in Marketing, Business, or Communications degree
• Creative mindset with strong communication skills
• Familiarity with social media platforms
• Basic knowledge of Adobe Creative Suite is a plus

This is a great opportunity to gain hands-on experience in a fast-paced startup environment!""",
            "category": JobCategory.MARKETING,
            "job_type": JobType.INTERNSHIP,
            "workplace_type": JobWorkplace.ON_SITE,
            "location": "Lleida",
            "salary_min": 600,
            "salary_max": 800,
            "salary_period": "month",
            "company_name": "DigitalBoost Agency",
            "company_description": "Creative digital marketing agency helping local businesses grow online.",
            "company_website": "https://digitalboost.example.com",
            "company_employee_count": "10-25",
            "user": verified_users[1],
            "logo_file": "digitalboost-agency.jpg",
            "days_ago": 3,
        },
        {
            "title": "Graphic Designer",
            "description": """We're looking for a creative Graphic Designer to join our team!

What You'll Do:
• Create visual content for web and print media
• Design marketing materials, brochures, and advertisements
• Collaborate with the marketing team on brand identity
• Develop layouts for social media campaigns

Requirements:
• Portfolio demonstrating strong design skills
• Proficiency in Adobe Creative Suite (Photoshop, Illustrator, InDesign)
• Understanding of typography, color theory, and composition
• Ability to work on multiple projects simultaneously

Work with a passionate team in a collaborative environment!""",
            "category": JobCategory.DESIGN,
            "job_type": JobType.PART_TIME,
            "workplace_type": JobWorkplace.REMOTE,
            "location": "Remote",
            "salary_min": 1200,
            "salary_max": 1800,
            "salary_period": "month",
            "company_name": "CreativeMinds Studio",
            "company_description": "Boutique design studio specializing in branding and visual identity.",
            "company_website": "https://creativeminds.example.com",
            "company_employee_count": "5-10",
            "user": verified_users[0],
            "logo_file": "creativeminds-studio.jpg",
            "days_ago": 14,
        },
        {
            "title": "Backend Software Engineer",
            "description": """Join our engineering team to build scalable backend systems!

Responsibilities:
• Design and implement RESTful APIs
• Optimize database queries and improve performance
• Write unit and integration tests
• Deploy and monitor microservices in cloud environments

Requirements:
• 2+ years of experience with Python or Java
• Strong understanding of SQL and NoSQL databases
• Experience with Docker and CI/CD pipelines
• Knowledge of AWS or Azure cloud platforms

Competitive salary, remote work options, and continuous learning opportunities!""",
            "category": JobCategory.ENGINEERING,
            "job_type": JobType.FULL_TIME,
            "workplace_type": JobWorkplace.HYBRID,
            "location": "Lleida",
            "salary_min": 32000,
            "salary_max": 45000,
            "salary_period": "year",
            "company_name": "DataFlow Systems",
            "company_description": "Enterprise software company building data processing solutions.",
            "company_website": "https://dataflow-systems.example.com",
            "company_employee_count": "100-250",
            "user": verified_users[1],
            "logo_file": "dataflow-systems.jpg",
            "days_ago": 5,
        },
        {
            "title": "Customer Support Specialist",
            "description": """Help our customers succeed with our products!

Responsibilities:
• Respond to customer inquiries via email, chat, and phone
• Troubleshoot technical issues and provide solutions
• Document customer feedback and report bugs
• Create help articles and FAQs

Requirements:
• Excellent communication skills in Spanish and English
• Patient and empathetic approach to customer service
• Basic technical knowledge and willingness to learn
• Previous experience in customer support is a plus

Flexible schedule and opportunities for career growth!""",
            "category": JobCategory.CUSTOMER_SERVICE,
            "job_type": JobType.FULL_TIME,
            "workplace_type": JobWorkplace.ON_SITE,
            "location": "Lleida",
            "salary_min": 20000,
            "salary_max": 26000,
            "salary_period": "year",
            "company_name": "HelpDesk Pro",
            "company_description": "Customer service platform helping businesses deliver excellent support.",
            "company_website": "https://helpdesk-pro.example.com",
            "company_employee_count": "25-50",
            "user": verified_users[0],
            "logo_file": "helpdesk-pro.jpg",
            "days_ago": 1,
        },
        {
            "title": "UX/UI Designer",
            "description": """Design exceptional user experiences for web and mobile apps!

Key Responsibilities:
• Conduct user research and usability testing
• Create wireframes, prototypes, and high-fidelity mockups
• Develop design systems and style guides
• Collaborate with developers to ensure design implementation

Requirements:
• 1-3 years of UX/UI design experience
• Strong portfolio showcasing mobile and web projects
• Proficiency in Figma, Sketch, or Adobe XD
• Understanding of user-centered design principles

Work on exciting projects with a talented design team!""",
            "category": JobCategory.DESIGN,
            "job_type": JobType.FULL_TIME,
            "workplace_type": JobWorkplace.REMOTE,
            "location": "Remote",
            "salary_min": 26000,
            "salary_max": 35000,
            "salary_period": "year",
            "company_name": "UserFirst Design",
            "company_description": "UX consultancy helping companies create user-friendly products.",
            "company_website": "https://userfirst.example.com",
            "company_employee_count": "10-25",
            "user": verified_users[1],
            "logo_file": "userfirst-design.jpg",
            "days_ago": 10,
        },
        {
            "title": "Data Analyst",
            "description": """Turn data into actionable insights!

Responsibilities:
• Analyze large datasets to identify trends and patterns
• Create dashboards and visualizations using Power BI/Tableau
• Collaborate with business teams to define KPIs
• Build predictive models and forecasts

Requirements:
• Degree in Statistics, Mathematics, or related field
• Strong SQL skills and experience with Python/R
• Experience with data visualization tools
• Analytical mindset and attention to detail

Great benefits package and professional development opportunities!""",
            "category": JobCategory.TECHNOLOGY,
            "job_type": JobType.FULL_TIME,
            "workplace_type": JobWorkplace.HYBRID,
            "location": "Lleida",
            "salary_min": 30000,
            "salary_max": 40000,
            "salary_period": "year",
            "company_name": "Analytics Hub",
            "company_description": "Data analytics consulting firm serving clients across industries.",
            "company_website": "https://analytics-hub.example.com",
            "company_employee_count": "50-100",
            "user": verified_users[0],
            "logo_file": "analytics-hub.jpg",
            "days_ago": 21,
        },
        {
            "title": "Content Writer",
            "description": """Create engaging content for our blog and marketing materials!

Responsibilities:
• Write blog posts, articles, and website copy
• Research industry trends and topics
• Optimize content for SEO
• Collaborate with the marketing team on content strategy

Requirements:
• Excellent writing skills in Spanish and English
• Experience with content management systems (WordPress)
• Basic understanding of SEO best practices
• Portfolio of published articles

Flexible remote work and creative freedom!""",
            "category": JobCategory.MARKETING,
            "job_type": JobType.FREELANCE,
            "workplace_type": JobWorkplace.REMOTE,
            "location": "Remote",
            "salary_min": None,
            "salary_max": None,
            "salary_period": "project",
            "company_name": "ContentCraft",
            "company_description": None,
            "company_website": None,
            "company_employee_count": None,
            "user": verified_users[1],
            "logo_file": None,
            "days_ago": 30,
        },
    ]

    jobs_with_dates = []
    admin_user = users[0]

    for job_data in jobs_data:
        logo_filename = job_data.pop("logo_file", None)
        user = job_data.pop("user")
        days_ago = job_data.pop("days_ago")

        created_at = now - datetime.timedelta(days=days_ago)

        job = JobOfferTableModel(
            id=uuid.uuid4(),
            user_id=user.id,
            created_at=created_at,
            is_active=True,
            **job_data,
        )

        db.add(job)
        db.flush()

        if logo_filename:
            logo_path = logos_path / logo_filename
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    logo_data = f.read()

                ext = logo_path.suffix.lower()
                content_type_map = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                }
                content_type = content_type_map.get(ext, "image/jpeg")

                file_record = File(
                    id=uuid.uuid4(),
                    filename=logo_filename,
                    content_type=content_type,
                    file_size=len(logo_data),
                    uploaded_at=created_at,
                    is_public=True,
                    storage_type="database",
                    file_data=logo_data,
                    uploader_id=admin_user.id,
                )

                db.add(file_record)
                db.flush()

                file_association = FileAssociation(
                    id=uuid.uuid4(),
                    file_id=file_record.id,
                    entity_type="job_offer",
                    entity_id=job.id,
                    order=0,
                    created_at=created_at,
                )

                db.add(file_association)
            else:
                print(f"WARNING: Logo file not found: {logo_path}")

        jobs_with_dates.append((job, created_at))

    db.commit()

    applicant_pool = [u for u in verified_users if u.role != "Admin"][:5]

    if applicant_pool:
        applications_created = 0
        for job, job_created_at in jobs_with_dates:
            num_applications = random.choice([0, 0, 1, 2, 3, 4])

            if num_applications > 0:
                applicants = random.sample(applicant_pool, min(num_applications, len(applicant_pool)))
                for applicant in applicants:
                    job_age_days = int((now - job_created_at).total_seconds() / 86400)
                    days_after_posting = random.randint(0, min(7, job_age_days))
                    applied_at = job_created_at + datetime.timedelta(days=days_after_posting)

                    application = JobApplication(
                        user_id=applicant.id,
                        job_id=job.id,
                        applied_at=applied_at,
                    )
                    db.add(application)
                    applications_created += 1

        db.commit()
        print(f"* Created {len(jobs_with_dates)} job offers with {applications_created} applications")
    else:
        print(f"* Created {len(jobs_with_dates)} job offers")

    return [job for job, _ in jobs_with_dates]
