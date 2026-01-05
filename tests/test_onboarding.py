from app.literals.users import OnboardingStep


def test_initial_onboarding_step(client, admin_auth_headers):
    """Test new user has default onboarding step."""
    payload = {
        "email": "onbourding_init@test.com",
        "username": "onboardinit",
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "User",
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 201

    login_resp = client.post("/auth/login", data={"username": payload["email"], "password": payload["password"]})
    token = login_resp.json()["access_token"]

    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["onboarding_step"] == OnboardingStep.NOT_STARTED


def test_update_onboarding_step(client, db):
    """Test updating onboarding step."""
    payload = {
        "email": "onboarding_update@test.com",
        "username": "onboardupdate",
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "User",
    }
    client.post("/auth/signup", json=payload)
    login_resp = client.post("/auth/login", data={"username": payload["email"], "password": payload["password"]})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    new_step = OnboardingStep.PERSONAL_INFO
    resp = client.patch(f"/auth/onboarding/step?step={new_step.value}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["onboarding_step"] == new_step.value

    from app.models import User

    db_user = db.query(User).filter_by(email=payload["email"]).first()
    db.refresh(db_user)
    assert db_user.onboarding_step == new_step.value

    resp = client.patch(f"/auth/onboarding/step?step={OnboardingStep.COMPLETED.value}", headers=headers)
    assert resp.status_code == 200

    db.refresh(db_user)
    assert db_user.onboarding_step == OnboardingStep.COMPLETED.value


def test_token_contains_onboarding_step(client):
    """Test JWT token contains onboarding step claim."""
    payload = {
        "email": "token_step@test.com",
        "username": "tokenstep",
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "User",
    }
    client.post("/auth/signup", json=payload)
    login_resp = client.post("/auth/login", data={"username": payload["email"], "password": payload["password"]})
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/auth/me", headers=headers)
    assert me_resp.json()["onboarding_step"] == OnboardingStep.NOT_STARTED
