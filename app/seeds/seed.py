"""Main database seeding script."""

from sqlalchemy.orm import Session

from app.core import Base, engine
from app.seeds.category import seed_housing_categories
from app.seeds.channels import seed_channels
from app.seeds.interests import seed_interests
from app.seeds.messages import seed_messages
from app.seeds.university import seed_universities
from app.seeds.users import seed_users


def seed_database(nuke: bool = False):
    """Populate database with initial data on first run."""
    if nuke:
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    db = Session(engine)

    try:
        print("\nSeeding database...")

        seed_interests(db)
        print("- Interests seeded")

        seed_universities(db)
        print("- Universities seeded")

        users = seed_users(db)
        print("- Users seeded")

        channels = seed_channels(db, users)
        print("- Channels seeded")

        seed_messages(db, users, channels)
        print("- Messages seeded")

        seed_housing_categories(db)
        print("- Categories seeded")

        # seed_housing_data(db, users)
        # print("- Housing data seeded")

        # seed_conversations(db)
        # print("- Conversations seeded")

        db.commit()
        print("\nDatabase seeded successfully!\n")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}\n")
        raise
    finally:
        db.close()
