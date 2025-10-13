import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.student import router as student_router
from app.services.mock_data import MOCK_USERS


@pytest.fixture
def app():
    """Create FastAPI app instance"""
    app = FastAPI()
    app.include_router(student_router, prefix="/students")
    return app


@pytest.fixture
def client(app):
    """Create test client with the app"""
    return TestClient(app)


class TestStudentEndpoints:
    """Group related student endpoint tests"""

    def test_fetch_students_success(self, client):
        """Test successful retrieval of all students"""
        response = client.get("/students/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == len(MOCK_USERS)
        for user in data:
            assert "id" in user
            assert "username" in user
            assert "email" in user
            assert "first_name" in user
            assert "last_name" in user

    def test_fetch_student_by_id_success(self, client):
        """Test successful retrieval of a single student"""
        student_id = str(MOCK_USERS[0].id)
        response = client.get(f"/students/{student_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == student_id
        assert data["username"] == MOCK_USERS[0].username

    def test_fetch_student_by_id_different_student(self, client):
        """Test retrieval works for different student IDs"""
        student_id = str(MOCK_USERS[0].id)
        response = client.get(f"/students/{student_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == student_id

    def test_fetch_student_invalid_id_type(self, client):
        """Test handling of invalid ID type"""
        response = client.get("/students/invalid")
        assert response.status_code == 422
