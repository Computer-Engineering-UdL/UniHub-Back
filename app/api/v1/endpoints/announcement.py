from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.utils import handle_crud_errors  # 👈 asegúrate de importar el decorador
from app.core.database import get_db
from app.crud.announcement import AnnouncementCRUD
from app.schemas.announcement import AnnouncementCreate, AnnouncementPublic, AnnouncementUpdate

router = APIRouter()


@router.get("/", response_model=list[AnnouncementPublic])
@handle_crud_errors
def fetch_announcements(db: Session = Depends(get_db)):
    """
    Retrieve all announcements.
    """
    return AnnouncementCRUD.get_all(db)


@router.get("/{announcement_id}", response_model=AnnouncementPublic)
@handle_crud_errors
def fetch_announcement(announcement_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific announcement by ID.
    """
    return AnnouncementCRUD.get_by_id(db, announcement_id)


@router.post("/", response_model=AnnouncementPublic)
@handle_crud_errors
def create_announcement(announcement_in: AnnouncementCreate, db: Session = Depends(get_db)):
    """
    Create a new announcement.
    """
    return AnnouncementCRUD.create(db, announcement_in)


@router.patch("/{announcement_id}", response_model=AnnouncementPublic)
@handle_crud_errors
def update_announcement(announcement_id: int, announcement_in: AnnouncementUpdate, db: Session = Depends(get_db)):
    """
    Update an existing announcement.
    """
    return AnnouncementCRUD.update(db, announcement_id, announcement_in)


@router.delete("/{announcement_id}")
@handle_crud_errors
def delete_announcement(announcement_id: int, db: Session = Depends(get_db)):
    """
    Delete an announcement.
    """
    return AnnouncementCRUD.delete(db, announcement_id)
