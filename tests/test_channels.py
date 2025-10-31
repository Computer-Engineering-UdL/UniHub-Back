class TestChannelEndpoints:
    """Test channel CRUD operations with permissions."""

    def test_create_channel_fails_for_non_admin(self, client, user_token, seller_token):
        """Test regular users (basic, seller) cannot create a channel."""
        for token in [user_token, seller_token]:
            response = client.post(
                "/channels/",
                json={
                    "name": "Failed Channel",
                    "description": "This should not be created",
                    "channel_type": "public",
                    "read_min_role": "Basic",
                    "write_min_role": "Seller",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 403

    def test_create_channel_success_for_admin(self, client, admin_token, admin_user):
        """Test site admin can create a channel and becomes channel admin."""
        response = client.post(
            "/channels/",
            json={
                "name": "Admin Test Channel",
                "description": "A test channel by admin",
                "channel_type": "public",
                "read_min_role": "Basic",
                "write_min_role": "Seller",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Admin Test Channel"
        assert data["read_min_role"] == "Basic"
        assert data["write_min_role"] == "Seller"

        channel_id = data["id"]
        member_response = client.get(
            f"/channels/{channel_id}/member/{admin_user.id}/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert member_response.status_code == 200
        assert member_response.json()["role"] == "admin"

    def test_create_channel_without_auth(self, client):
        """Test creating channel without authentication fails."""
        response = client.post(
            "/channels/",
            json={"name": "Test Channel", "channel_type": "public"},
        )
        assert response.status_code == 401

    def test_update_channel_requires_site_admin(self, client, admin_token, seller_token, seller_user):
        """Test only SITE admin can update channel (channel members/admins cannot)."""
        create_response = client.post(
            "/channels/",
            json={"name": "Update Test", "description": "Original", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        channel_id = create_response.json()["id"]

        client.post(
            f"/channels/{channel_id}/add_member/{seller_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.patch(
            f"/channels/{channel_id}",
            json={"description": "Hacked"},
            headers={"Authorization": f"Bearer {seller_token}"},
        )
        assert response.status_code == 403
        response = client.patch(
            f"/channels/{channel_id}",
            json={"description": "Updated description"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    def test_delete_channel_requires_site_admin(self, client, admin_token, seller_token, seller_user):
        """Test only SITE admin can delete channel (channel members/admins cannot)."""
        create_response = client.post(
            "/channels/",
            json={"name": "Delete Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        channel_id = create_response.json()["id"]

        client.post(
            f"/channels/{channel_id}/add_member/{seller_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.delete(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {seller_token}"})
        assert response.status_code == 403

        response = client.delete(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        assert response.json() is True

    def test_fetch_all_channels_filters_by_role(self, client, admin_token, seller_token, user_token):
        """Test GET /channels/ filters based on site role (Admin, Seller, Basic, Anonymous)."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        test_channels_set = {"Admin Read", "Seller Read", "Basic Read"}
        client.post(
            "/channels/",
            json={"name": "Admin Read", "read_min_role": "Admin", "write_min_role": "Admin"},
            headers=headers,
        )
        client.post(
            "/channels/",
            json={"name": "Seller Read", "read_min_role": "Seller", "write_min_role": "Seller"},
            headers=headers,
        )
        client.post(
            "/channels/",
            json={"name": "Basic Read", "read_min_role": "Basic", "write_min_role": "Basic"},
            headers=headers,
        )

        # --- Test Admin ---
        response_admin = client.get("/channels/", headers={"Authorization": f"Bearer {admin_token}"})
        assert response_admin.status_code == 200
        names_admin = {c["name"] for c in response_admin.json()}
        assert names_admin >= test_channels_set

        response_seller = client.get("/channels/", headers={"Authorization": f"Bearer {seller_token}"})
        assert response_seller.status_code == 200
        names_seller = {c["name"] for c in response_seller.json()}
        assert names_seller >= {"Seller Read", "Basic Read"}
        assert "Admin Read" not in names_seller

        # --- Test Basic ---
        response_basic = client.get("/channels/", headers={"Authorization": f"Bearer {user_token}"})
        assert response_basic.status_code == 200
        names_basic = {c["name"] for c in response_basic.json()}
        assert names_basic >= {"Basic Read"}
        assert "Admin Read" not in names_basic
        assert "Seller Read" not in names_basic
        response_anon = client.get("/channels/")
        assert response_anon.status_code == 200
        names_anon = {c["name"] for c in response_anon.json()}
        assert names_anon >= {"Basic Read"}
        assert "Admin Read" not in names_anon
        assert "Seller Read" not in names_anon

    def test_fetch_channel_requires_membership(self, client, admin_token, user_token, user2_token, basic_user):
        """Test only members can view a channel."""
        create_response = client.post(
            "/channels/",
            json={"name": "Private Channel", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_response.status_code == 200
        channel_id = create_response.json()["id"]

        client.post(
            f"/channels/{channel_id}/add_member/{basic_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.get(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200

        response = client.get(f"/channels/{channel_id}", headers={"Authorization": f"Bearer {user2_token}"})
        assert response.status_code == 403

    def test_add_member_requires_channel_admin(self, client, admin_token, user_token, basic_user, basic_user_2):
        """Test only channel admin can add members."""
        create_response = client.post(
            "/channels/",
            json={"name": "Member Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        channel_id = create_response.json()["id"]

        response = client.post(
            f"/channels/{channel_id}/add_member/{basic_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        response = client.post(
            f"/channels/{channel_id}/add_member/{basic_user_2.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_remove_member_moderator_can_remove(self, client, admin_token, basic_user):
        """Test moderators (or admin) can remove members."""
        create_response = client.post(
            "/channels/",
            json={"name": "Remove Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        channel_id = create_response.json()["id"]

        client.post(
            f"/channels/{channel_id}/add_member/{basic_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.post(
            f"/channels/{channel_id}/remove_member/{basic_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_ban_member_moderator_required(self, client, admin_token, basic_user):
        """Test only moderators and above can ban members."""
        create_response = client.post(
            "/channels/",
            json={"name": "Ban Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        channel_id = create_response.json()["id"]

        client.post(
            f"/channels/{channel_id}/add_member/{basic_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.post(
            f"/channels/{channel_id}/ban",
            json={"user_id": str(basic_user.id), "motive": "Test ban", "duration_days": 7},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["motive"] == "Test ban"
        assert data["active"] is True

    def test_unban_member_moderator_required(self, client, admin_token, basic_user):
        """Test only moderators and above can unban members."""
        create_response = client.post(
            "/channels/",
            json={"name": "Unban Test", "description": "Test", "channel_type": "public"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        channel_id = create_response.json()["id"]

        client.post(
            f"/channels/{channel_id}/add_member/{basic_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        client.post(
            f"/channels/{channel_id}/ban",
            json={"user_id": str(basic_user.id), "motive": "Test", "duration_days": 7},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        response = client.post(
            f"/channels/{channel_id}/unban",
            json={"user_id": str(basic_user.id), "motive": "Appealed"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["motive"] == "Appealed"
