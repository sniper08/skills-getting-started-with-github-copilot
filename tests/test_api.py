import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    # Work on a shallow copy for tests to avoid cross-test pollution
    # We'll reset participants to their original values before each test
    original = {
        k: {**v, "participants": list(v.get("participants", []))}
        for k, v in activities.items()
    }
    yield
    activities.clear()
    activities.update(original)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Tennis Club" in data


def test_signup_and_reflects_in_activities():
    activity = "Tennis Club"
    email = "test_student@example.com"

    # Ensure not present initially
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]

    # Sign up
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Signed up")

    # Now activity should contain the participant
    resp = client.get("/activities")
    assert email in resp.json()[activity]["participants"]


def test_remove_participant():
    activity = "Basketball Team"
    # Use an existing participant
    resp = client.get("/activities")
    participants = resp.json()[activity]["participants"]
    assert participants, "no participants to remove for test"
    email = participants[0]

    # Remove
    resp = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Removed")

    # Verify removed
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]


def test_signup_duplicate_fails():
    activity = "Art Studio"
    existing = activities[activity]["participants"][0]

    resp = client.post(f"/activities/{activity}/signup", params={"email": existing})
    assert resp.status_code == 400


def test_remove_nonexistent_participant_returns_404():
    activity = "Drama Club"
    resp = client.delete(f"/activities/{activity}/participants", params={"email": "noone@nowhere.test"})
    assert resp.status_code == 404
