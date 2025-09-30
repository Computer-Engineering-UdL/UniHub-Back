from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def fetch_students():
    """
    Retrieve students.
    """
    return [{"id": 1, "name": "Student 1"}, {"id": 2, "name": "Student 2"}]


@router.get("/{student_id}")
def fetch_student(student_id: int):
    """
    Retrieve a single student by its ID.
    """
    return {"student_id": student_id, "name": f"Student {student_id}"}
