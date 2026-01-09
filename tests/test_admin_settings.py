class TestGetSettings:
    """Tests for GET /admin/settings endpoint."""

    def test_get_settings_as_admin(self, client, admin_token):
        """Admin can retrieve settings."""
        response = client.get(
            "/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "system" in data
        assert "security" in data
        assert "content" in data
        assert "notifications" in data

    def test_get_settings_as_non_admin(self, client, user_token):
        """Non-admin user gets 403."""
        response = client.get(
            "/admin/settings",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_get_settings_unauthenticated(self, client):
        """Unauthenticated request gets 401."""
        response = client.get("/admin/settings")
        assert response.status_code == 401

    def test_get_settings_password_masked(self, client, admin_token):
        """SMTP password is masked in response."""
        response = client.get(
            "/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["notifications"]["smtpPassword"] == "********"

    def test_get_settings_structure(self, client, admin_token):
        """Settings response has correct structure."""
        response = client.get(
            "/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        data = response.json()

        system = data["system"]
        assert "maintenanceMode" in system
        assert "allowNewRegistrations" in system
        assert "maxUploadSizeMb" in system
        assert "defaultLanguage" in system

        security = data["security"]
        assert "passwordMinLength" in security
        assert "maxLoginAttempts" in security

        content = data["content"]
        assert "maxPostLength" in content
        assert "profanityFilterEnabled" in content

        notifications = data["notifications"]
        assert "emailFrom" in notifications
        assert "smtpServer" in notifications
        assert "smtpPort" in notifications


class TestUpdateSettings:
    """Tests for PUT /admin/settings endpoint."""

    def test_update_settings_as_admin(self, client, admin_token):
        """Admin can update settings."""
        response = client.put(
            "/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "system": {
                    "maintenanceMode": True,
                    "maxUploadSizeMb": 20,
                }
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Settings updated successfully"
        assert data["settings"]["system"]["maintenanceMode"] is True
        assert data["settings"]["system"]["maxUploadSizeMb"] == 20

    def test_update_settings_as_non_admin(self, client, user_token):
        """Non-admin user gets 403."""
        response = client.put(
            "/admin/settings",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"system": {"maintenanceMode": True}},
        )
        assert response.status_code == 403

    def test_update_settings_partial(self, client, admin_token):
        """Only specified fields are changed."""

        get_response = client.get(
            "/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        original = get_response.json()

        response = client.put(
            "/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "content": {
                    "maxPostLength": 8000,
                }
            },
        )
        assert response.status_code == 200

        data = response.json()

        assert data["settings"]["content"]["maxPostLength"] == 8000

        assert data["settings"]["security"]["passwordMinLength"] == original["security"]["passwordMinLength"]

    def test_update_settings_validation_max_upload_size(self, client, admin_token):
        """Validation error for maxUploadSizeMb out of range."""
        response = client.put(
            "/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "system": {
                    "maxUploadSizeMb": 200,
                }
            },
        )
        assert response.status_code == 422

    def test_update_settings_validation_invalid_language(self, client, admin_token):
        """Validation error for invalid language."""
        response = client.put(
            "/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "system": {
                    "defaultLanguage": "fr",
                }
            },
        )
        assert response.status_code == 422

    def test_update_settings_validation_password_min_length(self, client, admin_token):
        """Validation error for passwordMinLength out of range."""
        response = client.put(
            "/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "security": {
                    "passwordMinLength": 3,
                }
            },
        )
        assert response.status_code == 422


class TestSendTestEmail:
    """Tests for POST /admin/settings/test-email endpoint."""

    def test_send_test_email_as_non_admin(self, client, user_token):
        """Non-admin user gets 403."""
        response = client.post(
            "/admin/settings/test-email",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"email": "test@example.com"},
        )
        assert response.status_code == 403

    def test_send_test_email_invalid_email(self, client, admin_token):
        """Invalid email format returns 422."""
        response = client.post(
            "/admin/settings/test-email",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"email": "invalid-email"},
        )
        assert response.status_code == 422


class TestClearCache:
    """Tests for POST /admin/cache/clear endpoint."""

    def test_clear_cache_as_admin(self, client, admin_token):
        """Admin can clear cache."""
        response = client.post(
            "/admin/cache/clear",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Cache cleared successfully"
        assert "clearedAt" in data
        assert "details" in data
        assert data["details"]["redis"] is True
        assert data["details"]["applicationCache"] is True

    def test_clear_cache_as_non_admin(self, client, user_token):
        """Non-admin user gets 403."""
        response = client.post(
            "/admin/cache/clear",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403


class TestAuditLogging:
    """Tests for audit logging functionality."""

    def test_update_creates_audit_log(self, client, admin_token, db):
        """Settings update creates an audit log entry."""
        from app.models.system_settings import SettingsAuditLog

        initial_count = db.query(SettingsAuditLog).count()

        response = client.put(
            "/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "system": {
                    "maintenanceMode": False,
                }
            },
        )
        assert response.status_code == 200

        new_count = db.query(SettingsAuditLog).count()
        assert new_count == initial_count + 1

        latest_log = db.query(SettingsAuditLog).order_by(SettingsAuditLog.changed_at.desc()).first()
        assert latest_log is not None
        assert "system" in latest_log.changes
