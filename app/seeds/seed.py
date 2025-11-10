"""Main database seeding script."""

from sqlalchemy.orm import Session

from app.core import Base, engine
from app.seeds import seed_channels, seed_housing_data, seed_interests, seed_users
from app.seeds.conversations import seed_conversations
from app.seeds.messages import seed_messages
from app.seeds.university import seed_universities


def seed_database(nuke: bool = False):
    """Populate database with initial data on first run."""
    if nuke:
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    db = Session(engine)

    try:
        print("\nSeeding database...")

        seed_interests(db)
        print("* Interests seeded")
        seed_universities(db)
        users = seed_users(db)
        channels = seed_channels(db, users)
        seed_messages(db, users, channels)
        seed_housing_data(db)
        seed_conversations(db)
        db.commit()
        print("\nDatabase seeded successfully!\n")

    except Exception as e:
        db.rollback()
        print(f"\nError seeding database: {e}\n")
        raise
    finally:
        db.close()
