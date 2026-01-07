import json

from app.literals.job import JobCategory, JobType
from tests.factories.job_factory import sample_job_payload


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestJobEndpoints:
    # ---------------------------------
    # CREATE (Recruiter Only)
    # ---------------------------------
    def test_create_job_as_recruiter(self, client, recruiter_token):
        payload = sample_job_payload(title="Python Guru Needed")
        resp = client.post("/jobs/", json=payload, headers=_auth(recruiter_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Python Guru Needed"
        assert "id" in data

    def test_create_job_as_basic_user_fails(self, client, user_token):
        payload = sample_job_payload()
        resp = client.post("/jobs/", json=payload, headers=_auth(user_token))
        assert resp.status_code == 403

    # ---------------------------------
    # LIST & GET (Public / Filter)
    # ---------------------------------
    def test_list_jobs_with_filters(self, client, recruiter_token):
        payload = sample_job_payload(
            title="Frontend React Dev", category=JobCategory.TECHNOLOGY.value, job_type=JobType.FULL_TIME.value
        )
        client.post("/jobs/", json=payload, headers=_auth(recruiter_token))
        resp = client.get(f"/jobs/?category={JobCategory.TECHNOLOGY.value}")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        items = data["items"]
        assert len(items) > 0
        assert items[0]["category"] == JobCategory.TECHNOLOGY.value

    def test_get_job_detail(self, client, recruiter_token):
        create_resp = client.post("/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token))
        job_id = create_resp.json()["id"]
        resp = client.get(f"/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id

    # ---------------------------------
    # APPLY (Basic User & Admin)
    # ---------------------------------
    def test_apply_to_job_as_basic_user(self, client, recruiter_token, user_token):
        job_resp = client.post("/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token))
        job_id = job_resp.json()["id"]
        app_data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "+34 666 777 888",
            "cover_letter": "I am the best candidate.",
        }
        pdf_content = b"%PDF-1.4 mock content"
        files = {"file": ("cv.pdf", pdf_content, "application/pdf")}
        data = {"application_data": json.dumps(app_data)}
        apply_resp = client.post(f"/jobs/{job_id}/apply", files=files, data=data, headers=_auth(user_token))
        if apply_resp.status_code != 200:
            print(f"\n⚠️ ERROR DEL SERVIDOR: {apply_resp.text}")

        assert apply_resp.status_code == 200
        assert apply_resp.status_code == 200
        assert apply_resp.json()["message"] == "Application submitted successfully"
        my_apps = client.get("/jobs/applied", headers=_auth(user_token))
        assert my_apps.status_code == 200
        ids = [j["id"] for j in my_apps.json()]
        assert job_id in ids
        detail = client.get(f"/jobs/{job_id}", headers=_auth(user_token))
        assert detail.json()["is_applied"] is True

    def test_apply_to_job_as_admin(self, client, recruiter_token, admin_token):
        job_resp = client.post("/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token))
        job_id = job_resp.json()["id"]
        app_data = {"full_name": "Admin User", "email": "admin@test.com"}
        files = {"file": ("admin_cv.pdf", b"%PDF...", "application/pdf")}
        data = {"application_data": json.dumps(app_data)}
        resp = client.post(f"/jobs/{job_id}/apply", files=files, data=data, headers=_auth(admin_token))
        assert resp.status_code == 200

    def test_apply_twice_fails(self, client, recruiter_token, user_token):
        job_resp = client.post("/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token))
        job_id = job_resp.json()["id"]
        app_data = {"full_name": "User", "email": "u@test.com"}
        files = {"file": ("cv.pdf", b"pdf", "application/pdf")}
        data = {"application_data": json.dumps(app_data)}
        client.post(f"/jobs/{job_id}/apply", files=files, data=data, headers=_auth(user_token))
        files_2 = {"file": ("cv.pdf", b"pdf", "application/pdf")}
        resp = client.post(f"/jobs/{job_id}/apply", files=files_2, data=data, headers=_auth(user_token))

        assert resp.status_code == 409

    def test_recruiter_cannot_apply(self, client, recruiter_token):
        job_resp = client.post("/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token))
        job_id = job_resp.json()["id"]
        app_data = {"full_name": "Recruiter", "email": "r@test.com"}
        files = {"file": ("cv.pdf", b"pdf", "application/pdf")}
        data = {"application_data": json.dumps(app_data)}
        resp = client.post(f"/jobs/{job_id}/apply", files=files, data=data, headers=_auth(recruiter_token))
        assert resp.status_code == 403

    # ---------------------------------
    # VIEW APPLICATIONS
    # ---------------------------------
    def test_list_job_applications_as_owner(self, client, recruiter_token, user_token):
        job_resp = client.post("/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token))
        job_id = job_resp.json()["id"]
        app_data = {"full_name": "Applicant One", "email": "app1@test.com"}
        files = {"file": ("cv.pdf", b"pdf", "application/pdf")}
        data = {"application_data": json.dumps(app_data)}
        client.post(f"/jobs/{job_id}/apply", files=files, data=data, headers=_auth(user_token))

        resp = client.get(f"/jobs/{job_id}/applications", headers=_auth(recruiter_token))
        assert resp.status_code == 200
        apps_list = resp.json()
        assert len(apps_list) == 1
        assert apps_list[0]["full_name"] == "Applicant One"
        assert "cv_url" in apps_list[0]

    def test_list_job_applications_forbidden(self, client, recruiter_token, user_token):
        job_resp = client.post("/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token))
        job_id = job_resp.json()["id"]
        resp = client.get(f"/jobs/{job_id}/applications", headers=_auth(user_token))
        assert resp.status_code == 403

    # ---------------------------------
    # SAVE (Bookmarks)
    # ---------------------------------
    def test_toggle_save_job(self, client, recruiter_token, user_token):
        job_resp = client.post("/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token))
        job_id = job_resp.json()["id"]
        resp = client.post(f"/jobs/{job_id}/save", headers=_auth(user_token))
        assert resp.status_code == 200
        assert resp.json()["is_saved"] is True
        saved_list = client.get("/jobs/saved", headers=_auth(user_token))
        assert job_id in [j["id"] for j in saved_list.json()]
        resp2 = client.post(f"/jobs/{job_id}/save", headers=_auth(user_token))
        assert resp2.status_code == 200
        assert resp2.json()["is_saved"] is False

    # ---------------------------------
    # UPDATE & DELETE
    # ---------------------------------
    def test_update_job_as_owner(self, client, recruiter_token):
        job_resp = client.post("/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token))
        job_id = job_resp.json()["id"]
        update_payload = {"title": "Updated Title Example", "salary_min": 50000}
        resp = client.patch(f"/jobs/{job_id}", json=update_payload, headers=_auth(recruiter_token))
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title Example"
        assert float(resp.json()["salary_min"]) == 50000

    def test_delete_job_as_admin(self, client, recruiter_token, admin_token, db):
        job_resp = client.post("/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token))
        job_id = job_resp.json()["id"]
        resp = client.delete(f"/jobs/{job_id}", headers=_auth(admin_token))
        assert resp.status_code == 204
        get_resp = client.get(f"/jobs/{job_id}")
        assert get_resp.status_code == 404
