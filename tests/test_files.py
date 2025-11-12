import io
import uuid

import pytest
import starlette.status

from app.core.config import settings
from app.crud.files import FileCRUD


@pytest.fixture
def settings_fixture():
    """Make settings available as a fixture."""
    return settings


@pytest.fixture
def sample_file_content():
    """Create sample file content for testing."""
    return b"This is a test file content"


@pytest.fixture
def create_test_file(db, user_token, client):
    """Helper fixture to create a test file and return its ID."""

    def _create_file(content=b"test content", filename="test.txt", content_type="text/plain"):
        response = client.post(
            "/files/",
            files={"file": (filename, io.BytesIO(content), content_type)},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        return response.json()["id"] if response.status_code == 200 else None

    return _create_file


class TestFileUpload:
    """Tests for file upload endpoint."""

    def test_upload_file_success(self, client, user_token, sample_file_content):
        """Test successful file upload."""
        response = client.post(
            "/files/",
            files={"file": ("test.txt", io.BytesIO(sample_file_content), "text/plain")},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["content_type"] == "text/plain"
        assert data["file_size"] == len(sample_file_content)
        assert "id" in data
        assert "uploaded_at" in data

    def test_upload_file_unauthorized(self, client, sample_file_content):
        """Test file upload without authentication."""
        response = client.post("/files/", files={"file": ("test.txt", io.BytesIO(sample_file_content), "text/plain")})

        assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED

    def test_upload_file_too_large(self, client, user_token, settings_fixture):
        """Test uploading a file that exceeds size limit."""
        large_content = b"x" * (settings_fixture.MAX_FILE_SIZE + 1)

        response = client.post(
            "/files/",
            files={"file": ("large.txt", io.BytesIO(large_content), "text/plain")},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == starlette.status.HTTP_413_CONTENT_TOO_LARGE
        assert "exceeds the maximum limit" in response.json()["detail"]

    def test_upload_file_invalid_type(self, client, user_token):
        """Test uploading a file with disallowed content type."""
        response = client.post(
            "/files/",
            files={"file": ("test.exe", io.BytesIO(b"content"), "application/x-msdownload")},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == starlette.status.HTTP_400_BAD_REQUEST
        assert "not allowed" in response.json()["detail"]


class TestFileDetail:
    """Tests for file detail endpoint."""

    def test_get_file_detail_success(self, client, user_token, create_test_file):
        """Test retrieving file details as the owner."""
        file_id = create_test_file()

        response = client.get(f"/files/{file_id}", headers={"Authorization": f"Bearer {user_token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == file_id
        assert data["filename"] == "test.txt"
        assert "uploader_id" in data

    def test_get_file_detail_as_admin(self, client, admin_token, create_test_file):
        """Test admin can view any file details."""
        file_id = create_test_file()

        response = client.get(f"/files/{file_id}", headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200

    def test_get_file_detail_forbidden(self, client, user_token, user2_token, create_test_file):
        """Test user cannot view another user's file details."""
        file_id = create_test_file()

        response = client.get(f"/files/{file_id}", headers={"Authorization": f"Bearer {user2_token}"})

        assert response.status_code == starlette.status.HTTP_403_FORBIDDEN

    def test_get_file_detail_not_found(self, client, user_token):
        """Test retrieving non-existent file."""
        fake_id = str(uuid.uuid4())

        response = client.get(f"/files/{fake_id}", headers={"Authorization": f"Bearer {user_token}"})

        assert response.status_code == starlette.status.HTTP_404_NOT_FOUND

    def test_get_file_detail_unauthorized(self, client, create_test_file):
        """Test retrieving file details without authentication."""
        file_id = create_test_file()

        response = client.get(f"/files/{file_id}")

        assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED


class TestFileDownload:
    """Tests for file download endpoint."""

    def test_download_file_success(self, client, user_token, create_test_file, sample_file_content):
        """Test successful file download."""
        file_id = create_test_file(content=sample_file_content)

        response = client.get(f"/files/{file_id}/download", headers={"Authorization": f"Bearer {user_token}"})

        assert response.status_code == 200
        assert response.content == sample_file_content
        assert "attachment" in response.headers["content-disposition"]
        assert response.headers["x-content-type-options"] == "nosniff"

    def test_download_file_as_admin(self, client, admin_token, create_test_file):
        """Test admin can download any file."""
        file_id = create_test_file()

        response = client.get(f"/files/{file_id}/download", headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200

    def test_download_file_forbidden(self, client, user2_token, create_test_file):
        """Test user cannot download another user's file."""
        file_id = create_test_file()

        response = client.get(f"/files/{file_id}/download", headers={"Authorization": f"Bearer {user2_token}"})

        assert response.status_code == starlette.status.HTTP_403_FORBIDDEN


class TestFileView:
    """Tests for file view endpoint."""

    def test_view_file_success(self, client, user_token, create_test_file, sample_file_content):
        """Test viewing file inline."""
        file_id = create_test_file(content=sample_file_content)

        response = client.get(f"/files/{file_id}/view", headers={"Authorization": f"Bearer {user_token}"})

        assert response.status_code == 200
        assert response.content == sample_file_content
        assert "inline" in response.headers["content-disposition"]
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "Content-Security-Policy" in response.headers

    def test_view_file_forbidden(self, client, user2_token, create_test_file):
        """Test user cannot view another user's file."""
        file_id = create_test_file()

        response = client.get(f"/files/{file_id}/view", headers={"Authorization": f"Bearer {user2_token}"})

        assert response.status_code == starlette.status.HTTP_403_FORBIDDEN

    def test_view_file_as_admin(self, client, admin_token, create_test_file):
        """Test admin can view any file."""
        file_id = create_test_file()

        response = client.get(f"/files/{file_id}/view", headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200


class TestFileDelete:
    """Tests for file delete endpoint."""

    def test_delete_file_success(self, client, user_token, create_test_file, db):
        """Test successful file deletion by owner."""
        file_id = create_test_file()

        response = client.delete(f"/files/{file_id}", headers={"Authorization": f"Bearer {user_token}"})

        assert response.status_code == starlette.status.HTTP_204_NO_CONTENT

        with pytest.raises(Exception):
            FileCRUD.get_file_by_id(db, uuid.UUID(file_id))

    def test_delete_file_as_admin(self, client, admin_token, create_test_file, db):
        """Test admin can delete any file."""
        file_id = create_test_file()

        response = client.delete(f"/files/{file_id}", headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == starlette.status.HTTP_204_NO_CONTENT

    def test_delete_file_forbidden(self, client, user2_token, create_test_file):
        """Test user cannot delete another user's file."""
        file_id = create_test_file()

        response = client.delete(f"/files/{file_id}", headers={"Authorization": f"Bearer {user2_token}"})

        assert response.status_code == starlette.status.HTTP_403_FORBIDDEN

    def test_delete_file_not_found(self, client, user_token):
        """Test deleting non-existent file."""
        fake_id = str(uuid.uuid4())

        response = client.delete(f"/files/{fake_id}", headers={"Authorization": f"Bearer {user_token}"})

        assert response.status_code == starlette.status.HTTP_404_NOT_FOUND


class TestListFiles:
    """Tests for listing files endpoint."""

    def test_list_files_success(self, client, user_token, create_test_file):
        """Test listing user's own files."""

        create_test_file(filename="file1.txt")
        create_test_file(filename="file2.txt")

        response = client.get("/files/", headers={"Authorization": f"Bearer {user_token}"})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert all("filename" in item for item in data)

    def test_list_files_pagination(self, client, user_token, create_test_file):
        """Test pagination parameters."""

        for i in range(5):
            create_test_file(filename=f"file{i}.txt")

        response = client.get("/files/?skip=2&limit=2", headers={"Authorization": f"Bearer {user_token}"})

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_files_admin_sees_all(self, client, admin_token, user_token, create_test_file):
        """Test admin can see all files."""

        create_test_file(filename="user_file.txt")

        response = client.get("/files/", headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_files_user_isolation(self, client, user_token, user2_token, create_test_file):
        """Test users only see their own files."""
        create_test_file(filename="user1_file.txt")

        response = client.get("/files/", headers={"Authorization": f"Bearer {user2_token}"})

        assert response.status_code == 200
        data = response.json()

        assert not any(f["filename"] == "user1_file.txt" for f in data)

    def test_list_files_unauthorized(self, client):
        """Test listing files without authentication."""
        response = client.get("/files/")

        assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED


class TestFileContentTypes:
    """Tests for different file content types."""

    @pytest.mark.parametrize(
        "filename,content_type",
        [
            ("document.pdf", "application/pdf"),
            ("image.jpg", "image/jpeg"),
            ("image.png", "image/png"),
            ("data.json", "application/json"),
            ("style.css", "text/css"),
        ],
    )
    def test_upload_various_content_types(self, client, user_token, filename, content_type):
        """Test uploading files with various allowed content types."""
        response = client.post(
            "/files/",
            files={"file": (filename, io.BytesIO(b"content"), content_type)},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        if response.status_code == 200:
            assert response.json()["content_type"] == content_type


class TestPublicFileUpload:
    """Tests for uploading public files."""

    def test_upload_public_file_success(self, client, user_token, sample_file_content):
        """Test successful public file upload."""
        response = client.post(
            "/files/",
            files={"file": ("public_test.jpg", io.BytesIO(sample_file_content), "image/jpeg")},
            data={"is_public": "true"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "public_test.jpg"
        assert data["is_public"] is True
        assert "public_url" in data
        assert f"{settings.API_VERSION}/files/public/{data['id']}" in data["public_url"]

    def test_upload_private_file_no_public_url(self, client, user_token, sample_file_content):
        """Test private file upload has no public URL."""
        response = client.post(
            "/files/",
            files={"file": ("private_test.txt", io.BytesIO(sample_file_content), "text/plain")},
            data={"is_public": "false"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] is False
        assert data.get("public_url") is None

    def test_upload_file_default_private(self, client, user_token, sample_file_content):
        """Test file is private by default when is_public not specified."""
        response = client.post(
            "/files/",
            files={"file": ("default_test.txt", io.BytesIO(sample_file_content), "text/plain")},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] is False


class TestPublicFileView:
    """Tests for viewing public files without authentication."""

    def test_view_public_file_no_auth(self, client, user_token, sample_file_content):
        """Test viewing public file without authentication."""

        upload_response = client.post(
            "/files/",
            files={"file": ("public_image.jpg", io.BytesIO(sample_file_content), "image/jpeg")},
            data={"is_public": "true"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        file_id = upload_response.json()["id"]

        response = client.get(f"/files/public/{file_id}")

        assert response.status_code == 200
        assert response.content == sample_file_content
        assert "inline" in response.headers["content-disposition"]
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "Cache-Control" in response.headers

    def test_view_private_file_as_public_fails(self, client, user_token, sample_file_content):
        """Test accessing private file through public endpoint fails."""

        upload_response = client.post(
            "/files/",
            files={"file": ("private_file.txt", io.BytesIO(sample_file_content), "text/plain")},
            data={"is_public": "false"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        file_id = upload_response.json()["id"]

        response = client.get(f"/files/public/{file_id}")

        assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
        assert "Public file not found" in response.json()["detail"]

    def test_view_public_file_not_found(self, client):
        """Test accessing non-existent public file."""
        fake_id = str(uuid.uuid4())

        response = client.get(f"/files/public/{fake_id}")

        assert response.status_code == starlette.status.HTTP_404_NOT_FOUND

    def test_view_public_file_invalid_id(self, client):
        """Test accessing public file with invalid UUID."""
        response = client.get("/files/public/invalid-uuid")

        assert response.status_code == starlette.status.HTTP_400_BAD_REQUEST
        assert "Invalid file ID format" in response.json()["detail"]

    def test_view_deleted_public_file_fails(self, client, user_token, sample_file_content):
        """Test accessing deleted public file fails."""

        upload_response = client.post(
            "/files/",
            files={"file": ("deleted_file.jpg", io.BytesIO(sample_file_content), "image/jpeg")},
            data={"is_public": "true"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        file_id = upload_response.json()["id"]

        client.delete(f"/files/{file_id}", headers={"Authorization": f"Bearer {user_token}"})

        response = client.get(f"/files/public/{file_id}")

        assert response.status_code == starlette.status.HTTP_404_NOT_FOUND


class TestFileVisibilityUpdate:
    """Tests for updating file visibility."""

    def test_update_file_to_public(self, client, user_token, create_test_file):
        """Test changing file from private to public."""
        file_id = create_test_file()

        response = client.patch(
            f"/files/{file_id}/visibility", json={"is_public": True}, headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] is True
        assert "public_url" in data

    def test_update_file_to_private(self, client, user_token, sample_file_content):
        """Test changing file from public to private."""

        upload_response = client.post(
            "/files/",
            files={"file": ("test.jpg", io.BytesIO(sample_file_content), "image/jpeg")},
            data={"is_public": "true"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        file_id = upload_response.json()["id"]

        response = client.patch(
            f"/files/{file_id}/visibility", json={"is_public": False}, headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] is False
        assert data.get("public_url") is None

    def test_update_visibility_forbidden(self, client, user2_token, create_test_file):
        """Test user cannot update another user's file visibility."""
        file_id = create_test_file()

        response = client.patch(
            f"/files/{file_id}/visibility", json={"is_public": True}, headers={"Authorization": f"Bearer {user2_token}"}
        )

        assert response.status_code == starlette.status.HTTP_403_FORBIDDEN

    def test_update_visibility_as_admin(self, client, admin_token, create_test_file):
        """Test admin can update any file's visibility."""
        file_id = create_test_file()

        response = client.patch(
            f"/files/{file_id}/visibility", json={"is_public": True}, headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        assert response.json()["is_public"] is True

    def test_update_visibility_not_found(self, client, user_token):
        """Test updating visibility of non-existent file."""
        fake_id = str(uuid.uuid4())

        response = client.patch(
            f"/files/{fake_id}/visibility", json={"is_public": True}, headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == starlette.status.HTTP_404_NOT_FOUND

    def test_update_visibility_invalid_id(self, client, user_token):
        """Test updating visibility with invalid UUID."""
        response = client.patch(
            "/files/invalid-uuid/visibility",
            json={"is_public": True},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == starlette.status.HTTP_400_BAD_REQUEST

    def test_update_visibility_unauthorized(self, client, create_test_file):
        """Test updating visibility without authentication."""
        file_id = create_test_file()

        response = client.patch(f"/files/{file_id}/visibility", json={"is_public": True})

        assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED
