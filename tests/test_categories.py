from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.housing_category import HousingCategoryTableModel
from app.schemas.housing_category import (
    HousingCategoryCreate,
    HousingCategoryList,
    HousingCategoryRead,
    HousingCategoryUpdate,
)


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

    @pytest.mark.no_seed
    def test_get_all_returns_empty_list(self, db, housing_category_repository):
        repo = housing_category_repository

        categories = repo.get_all()

        assert isinstance(categories, list)
        assert len(categories) == 0

    @pytest.mark.no_seed
    def test_get_all_returns_all_items(self, db, housing_category_repository):
        repo = housing_category_repository

        # Insert multiple rows
        db.add(HousingCategoryTableModel(name="Cat1"))
        db.add(HousingCategoryTableModel(name="Cat2"))
        db.commit()

        categories = repo.get_all()

        assert len(categories) == 2
        names = [c.name for c in categories]
        assert "Cat1" in names
        assert "Cat2" in names

    @pytest.mark.no_seed
    def test_get_all_respects_pagination(self, db, housing_category_repository):
        repo = housing_category_repository

        for i in range(5):
            db.add(HousingCategoryTableModel(name=f"Cat{i}"))
        db.commit()

        categories = repo.get_all(skip=1, limit=2)

        assert len(categories) == 2
        assert categories[0].name == "Cat1"
        assert categories[1].name == "Cat2"

    # --- update ---

    def test_update_existing_category(self, db, housing_category_repository):
        repo = housing_category_repository

        category = HousingCategoryTableModel(name="OldName")
        db.add(category)
        db.commit()
        db.refresh(category)

        updated = repo.update(category.id, {"name": "NewName"})

        assert updated is not None
        assert updated.name == "NewName"

        # Confirm DB update
        stored = db.get(HousingCategoryTableModel, category.id)
        assert stored.name == "NewName"

    def test_update_nonexistent_returns_none(self, housing_category_repository):
        repo = housing_category_repository

        non_existent_id = UUID("00000000-0000-0000-0000-000000000000")

        result = repo.update(non_existent_id, {"name": "DoesNotMatter"})

        assert result is None

    def test_update_ignores_invalid_fields(self, db, housing_category_repository):
        repo = housing_category_repository

        category = HousingCategoryTableModel(name="ValidName")
        db.add(category)
        db.commit()
        db.refresh(category)

        updated = repo.update(
            category.id,
            {
                "name": "UpdatedName",
                "nonexistent_field": "should_be_ignored"
            }
        )

        assert updated.name == "UpdatedName"
        assert not hasattr(updated, "nonexistent_field")

    def test_update_duplicate_name_raises(self, db, housing_category_repository):
        repo = housing_category_repository

        # Insert two rows
        category1 = HousingCategoryTableModel(name="Name1")
        category2 = HousingCategoryTableModel(name="Name2")
        db.add_all([category1, category2])
        db.commit()

        # Try to update category2 to name1
        with pytest.raises(IntegrityError):
            repo.update(category2.id, {"name": "Name1"})
            # Update commits automatically in repo.update

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

    @pytest.mark.no_seed
    def test_create_category_duplicate(self, category_service, db):
        # Add existing category
        db.add(HousingCategoryTableModel(name="House"))
        db.flush()

        payload = HousingCategoryCreate(name="House")

        with pytest.raises(Exception):
            category_service.create_category(payload)

    @pytest.mark.no_seed
    def test_get_category_by_id_success(self, category_service, db):

        category = HousingCategoryTableModel(name="Room")
        db.add(category)
        db.commit()
        db.refresh(category)

        result = category_service.get_category_by_id(category.id)

        assert isinstance(result, HousingCategoryRead)
        assert result.id == category.id
        assert result.name == category.name

    def test_get_category_by_id_not_found(self, category_service):
        fake_id = uuid4()

        with pytest.raises(HTTPException) as exc:
            category_service.get_category_by_id(fake_id)

        assert exc.value.status_code == 404
        assert "not found" in exc.value.detail.lower()

    # --- list_categories ---

    def test_list_categories_returns_all(self, category_service, db):
        db.add(HousingCategoryTableModel(name="Cat1"))
        db.add(HousingCategoryTableModel(name="Cat2"))
        db.commit()

        result = category_service.list_categories()

        assert isinstance(result, list)
        assert all(isinstance(c, HousingCategoryList) for c in result)
        names = [c.name for c in result]
        assert "Cat1" in names
        assert "Cat2" in names

    @pytest.mark.no_seed
    def test_list_categories_pagination(self, category_service, db):
        for i in range(5):
            db.add(HousingCategoryTableModel(name=f"Cat{i}"))
        db.commit()

        result = category_service.list_categories(skip=1, limit=2)

        assert len(result) == 2
        assert result[0].name == "Cat1"
        assert result[1].name == "Cat2"

    # --- update_category ---

    def test_update_category_success(self, category_service, db):
        category = HousingCategoryTableModel(name="OldName")
        db.add(category)
        db.commit()
        db.refresh(category)

        update_payload = HousingCategoryUpdate(name="NewName")
        result = category_service.update_category(category.id, update_payload)

        assert isinstance(result, HousingCategoryRead)
        assert result.name == "NewName"

        stored = db.get(HousingCategoryTableModel, category.id)
        assert stored.name == "NewName"

    def test_update_category_not_found(self, category_service):
        fake_id = uuid4()
        update_payload = HousingCategoryUpdate(name="DoesNotExist")

        with pytest.raises(HTTPException) as exc:
            category_service.update_category(fake_id, update_payload)

        assert exc.value.status_code == 404

    # --- delete_category ---

    def test_delete_category_success(self, category_service, db):
        category = HousingCategoryTableModel(name="ToDelete")
        db.add(category)
        db.commit()
        db.refresh(category)

        category_service.delete_category(category.id)

        stored = db.get(HousingCategoryTableModel, category.id)
        assert stored is None

    def test_delete_category_not_found(self, category_service):
        fake_id = uuid4()
        with pytest.raises(HTTPException) as exc:
            category_service.delete_category(fake_id)

        assert exc.value.status_code == 404

