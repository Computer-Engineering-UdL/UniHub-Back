import datetime

from app.models import User


class TestUserBan:
    """Test user ban functionality."""

    def test_ban_user_as_admin(self, client, admin_auth_headers, db):
        """Test that an admin can ban a user."""
        user = User(
            username="tobeban",
            email="tobeban@example.com",
            password="hashed_password",
            first_name="To Be",
            last_name="Banned",
            referral_code="BANME",
            provider="local",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        response = client.post(
            f"/users/{user.id}/ban",
            headers=admin_auth_headers,
            json={"reason": "Violation of terms", "banned_until": None},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_banned"] is True
        assert data["ban_reason"] == "Violation of terms"
        assert data["banned_until"] is None
        assert data["banned_at"] is not None

        db.refresh(user)
        assert user.is_banned is True
        assert user.ban_reason == "Violation of terms"

    def test_ban_user_expiration(self, client, admin_auth_headers, db):
        """Test banning with expiration."""
        user = User(
            username="tempban",
            email="tempban@example.com",
            password="hashed_password",
            first_name="Temp",
            last_name="Ban",
            referral_code="TMPBN",
            provider="local",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        tomorrow = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
        response = client.post(
            f"/users/{user.id}/ban",
            headers=admin_auth_headers,
            json={"reason": "Temp ban", "banned_until": tomorrow.isoformat()},
        )

        assert response.status_code == 200
        assert response.json()["is_banned"] is True

        db.refresh(user)
        assert user.is_banned is True

    def test_non_admin_cannot_ban(self, client, user_token, db):
        """Test that non-admin cannot ban users."""
        target_id = "00000000-0000-0000-0000-000000000000"  # dummy
        response = client.post(
            f"/users/{target_id}/ban",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"reason": "Malicious attempt"},
        )
        assert response.status_code == 403

    def test_banned_user_login(self, client, db):
        """Test that a banned user cannot login."""
        password = "ComplexPassword123!"
        from app.core.security import hash_password

        user = User(
            username="bannedlogin",
            email="bannedlogin@example.com",
            password=hash_password(password),
            first_name="Banned",
            last_name="User",
            referral_code="BNLOG",
            provider="local",
            is_active=True,
            is_verified=True,
            banned_at=datetime.datetime.now(datetime.UTC),
            banned_until=None,  # Indefinite
        )
        db.add(user)
        db.commit()

        response = client.post("/auth/login", data={"username": "bannedlogin", "password": password})

        assert response.status_code == 403
        assert response.status_code == 403
        detail = response.json()["detail"]
        assert detail["message"] == "User account is banned"
        assert detail["banned_until"] is None

    def test_unban_user(self, client, admin_auth_headers, db):
        """Test unbanning a user."""
        user = User(
            username="tounban",
            email="tounban@example.com",
            password="pwd",
            first_name="To",
            last_name="Unban",
            referral_code="UNBAN",
            provider="local",
            is_active=True,
            is_verified=True,
            banned_at=datetime.datetime.now(datetime.UTC),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.is_banned is True

        response = client.delete(f"/users/{user.id}/ban", headers=admin_auth_headers)
        assert response.status_code == 204

        db.refresh(user)
        assert user.is_banned is False
        assert user.banned_at is None

    def test_banned_future_login(self, client, db):
        """Test login for user banned until future date."""
        password = "ComplexPassword123!"
        from app.core.security import hash_password

        future_date = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)

        user = User(
            username="futureban",
            email="futureban@example.com",
            password=hash_password(password),
            first_name="Future",
            last_name="Ban",
            referral_code="FUTBN",
            provider="local",
            is_active=True,
            is_verified=True,
            banned_at=datetime.datetime.now(datetime.UTC),
            banned_until=future_date,
        )
        db.add(user)
        db.commit()

        # Try to login
        response = client.post("/auth/login", data={"username": "futureban", "password": password})

        assert response.status_code == 403
        detail = response.json()["detail"]
        assert detail["message"] == "User account is banned"
        # Compare without timezone info as SQLite may strip it
        assert detail["banned_until"] == future_date.replace(tzinfo=None).isoformat()

    def test_expired_ban_login(self, client, db):
        """Test that user can login after ban expires."""
        password = "ComplexPassword123!"
        from app.core.security import hash_password

        past_date = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)

        user = User(
            username="expiredban",
            email="expiredban@example.com",
            password=hash_password(password),
            first_name="Expired",
            last_name="Ban",
            referral_code="EXPBN",
            provider="local",
            is_active=True,
            is_verified=True,
            banned_at=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=2),
            banned_until=past_date,
        )
        db.add(user)
        db.commit()

        assert user.is_banned is False

        response = client.post("/auth/login", data={"username": "expiredban", "password": password})

        assert response.status_code == 200
        assert "access_token" in response.json()
