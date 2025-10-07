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
        assert len(data) == 2
        assert data[0]["id"] == "32ac1969-9800-4ed7-815d-968f5094039e"
        assert data[0]["first_name"] == "Aniol"
        assert data[0]["last_name"] == "Serrano"
        assert data[1]["id"] == "0bfeba8c-8e01-49fa-a50a-854ebcd19d41"
        assert data[1]["first_name"] == "Admin"
        assert data[1]["last_name"] == "User"

    def test_fetch_student_by_id_success(self, client):
        """Test successful retrieval of a single student"""
        student_id = MOCK_USERS[0]["id"]
        response = client.get(f"/students/{student_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(student_id)
        assert data["first_name"] == "Aniol"
        assert data["last_name"] == "Serrano"

    def test_fetch_student_by_id_different_student(self, client):
        """Test retrieval works for different student IDs"""
        response = client.get("/students/32ac1969-9800-4ed7-815d-968f5094039e")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "32ac1969-9800-4ed7-815d-968f5094039e"

    def test_fetch_student_invalid_id_type(self, client):
        """Test handling of invalid ID type"""
        response = client.get("/students/invalid")
        assert response.status_code == 422
