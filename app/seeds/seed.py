"""Main database seeding script."""

from sqlalchemy.orm import Session

from app.core import Base, engine
from app.seeds import seed_channels, seed_housing_data, seed_interests, seed_users


def seed_database(nuke: bool=False):
    """Populate database with initial data on first run."""
    if nuke:
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    db = Session(engine)

    try:
        print("\nSeeding database...")

        seed_interests(db)
        print("* Interests seeded")

        users = seed_users(db)

        seed_channels(db, users)

        seed_housing_data(db)
        db.commit()
        print("\nDatabase seeded successfully!\n")

    except Exception as e:
        db.rollback()
        print(f"\nError seeding database: {e}\n")
        raise
    finally:
        db.close()
