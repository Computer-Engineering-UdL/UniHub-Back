import sqlalchemy as sa
from pydantic import BaseModel, Field
from sqlalchemy import Column
from sqlalchemy.orm import relationship

from app.core.database import Base


class HousingCategory(BaseModel):
    """
    Pydantic model representing a housing category.
    Used for data validation and serialization in API requests/responses.
    """
    id: int | None = None
    name: str = Field(min_length=1, max_length=50)

    class Config:
        # Allows Pydantic model to be created from ORM objects
        from_attributes = True


class HousingCategoryTableModel(Base):
    """
    SQLAlchemy model representing a housing category in the database.
    Maps to the 'housing_category' table.
    Establishes a relationship to housing offers.
    """
    __tablename__ = "housing_category"

    id = Column(sa.Integer, primary_key=True, autoincrement=True)
    name = Column(sa.String(50), nullable=False, unique=True)

    # One-to-many relationship: a category can have multiple housing offers
    housing_offers = relationship("HousingOfferTableModel", back_populates="category")
