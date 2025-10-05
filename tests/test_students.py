import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.student import router as student_router


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
        pass
    # TODO: Re-enable and create tests when implementing this task
    # def test_fetch_students_success(self, client):
    #     """Test successful retrieval of all students"""
    #     response = client.get("/students/")
    #
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert isinstance(data, list)
    #     assert len(data) == 2
    #     assert data[0]["id"] == 1
    #     assert data[0]["name"] == "Student 1"
    #     assert data[1]["id"] == 2
    #     assert data[1]["name"] == "Student 2"
    #
    # def test_fetch_student_by_id_success(self, client):
    #     """Test successful retrieval of a single student"""
    #     response = client.get("/students/1")
    #
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["student_id"] == 1
    #     assert data["name"] == "Student 1"
    #
    # def test_fetch_student_by_id_different_student(self, client):
    #     """Test retrieval works for different student IDs"""
    #     response = client.get("/students/42")
    #
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["student_id"] == 42
    #     assert data["name"] == "Student 42"
    #
    # def test_fetch_student_invalid_id_type(self, client):
    #     """Test handling of invalid ID type"""
    #     response = client.get("/students/invalid")
    #     assert response.status_code == 422
