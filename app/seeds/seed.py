"""Main database seeding script."""

from sqlalchemy.orm import Session

from app.core import Base, engine
from app.seeds import seed_housing_data
from app.seeds.amenities import seed_amenities
from app.seeds.category import seed_housing_categories
from app.seeds.channels import seed_channels
from app.seeds.conversations import seed_conversations
from app.seeds.interests import seed_interests
from app.seeds.item_category import seed_item_categories
from app.seeds.messages import seed_messages
from app.seeds.reports import seed_reports
from app.seeds.terms import seed_terms
from app.seeds.university import seed_universities
from app.seeds.user_terms import seed_user_acceptances
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

        messages = seed_messages(db, users, channels)
        print("- Messages seeded")

        seed_housing_categories(db)
        print("- Categories seeded")

        seed_item_categories(db)
        print("- Marketplace Item Categories seeded")

        terms = seed_terms(db)
        print("- Terms seeded")

        seed_user_acceptances(db, users, terms)
        print("- User Terms seeded")

        seed_amenities(db)
        print("- Amenities seeded")

        housing_offers = seed_housing_data(db, users)
        print("- Housing data seeded")

        seed_reports(db, users, channels, messages, housing_offers)
        print("- Reports seeded")

        seed_conversations(db)
        print("- Conversations seeded")

        db.commit()
        print("\nDatabase seeded successfully!\n")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}\n")
        raise
    finally:
        db.close()
