from typing import List

from sqlalchemy.orm import Session

from app.models import TermsTableModel, User, UserTermsAcceptanceTableModel


def seed_user_acceptances(db: Session, users: List[User], terms: TermsTableModel):
    """
    Creates acceptance records for the provided users and terms.
    """
    acceptances = []

    for user in users:
        exists = db.query(UserTermsAcceptanceTableModel).filter_by(
            user_id=user.id,
            terms_id=terms.id
        ).first()

        if not exists:
            acceptance = UserTermsAcceptanceTableModel(
                user_id=user.id,
                terms_id=terms.id
            )
            acceptances.append(acceptance)

    if acceptances:
        db.add_all(acceptances)
        db.commit()
        print(f"* Accepted Terms v1.0 for {len(acceptances)} users.")
    else:
        print("* All users have already accepted Terms v1.0.")
