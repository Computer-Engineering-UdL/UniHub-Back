from app.core.security import get_payload
from app.models import HousingCategoryTableModel
from tests.factories.offer_factory import sample_offer_payload


class TestUserLikesEndpoints:
    def test_like_flow_for_offer(self, client, db, auth_headers, user_token):
        """Full cycle: create offer → like → check → unlike → check again."""

        # download user ID from token
        user_data = get_payload(user_token)
        user_id = user_data["sub"]

        # choose a housing category from DB
        category = db.query(HousingCategoryTableModel).first()
        assert category is not None, "No housing category found in test DB."

        # create a housing offer
        payload = sample_offer_payload(user_id=user_id, category_id=str(category.id))
        resp_offer = client.post("/offers/", json=payload, headers=auth_headers)
        assert resp_offer.status_code == 201, resp_offer.text
        offer_id = resp_offer.json()["id"]

        # like the offer
        like_resp = client.post(f"/user-likes/{offer_id}", headers=auth_headers)
        assert like_resp.status_code == 201, like_resp.text
        like_data = like_resp.json()
        assert like_data["status"] == "active"
        assert like_data["target_id"] == offer_id

        # check the like status
        status_resp = client.get(f"/user-likes/{offer_id}/status", headers=auth_headers)
        assert status_resp.status_code == 200
        assert status_resp.json()["liked"] is True

        # get myu likes and verify the offer is listed
        my_likes_resp = client.get("/user-likes/me", headers=auth_headers)
        assert my_likes_resp.status_code == 200
        my_likes = my_likes_resp.json()
        assert any(like["target_id"] == offer_id for like in my_likes)

        # unlike the offer
        unlike_resp = client.delete(f"/user-likes/{offer_id}", headers=auth_headers)
        assert unlike_resp.status_code == 200
        assert "deactivated" in unlike_resp.json()["detail"].lower()

        # check the like status again
        status_after = client.get(f"/user-likes/{offer_id}/status", headers=auth_headers)
        assert status_after.status_code == 200
        assert status_after.json()["liked"] is False
