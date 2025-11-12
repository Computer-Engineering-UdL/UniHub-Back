import io
import uuid

from app.models import FileAssociation, HousingOfferTableModel


class TestFileAssociations:
    """Tests for file association system."""

    def test_create_file_association(self, client, auth_headers, db):
        """Test creating a file association."""

        file_content = b"test image content"
        files = {"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")}
        upload_resp = client.post("/files/", files=files, data={"is_public": "true"}, headers=auth_headers)
        assert upload_resp.status_code == 200
        file_id = upload_resp.json()["id"]

        offer = db.query(HousingOfferTableModel).first()
        assert offer is not None

        payload = {
            "file_id": file_id,
            "entity_type": "housing_offer",
            "entity_id": str(offer.id),
            "category": "photo",
            "order": 0,
        }
        resp = client.post("/file-associations/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["file_id"] == file_id
        assert data["entity_type"] == "housing_offer"
        assert data["category"] == "photo"

    def test_bulk_create_associations(self, client, auth_headers, db):
        """Test creating multiple associations at once."""

        file_ids = []
        for i in range(3):
            files = {"file": (f"test{i}.jpg", io.BytesIO(b"content"), "image/jpeg")}
            resp = client.post("/files/", files=files, data={"is_public": "true"}, headers=auth_headers)
            assert resp.status_code == 200
            file_ids.append(resp.json()["id"])

        offer = db.query(HousingOfferTableModel).first()

        payload = [
            {
                "file_id": file_id,
                "entity_type": "housing_offer",
                "entity_id": str(offer.id),
                "category": "photo",
                "order": idx,
            }
            for idx, file_id in enumerate(file_ids)
        ]
        resp = client.post("/file-associations/bulk", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 3

    def test_get_associations_by_entity(self, client, auth_headers, db):
        """Test retrieving all associations for an entity."""
        offer = db.query(HousingOfferTableModel).first()

        resp = client.get(f"/file-associations/entity/housing_offer/{offer.id}?category=photo", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_reorder_associations(self, client, auth_headers, db):
        """Test reordering file associations."""

        offer = db.query(HousingOfferTableModel).first()

        file_ids = []
        for i in range(3):
            files = {"file": (f"test{i}.jpg", io.BytesIO(b"content"), "image/jpeg")}
            resp = client.post("/files/", files=files, data={"is_public": "true"}, headers=auth_headers)
            file_ids.append(resp.json()["id"])

        associations = []
        for idx, file_id in enumerate(file_ids):
            payload = {
                "file_id": file_id,
                "entity_type": "housing_offer",
                "entity_id": str(offer.id),
                "order": idx + 100,
            }
            resp = client.post("/file-associations/", json=payload, headers=auth_headers)
            associations.append(resp.json()["id"])

        reorder_payload = {"association_ids": list(reversed(associations))}
        resp = client.post(
            f"/file-associations/entity/housing_offer/{offer.id}/reorder", json=reorder_payload, headers=auth_headers
        )
        assert resp.status_code == 200

        check_resp = client.get(f"/file-associations/entity/housing_offer/{offer.id}", headers=auth_headers)
        all_data = check_resp.json()
        data = [a for a in all_data if a["id"] in associations]

        assert len(data) == 3
        assert data[0]["id"] == associations[2]
        assert data[1]["id"] == associations[1]
        assert data[2]["id"] == associations[0]

    def test_delete_association(self, client, auth_headers, db):
        """Test deleting a file association."""

        files = {"file": ("test.jpg", io.BytesIO(b"content"), "image/jpeg")}
        upload_resp = client.post("/files/", files=files, headers=auth_headers)
        file_id = upload_resp.json()["id"]

        offer = db.query(HousingOfferTableModel).first()

        payload = {"file_id": file_id, "entity_type": "housing_offer", "entity_id": str(offer.id)}
        create_resp = client.post("/file-associations/", json=payload, headers=auth_headers)
        association_id = create_resp.json()["id"]

        resp = client.delete(f"/file-associations/{association_id}", headers=auth_headers)
        assert resp.status_code == 204

        check = db.query(FileAssociation).filter_by(id=uuid.UUID(association_id)).first()
        assert check is None

    def test_housing_offer_photos_property(self, db):
        """Test that housing offer photos property works."""
        offer = db.query(HousingOfferTableModel).first()

        photos = offer.photos
        assert isinstance(photos, list)

        for photo_assoc in photos:
            assert photo_assoc.category in ("photo", None)
            assert hasattr(photo_assoc, "file")
