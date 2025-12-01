from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.housing_category import HousingCategoryTableModel
from app.schemas.housing_category import HousingCategoryCreate, HousingCategoryRead


class TestHousingCategoryRepository:

    def test_repository_initializes(self, db, housing_category_repository):
        repo = housing_category_repository

        assert repo.db is db
        assert repo.model is HousingCategoryTableModel

    def test_create_category(self, db, housing_category_repository):
        repo = housing_category_repository

        data = {"name": "TestApartment"}
        category = repo.create(data)

        # Validate returned model
        assert isinstance(category, HousingCategoryTableModel)
        assert isinstance(category.id, UUID)
        assert category.name == "TestApartment"

        # Validate stored in DB
        stored = db.query(HousingCategoryTableModel).filter_by(name="TestApartment").first()
        assert stored is not None
        assert stored.id == category.id

    def test_create_duplicate_name_raises(self, db):
        # First insert
        db.add(HousingCategoryTableModel(name="UniqueName"))
        db.commit()

        # Second insert (duplicate)
        duplicate = HousingCategoryTableModel(name="UniqueName")
        db.add(duplicate)

        with pytest.raises(IntegrityError):
            db.commit()

class TestHousingCategoryService:

    def test_service_initializes(self, category_service, db):
        assert category_service.db is db
        assert category_service.repository is not None

    def test_create_category_success(self, category_service, db):
        payload = HousingCategoryCreate(name="TestCrib")

        result: HousingCategoryRead = category_service.create_category(payload)

        # Validate schema output
        assert isinstance(result, HousingCategoryRead)
        assert isinstance(result.id, UUID)
        assert result.name == "TestCrib"

        # Validate DB persistence
        stored = db.query(HousingCategoryTableModel).filter_by(name="TestCrib").first()
        assert stored is not None
        assert stored.id == result.id

    def test_create_category_duplicate(self, category_service, db):
        # Add existing category
        db.add(HousingCategoryTableModel(name="House"))
        db.flush()

        payload = HousingCategoryCreate(name="House")

        with pytest.raises(Exception):
            category_service.create_category(payload)

