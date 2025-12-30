from app.core.config import settings


class TestEmailVerification:
    """Test email verification flow."""

    def test_send_verification_email_success(self, client, db):
        """Test sending verification email for a registered user."""

        response = client.post(
            "/auth/signup",
            json={
                "username": "verify_test_user",
                "email": "verify_test@example.com",
                "password": "TestPass123!",
                "first_name": "Verify",
                "last_name": "Test",
                "accepted_terms_version": "v1.0.0",
            },
        )

        assert response.status_code == 201

        response = client.post(
            "/auth/verify/send",
            json={"email": "verify_test@example.com"},
        )
        assert response.status_code == 200
        assert "verification link has been sent" in response.json()["message"].lower()

    def test_send_verification_email_nonexistent_user(self, client):
        """Test that sending to non-existent email still returns success (security)."""
        response = client.post(
            "/auth/verify/send",
            json={"email": "nonexistent@example.com"},
        )

        assert response.status_code == 200

    def test_send_verification_already_verified(self, client, db, admin_token):
        """Test that verified users get an error when requesting verification."""

        response = client.post(
            "/auth/verify/send",
            json={"email": "admin@admin.com"},
        )
        assert response.status_code == 400
        assert "already verified" in response.json()["detail"].lower()

    def test_confirm_verification_invalid_token(self, client):
        """Test confirmation with invalid token."""
        response = client.post(
            "/auth/verify/confirm",
            json={"token": "invalid_token_here"},
        )
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


class TestPasswordForgot:
    """Test password forgot/reset flow."""

    def test_forgot_password_success(self, client):
        """Test forgot password request for existing user."""
        response = client.post(
            "/auth/password/forgot",
            json={"email": "admin@admin.com"},
        )
        assert response.status_code == 200
        assert "password reset link" in response.json()["message"].lower()

    def test_forgot_password_nonexistent_email(self, client):
        """Test that non-existent email still returns success (security)."""
        response = client.post(
            "/auth/password/forgot",
            json={"email": "nonexistent@example.com"},
        )

        assert response.status_code == 200

    def test_reset_password_invalid_token(self, client):
        """Test password reset with invalid token."""
        response = client.post(
            "/auth/password/reset",
            json={
                "token": "invalid_token",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!",
            },
        )
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_reset_password_mismatch(self, client):
        """Test password reset with mismatched passwords."""
        response = client.post(
            "/auth/password/reset",
            json={"token": "some_token", "new_password": "NewSecurePass123!", "confirm_password": "DifferentPass123!"},
        )
        assert response.status_code == 422


class TestPasswordChange:
    """Test authenticated password change."""

    def test_change_password_success(self, client, db):
        """Test successful password change."""

        signup_response = client.post(
            "/auth/signup",
            json={
                "username": "pwchange_user",
                "email": "pwchange@example.com",
                "password": "OldPass123!",
                "first_name": "PwChange",
                "last_name": "User",
                "accepted_terms_version": "v1.0.0",
            },
        )
        assert signup_response.status_code == 201
        token = signup_response.json()["access_token"]

        response = client.post(
            "/auth/password/change",
            json={
                "current_password": "OldPass123!",
                "new_password": "NewSecure456!",
                "confirm_password": "NewSecure456!",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "changed successfully" in response.json()["message"].lower()

        login_response = client.post(
            "/auth/login",
            data={"username": "pwchange_user", "password": "NewSecure456!"},
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, client, admin_token):
        """Test password change with wrong current password."""
        response = client.post(
            "/auth/password/change",
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewSecure456!",
                "confirm_password": "NewSecure456!",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_change_password_unauthenticated(self, client):
        """Test password change without authentication."""
        response = client.post(
            "/auth/password/change",
            json={
                "current_password": "OldPass123!",
                "new_password": "NewSecure456!",
                "confirm_password": "NewSecure456!",
            },
        )
        assert response.status_code == 401

    def test_change_password_weak_password(self, client, db):
        """Test password change with weak password."""

        signup_response = client.post(
            "/auth/signup",
            json={
                "username": "weakpw_user",
                "email": "weakpw@example.com",
                "password": "StrongPass123!",
                "first_name": "Weak",
                "last_name": "Password",
                "accepted_terms_version": "v1.0.0",
            },
        )
        token = signup_response.json()["access_token"]

        response = client.post(
            "/auth/password/change",
            json={
                "current_password": "StrongPass123!",
                "new_password": "weak",
                "confirm_password": "weak",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_change_password_mismatch(self, client, admin_token):
        """Test password change with mismatched passwords."""
        response = client.post(
            "/auth/password/change",
            json={
                "current_password": settings.DEFAULT_PASSWORD,
                "new_password": "NewSecure456!",
                "confirm_password": "DifferentPass789!",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422
