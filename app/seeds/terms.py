import datetime

from sqlalchemy.orm import Session

from app.models import TermsTableModel

# Sample Terms & Conditions content
TERMS_CONTENT_V1 = """
Welcome to the UniHub app!

1. General provisions
   By using the app, you accept the rules of the student community.
2. Conduct guidelines
   Be nice to other students. Do not spam on channels.
3. Housing offers
   Post only genuine listings.
4. Privacy
   Your data is safe (usually).

Version 1.0
"""


def seed_terms(db: Session) -> TermsTableModel:
    """Creates default Terms and Conditions version."""

    # Check if version 1.0.0 already exists
    existing_terms = db.query(TermsTableModel).filter_by(version="1.0.0").first()
    if existing_terms:
        print(f"* Terms 1.0.0 already exists ({existing_terms.id})")
        return existing_terms

    print("Seeding Terms 1.0.0...")

    terms = TermsTableModel(version="1.0.0", content=TERMS_CONTENT_V1, created_at=datetime.datetime.now(datetime.UTC))

    db.add(terms)
    db.commit()
    db.refresh(terms)

    print(f"* Created Terms 1.0.0 with ID: {terms.id}")
    return terms
