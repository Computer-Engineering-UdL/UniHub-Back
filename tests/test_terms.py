import uuid
from typing import Dict

from app.core.config import settings


def sample_terms_payload(version_suffix: str = "") -> Dict[str, str]:
    suffix = version_suffix if version_suffix else str(uuid.uuid4())[:8]
    return {
        "version": f"v.{suffix}",
        "content": f"This is the content for version {suffix}. Terms and conditions apply."
    }


class TestTermsEndpoints:

    def test_create_terms_as_admin(self, client, admin_auth_headers):
        """Admin should be able to create new terms."""
        payload = sample_terms_payload("1.0.TEST")

        url = f"{settings.API_VERSION}/terms/"

        resp = client.post(url, json=payload, headers=admin_auth_headers)

        assert resp.status_code == 201, resp.text
        data = resp.json()

        assert data["version"] == payload["version"]
        assert data["content"] == payload["content"]
        assert "id" in data
        assert "created_at" in data

    def test_create_terms_as_basic_user(self, client, auth_headers):
        """Basic user should NOT be able to create terms."""
        payload = sample_terms_payload("1.1.TEST")

        url = f"{settings.API_VERSION}/terms/"

        resp = client.post(url, json=payload, headers=auth_headers)

        assert resp.status_code == 403
        assert "Admin privileges required" in resp.json()["detail"]

    def test_create_duplicate_version_fails(self, client, admin_auth_headers):
        """Creating a version that already exists should fail (Unique Constraint)."""
        payload = sample_terms_payload("DUPLICATE")
        url = f"{settings.API_VERSION}/terms/"

        resp1 = client.post(url, json=payload, headers=admin_auth_headers)
        assert resp1.status_code == 201

        resp2 = client.post(url, json=payload, headers=admin_auth_headers)
        assert resp2.status_code in [400, 409, 500]

    def test_list_terms(self, client, auth_headers, admin_auth_headers):
        """Should return list of terms. Ordered by newest first."""
        url = f"{settings.API_VERSION}/terms/"

        v1 = sample_terms_payload("LIST_V1")
        v2 = sample_terms_payload("LIST_V2")

        client.post(url, json=v1, headers=admin_auth_headers)
        client.post(url, json=v2, headers=admin_auth_headers)

        resp = client.get(url, headers=auth_headers)
        assert resp.status_code == 200

        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

        versions = [t["version"] for t in data]
        assert v1["version"] in versions
        assert v2["version"] in versions

    def test_get_terms_by_id(self, client, auth_headers, admin_auth_headers):
        """Should return details by UUID."""
        payload = sample_terms_payload("GET_ID")
        url_create = f"{settings.API_VERSION}/terms/"

        create_resp = client.post(url_create, json=payload, headers=admin_auth_headers)
        assert create_resp.status_code == 201
        terms_id = create_resp.json()["id"]

        resp = client.get(f"{settings.API_VERSION}/terms/{terms_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == terms_id
        assert resp.json()["version"] == payload["version"]

    def test_get_terms_by_id_not_found(self, client, auth_headers):
        """Should return 404 for random UUID."""
        random_id = uuid.uuid4()
        resp = client.get(f"{settings.API_VERSION}/terms/{random_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_terms_by_version(self, client, auth_headers, admin_auth_headers):
        """Should return details by version string."""
        target_version = "v.SEARCH_ME"
        payload = sample_terms_payload("SEARCH_ME")
        payload["version"] = target_version

        client.post(f"{settings.API_VERSION}/terms/", json=payload, headers=admin_auth_headers)

        resp = client.get(f"{settings.API_VERSION}/terms/version/{target_version}", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json()["version"] == target_version
        assert resp.json()["content"] == payload["content"]

    def test_get_terms_by_version_not_found(self, client, auth_headers):
        resp = client.get(f"{settings.API_VERSION}/terms/version/v.NON_EXISTENT", headers=auth_headers)
        assert resp.status_code == 404

    def test_update_terms_as_admin(self, client, admin_auth_headers):
        """Admin should be able to update terms content."""
        payload = sample_terms_payload("UPDATE_TEST")
        create_resp = client.post(f"{settings.API_VERSION}/terms/", json=payload, headers=admin_auth_headers)
        terms_id = create_resp.json()["id"]

        update_payload = {"content": "Updated content by Admin."}

        resp = client.patch(f"{settings.API_VERSION}/terms/{terms_id}", json=update_payload, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "Updated content by Admin."
        assert data["version"] == payload["version"]

    def test_update_terms_as_basic_user(self, client, auth_headers, admin_auth_headers):
        """Basic user cannot update terms."""
        payload = sample_terms_payload("UPDATE_FAIL")
        create_resp = client.post(f"{settings.API_VERSION}/terms/", json=payload, headers=admin_auth_headers)
        terms_id = create_resp.json()["id"]

        update_payload = {"content": "Hacker content"}

        resp = client.patch(f"{settings.API_VERSION}/terms/{terms_id}", json=update_payload, headers=auth_headers)

        assert resp.status_code == 403

    def test_update_terms_not_found(self, client, admin_auth_headers):
        random_id = uuid.uuid4()
        resp = client.patch(f"{settings.API_VERSION}/terms/{random_id}", json={"content": "New"},
                            headers=admin_auth_headers)
        assert resp.status_code == 404


    def test_delete_terms_as_admin(self, client, admin_auth_headers, db):
        """Admin can delete terms."""
        payload = sample_terms_payload("DELETE_ME")
        create_resp = client.post(f"{settings.API_VERSION}/terms/", json=payload, headers=admin_auth_headers)
        terms_id = create_resp.json()["id"]

        resp = client.delete(f"{settings.API_VERSION}/terms/{terms_id}", headers=admin_auth_headers)
        assert resp.status_code == 204

        get_resp = client.get(f"{settings.API_VERSION}/terms/{terms_id}", headers=admin_auth_headers)
        assert get_resp.status_code == 404

    def test_delete_terms_as_basic_user(self, client, auth_headers, admin_auth_headers):
        """Basic user cannot delete terms."""
        payload = sample_terms_payload("DELETE_FAIL")
        create_resp = client.post(f"{settings.API_VERSION}/terms/", json=payload, headers=admin_auth_headers)
        terms_id = create_resp.json()["id"]

        resp = client.delete(f"{settings.API_VERSION}/terms/{terms_id}", headers=auth_headers)
        assert resp.status_code == 403

    def test_delete_terms_not_found(self, client, admin_auth_headers):
        random_id = uuid.uuid4()
        resp = client.delete(f"{settings.API_VERSION}/terms/{random_id}", headers=admin_auth_headers)
        assert resp.status_code == 404