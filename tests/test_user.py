def _auth(token: str) -> dict[str, str]:
    """Build Authorization header once."""
    return {"Authorization": f"Bearer {token}"}


class TestUsersAPI:
    """End-to-end checks for /users endpoints with role enforcement."""

    # ---------------------------------
    # CREATE (admin only)
    # ---------------------------------
    def test_admin_can_create_user_and_basic_cannot(self, client, admin_token, user_token):
        body = {
            "username": "newuser123",
            "email": "newuser123@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "VerySecure123!",
            "provider": "local",
            "role": "Basic",
        }

        # Admin creates the user
        resp = client.post("/users/", json=body, headers=_auth(admin_token))
        assert resp.status_code == 201, resp.text
        created = resp.json()
        assert created["username"] == body["username"]
        assert created["email"] == body["email"]

        # Non-admin is rejected
        resp2 = client.post("/users/", json=body, headers=_auth(user_token))
        assert resp2.status_code == 403

        # Cleanup
        delete_resp = client.delete(f"/users/{created['id']}", headers=_auth(admin_token))
        assert delete_resp.status_code == 204

    # ---------------------------------
    # ME (authenticated)
    # ---------------------------------
    def test_me_returns_profile_when_authenticated(self, client, user_token):
        resp = client.get("/users/me", headers=_auth(user_token))
        assert resp.status_code == 200
        data = resp.json()
        assert {"id", "email", "username"}.issubset(data.keys())

    def test_me_requires_authentication(self, client):
        resp = client.get("/users/me")
        assert resp.status_code == 401

    # ---------------------------------
    # GET by id (admin only)
    # ---------------------------------
    def test_get_user_by_id_admin_only(self, client, admin_token, user_token):
        # Look up a regular user's ID first
        me = client.get("/users/me", headers=_auth(user_token)).json()
        uid = me["id"]

        # Admin can fetch someone else
        r_admin = client.get(f"/users/{uid}", headers=_auth(admin_token))
        assert r_admin.status_code == 200
        assert r_admin.json()["id"] == uid

        # Regular user cannot fetch by id
        r_user = client.get(f"/users/{uid}", headers=_auth(user_token))
        assert r_user.status_code == 403

    # ---------------------------------
    # LIST (admin only)
    # ---------------------------------
    def test_list_users_admin_only(self, client, admin_token, user_token):
        ok = client.get("/users/", headers=_auth(admin_token))
        assert ok.status_code == 200
        assert isinstance(ok.json(), list)

        forbidden = client.get("/users/", headers=_auth(user_token))
        assert forbidden.status_code == 403

    # ---------------------------------
    # PATCH /users/me (self update)
    # ---------------------------------
    def test_update_me_allows_partial_update(self, client, user_token):
        r = client.patch("/users/me", json={"first_name": "UpdatedName"}, headers=_auth(user_token))
        assert r.status_code == 200
        assert r.json()["first_name"] == "UpdatedName"

    # ---------------------------------
    # PATCH /users/{id} (admin only)
    # ---------------------------------
    def test_admin_can_update_other_user(self, client, admin_token, user_token):
        me = client.get("/users/me", headers=_auth(user_token)).json()
        uid = me["id"]

        r_admin = client.patch(f"/users/{uid}", json={"last_name": "AdminSet"}, headers=_auth(admin_token))
        assert r_admin.status_code == 200
        assert r_admin.json()["last_name"] == "AdminSet"

    def test_regular_user_cannot_update_other_user(self, client, admin_token, user_token):
        me = client.get("/users/me", headers=_auth(user_token)).json()
        uid = me["id"]

        r_user = client.patch(f"/users/{uid}", json={"last_name": "Hacked"}, headers=_auth(user_token))
        assert r_user.status_code == 403

    # ---------------------------------
    # Password changes
    # ---------------------------------
    def test_change_my_password(self, client, user_token):
        payload = {
            "current_password": "password",
            "new_password": "NewStrongPassw0rd!",
            "confirm_password": "NewStrongPassw0rd!",
        }
        r = client.put("/users/me/password", json=payload, headers=_auth(user_token))
        assert r.status_code == 200

    def test_admin_can_change_someone_elses_password(self, client, admin_token, user_token):
        me = client.get("/users/me", headers=_auth(user_token)).json()
        uid = me["id"]

        payload = {
            "current_password": "ignored_for_admin",
            "new_password": "AnotherStrongPassw0rd!",
            "confirm_password": "AnotherStrongPassw0rd!",
        }
        r = client.put(f"/users/{uid}/password", json=payload, headers=_auth(admin_token))
        assert r.status_code == 200

    # ---------------------------------
    # DELETE (admin only)
    # ---------------------------------
    def test_delete_user_admin_only(self, client, admin_token, user_token):
        # Create one user we can safely remove
        body = {
            "username": "temp_delete",
            "email": "temp_delete@example.com",
            "first_name": "Temp",
            "last_name": "Delete",
            "password": "TempPass123!",
            "provider": "local",
            "role": "Basic",
        }
        created = client.post("/users/", json=body, headers=_auth(admin_token))
        assert created.status_code == 201
        uid = created.json()["id"]

        # Regular user is forbidden
        forbidden = client.delete(f"/users/{uid}", headers=_auth(user_token))
        assert forbidden.status_code == 403

        # Admin can delete
        ok = client.delete(f"/users/{uid}", headers=_auth(admin_token))
        assert ok.status_code == 204
