import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core import hash_password
from app.core.database import Base, engine
from app.literals.users import Role
from app.models import Interest, InterestCategory, User

DEFAULT_PASSWORD = "unirromsuperadminsecretpassword"

INTEREST_CATALOG = {
    "Academics & Learning": [
        "Study groups",
        "Note-taking",
        "Exam prep",
        "Engineering",
        "Computer science",
        "Design & UX",
        "Data science",
        "AI & ML",
        "Economics & finance",
        "Marketing",
        "Law & public policy",
        "Psychology",
        "Medicine & health",
        "Architecture",
        "Humanities & liberal arts",
        "Research & hackathons",
        "Olympiads & competitions",
        "Scientific reading",
    ],
    "Sports & Fitness": [
        "Running",
        "Cycling",
        "Hiking",
        "Climbing",
        "Soccer",
        "Basketball",
        "Volleyball",
        "Tennis & padel",
        "Gym & calisthenics",
        "Yoga & Pilates",
        "Swimming",
        "E-sports",
        "Dance",
        "Martial arts",
    ],
    "Arts & Culture": [
        "Movies & series",
        "Music & concerts",
        "Podcasting",
        "Photography",
        "Video & editing",
        "Illustration & drawing",
        "Theatre",
        "Literature & book clubs",
        "Museums & exhibitions",
        "Crafts & DIY",
        "Fashion & style",
    ],
    "Tech, Maker & Gaming": [
        "Web & app development",
        "DevOps & cloud",
        "Cybersecurity",
        "Electronics & Arduino",
        "3D printing & fablab",
        "Robotics",
        "Product & tech startups",
        "No-code & automation",
        "Video games",
        "Game design",
        "VR & AR",
    ],
    "Travel & Languages": [
        "Exchange & Erasmus",
        "Budget travel",
        "Backpacking",
        "English language",
        "French language",
        "German language",
        "Italian language",
        "Portuguese language",
        "Swedish language",
        "Catalan & Spanish",
        "Other languages",
        "Language exchange & tandem",
        "International culture",
    ],
    "Volunteering & Sustainability": [
        "Social volunteering",
        "Mentoring",
        "Donations & NGOs",
        "Sustainability",
        "Zero-waste lifestyle",
        "Urban gardening",
        "Beach & mountain clean-ups",
        "Environmental education",
    ],
    "Food, Coffee & Lifestyle": [
        "Coffee shops & study spots",
        "Brunch",
        "Home cooking",
        "Vegetarian & vegan",
        "Nutrition",
        "Baking & pastry",
        "Coffee & tea",
        "Craft beer (18+)",
        "Wine tasting (18+)",
        "Minimalism & organization",
    ],
    "Career & Entrepreneurship": [
        "Job board",
        "Internships",
        "CV & LinkedIn",
        "Consulting case prep",
        "Business cases",
        "Entrepreneurship & startups",
        "Pitching & incubators",
        "Networking & meetups",
        "Career fairs",
    ],
    "Housing & Daily Life": [
        "Room hunting",
        "Roommates",
        "Low-cost decor",
        "Second-hand furniture",
        "Repairs & DIY",
        "Moving & logistics",
        "Expense management",
        "Insurance",
        "Home internet",
    ],
    "Social, Events & Nightlife": [
        "Campus events",
        "Dating",
        "Theme parties",
        "Board games",
        "Role-playing games",
        "Trivia & quiz nights",
        "Student clubs & associations",
    ],
    "Wellbeing & Mindfulness": [
        "Mental health",
        "Mindfulness & meditation",
        "Time management & focus",
        "Bullet journaling",
        "Study-life balance",
        "Digital detox",
    ],
    "Finance & Investing (students)": [
        "Personal budgeting",
        "Saving money",
        "Stocks & ETFs basics",
        "Crypto (educational)",
        "Ethical finance",
        "Scholarships & grants",
    ],
    "Mobility & Carpool": [
        "Daily carpool",
        "Weekend ridesharing",
        "Electric bike",
        "Scooter commuting",
        "Public transport",
        "Road trips",
    ],
}


def seed_interests(db: Session) -> None:
    """Create the default catalog of interest categories and interests."""

    for category_name, interests in INTEREST_CATALOG.items():
        category = db.query(InterestCategory).filter_by(name=category_name).first()
        if not category:
            category = InterestCategory(name=category_name)
            db.add(category)
            db.flush()

        existing = {interest.name for interest in category.interests}
        for interest_name in interests:
            if interest_name not in existing:
                db.add(Interest(name=interest_name, category=category))


def seed_database():
    """Populate database with initial data on first run."""
    Base.metadata.create_all(bind=engine)

    db = Session(engine)

    try:
        seed_interests(db)

        admin = db.query(User).filter_by(email="admin@admin.com").first()
        if admin:
            db.commit()
            print("Database already seeded. Skipping user creation...")
            return

        admin_user = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@admin.com",
            password=hash_password(DEFAULT_PASSWORD),
            first_name="Admin",
            last_name="User",
            phone="+34 666 777 888",
            university="Universitat de Lleida",
            avatar_url="https://avatar.iran.liara.run/public/12",
            room_number="101",
            provider="local",
            role=Role.ADMIN,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
        )
        test_user1 = User(
            id=uuid.uuid4(),
            username="basic_user",
            email="user@user.com",
            password=hash_password(DEFAULT_PASSWORD),
            first_name="Joan",
            last_name="Pere",
            phone="+34 666 111 222",
            university="Universitat de Lleida",
            avatar_url="https://avatar.iran.liara.run/public/34",
            room_number="202",
            provider="local",
            role=Role.BASIC,
            is_active=False,
            is_verified=False,
            created_at=datetime.utcnow(),
        )

        test_user2 = User(
            id=uuid.uuid4(),
            username="jane_smith",
            email="jane@example.com",
            password=hash_password(DEFAULT_PASSWORD),
            first_name="Jane",
            last_name="Smith",
            phone="+34 666 333 444",
            university="Universitat de Barcelona",
            avatar_url="https://avatar.iran.liara.run/public/45",
            room_number="303",
            provider="local",
            role=Role.SELLER,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
        )

        db.add_all([admin_user, test_user1, test_user2])
        db.commit()
        print("Database seeded successfully!")
        print(f"   - Admin: {admin_user.email} / {DEFAULT_PASSWORD}")
        print(f"   - User 1: {test_user1.email} / {DEFAULT_PASSWORD}")
        print(f"   - User 2: {test_user2.email} / {DEFAULT_PASSWORD}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()
