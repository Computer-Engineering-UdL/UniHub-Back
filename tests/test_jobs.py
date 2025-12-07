from app.core.config import settings
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

        resp = client.post(f"{settings.API_VERSION}/jobs/", json=payload, headers=_auth(recruiter_token))

        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Python Guru Needed"
        assert data["company_name"] == "TechStartup BCN"
        assert "id" in data

    def test_create_job_as_basic_user_fails(self, client, user_token):
        """Basic users cannot create job offers."""
        payload = sample_job_payload()
        resp = client.post(f"{settings.API_VERSION}/jobs/", json=payload, headers=_auth(user_token))
        assert resp.status_code == 403

    # ---------------------------------
    # LIST & GET (Public / Filter)
    # ---------------------------------
    def test_list_jobs_with_filters(self, client, recruiter_token):
        payload = sample_job_payload(
            title="Frontend React Dev", category=JobCategory.TECHNOLOGY.value, job_type=JobType.FULL_TIME.value
        )
        client.post(f"{settings.API_VERSION}/jobs/", json=payload, headers=_auth(recruiter_token))
        resp = client.get(f"{settings.API_VERSION}/jobs/?category={JobCategory.TECHNOLOGY.value}")
        assert resp.status_code == 200
        data = resp.json()

        assert len(data) > 0
        assert data[0]["category"] == JobCategory.TECHNOLOGY.value

    def test_get_job_detail(self, client, recruiter_token):
        create_resp = client.post(
            f"{settings.API_VERSION}/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token)
        )
        job_id = create_resp.json()["id"]
        resp = client.get(f"{settings.API_VERSION}/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id

    # ---------------------------------
    # APPLY (Basic User Only)
    # ---------------------------------
    def test_apply_to_job_as_basic_user(self, client, recruiter_token, user_token):
        # El recruiter crea la oferta
        job_resp = client.post(
            f"{settings.API_VERSION}/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token)
        )
        job_id = job_resp.json()["id"]
        apply_resp = client.post(f"{settings.API_VERSION}/jobs/{job_id}/apply", headers=_auth(user_token))
        assert apply_resp.status_code == 200
        assert apply_resp.json()["message"] == "Application submitted successfully"
        my_apps = client.get(f"{settings.API_VERSION}/jobs/applied", headers=_auth(user_token))
        assert my_apps.status_code == 200
        ids = [j["id"] for j in my_apps.json()]
        assert job_id in ids
        detail = client.get(f"{settings.API_VERSION}/jobs/{job_id}", headers=_auth(user_token))
        assert detail.json()["is_applied"] is True

    def test_apply_twice_fails(self, client, recruiter_token, user_token):
        job_resp = client.post(
            f"{settings.API_VERSION}/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token)
        )
        job_id = job_resp.json()["id"]
        client.post(f"{settings.API_VERSION}/jobs/{job_id}/apply", headers=_auth(user_token))
        resp = client.post(f"{settings.API_VERSION}/jobs/{job_id}/apply", headers=_auth(user_token))
        assert resp.status_code == 409

    def test_recruiter_cannot_apply(self, client, recruiter_token):
        """Recruiters should not apply to jobs."""
        job_resp = client.post(
            f"{settings.API_VERSION}/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token)
        )
        job_id = job_resp.json()["id"]

        resp = client.post(f"{settings.API_VERSION}/jobs/{job_id}/apply", headers=_auth(recruiter_token))
        assert resp.status_code == 403

    # ---------------------------------
    # SAVE (Bookmarks)
    # ---------------------------------
    def test_toggle_save_job(self, client, recruiter_token, user_token):
        job_resp = client.post(
            f"{settings.API_VERSION}/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token)
        )
        job_id = job_resp.json()["id"]
        resp = client.post(f"{settings.API_VERSION}/jobs/{job_id}/save", headers=_auth(user_token))
        assert resp.status_code == 200
        assert resp.json()["is_saved"] is True
        saved_list = client.get(f"{settings.API_VERSION}/jobs/saved", headers=_auth(user_token))
        assert job_id in [j["id"] for j in saved_list.json()]
        resp2 = client.post(f"{settings.API_VERSION}/jobs/{job_id}/save", headers=_auth(user_token))
        assert resp2.status_code == 200
        assert resp2.json()["is_saved"] is False

    # ---------------------------------
    # UPDATE & DELETE
    # ---------------------------------
    def test_update_job_as_owner(self, client, recruiter_token):
        job_resp = client.post(
            f"{settings.API_VERSION}/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token)
        )
        job_id = job_resp.json()["id"]
        update_payload = {"title": "Updated Title Example", "salary_min": 50000}
        resp = client.patch(
            f"{settings.API_VERSION}/jobs/{job_id}", json=update_payload, headers=_auth(recruiter_token)
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title Example"
        assert float(resp.json()["salary_min"]) == 50000

    def test_delete_job_as_admin(self, client, recruiter_token, admin_token, db):
        job_resp = client.post(
            f"{settings.API_VERSION}/jobs/", json=sample_job_payload(), headers=_auth(recruiter_token)
        )
        job_id = job_resp.json()["id"]
        resp = client.delete(f"{settings.API_VERSION}/jobs/{job_id}", headers=_auth(admin_token))
        assert resp.status_code == 204

        # Verificar que no existe
        get_resp = client.get(f"{settings.API_VERSION}/jobs/{job_id}")
        assert get_resp.status_code == 404
