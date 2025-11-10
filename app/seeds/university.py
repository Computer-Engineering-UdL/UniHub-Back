from sqlalchemy.orm import Session

from app.models.university import Faculty, University


def seed_universities(db: Session):
    udl = db.query(University).filter_by(name="Universidad de Lleida").first()

    if udl:
        return

    new_udl = University(name="Universidad de Lleida")
    db.add(new_udl)

    faculties_list = [
        "Facultad de Letras",
        "Facultad de Derecho, Economía y Turismo",
        "Escuela Politécnica Superior",
        "Facultad de Educación, Psicología y Trabajo Social",
        "Facultad de Medicina",
        "Facultad de Enfermería y Fisioterapia",
        "Escuela Técnica Superior de Ingeniería Agroalimentaria y Forestal y de Veterinaria",
    ]

    faculties = [Faculty(name=name, university=new_udl) for name in faculties_list]

    db.add_all(faculties)
    db.commit()
    print("🎓 Universidad de Lleida y sus facultades añadidas.")
