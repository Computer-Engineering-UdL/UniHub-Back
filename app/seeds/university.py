from sqlalchemy.orm import Session

from app.models.university import Faculty, University


def seed_universities(db: Session):
    """Seed universities and their faculties."""
    udl = db.query(University).filter_by(name="University of Lleida").first()
    if udl:
        return

    new_udl = University(name="University of Lleida")
    db.add(new_udl)
    db.flush()

    faculties_list = [
        "Faculty of Arts",
        "Faculty of Law, Economics and Tourism",
        "Higher Polytechnic School",
        "Faculty of Education, Psychology and Social Work",
        "Faculty of Medicine",
        "Faculty of Nursing and Physiotherapy",
        "Higher Technical School of Agri-Food and Forestry Engineering and Veterinary Medicine",
    ]

    faculties = [Faculty(name=name, university=new_udl) for name in faculties_list]
    db.add_all(faculties)
    db.flush()