class TestHousingCategoryEndpoints:

    def test_create_category_endpoint(self, client, admin_auth_headers):
        payload = {"name": "NewCategory"}
        response = client.post("/categories/", json=payload, headers=admin_auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "NewCategory"
        assert "id" in data

    def test_create_category_endpoint_no_seed(self, client, admin_auth_headers):
        payload = {"name": "FreshCategory"}
        response = client.post("/categories/", json=payload, headers=admin_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "FreshCategory"
        assert "id" in data

    # -------------------------
    # LIST
    # -------------------------
    def test_list_categories_endpoint(self,client):
        response = client.get("/categories/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # check at least one seeded category exists
        assert any("Room" == c["name"] for c in data)

    def test_list_categories_pagination_endpoint(self, client):
        response = client.get("/categories/?skip=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    # -------------------------
    # GET BY ID
    # -------------------------
    def test_get_category_endpoint(self, client, db):
        # create category in DB
        category = HousingCategoryTableModel(name="TestCat")
        db.add(category)
        db.commit()
        db.refresh(category)

        response = client.get(f"/categories/{category.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(category.id)
        assert data["name"] == "TestCat"

    def test_get_category_not_found(self, client):
        fake_id = uuid4()
        response = client.get(f"/categories/{fake_id}")
        assert response.status_code == 404

    # -------------------------
    # UPDATE
    # -------------------------
    def test_update_category_endpoint(self, client, db, admin_auth_headers):
        category = HousingCategoryTableModel(name="OldName")
        db.add(category)
        db.commit()
        db.refresh(category)

        payload = {"name": "UpdatedName"}
        response = client.patch(f"/categories/{category.id}", json=payload, headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "UpdatedName"

    def test_update_category_not_found(self, client, admin_auth_headers):
        fake_id = uuid4()
        payload = {"name": "DoesNotExist"}
        response = client.patch(f"/categories/{fake_id}", json=payload, headers=admin_auth_headers)
        assert response.status_code == 404

    # -------------------------
    # DELETE
    # -------------------------
    def test_delete_category_endpoint(self, client, db, admin_auth_headers):
        category = HousingCategoryTableModel(name="ToDelete")
        db.add(category)
        db.commit()
        db.refresh(category)

        response = client.delete(f"/categories/{category.id}", headers=admin_auth_headers)
        assert response.status_code == 204

        # confirm deletion
        stored = db.get(HousingCategoryTableModel, category.id)
        assert stored is None

    def test_delete_category_not_found(self, client, admin_auth_headers):
        fake_id = uuid4()
        response = client.delete(f"/categories/{fake_id}", headers=admin_auth_headers)
        assert response.status_code == 404



