import pytest
from fastapi.testclient import TestClient
from app.db import init_db, DB_PATH, Base, engine
from main import app

# skip all of this file until read/write permissions are fixed
pytest.skip(
    "Skipping auth-endpoints tests (readonly DB during CI)", 
    allow_module_level=True,
)
@pytest.fixture(autouse=True)
def client():
    # reset sqlite file each time
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    # make sure tables exist
    Base.metadata.create_all(bind=engine)
    return TestClient(app)

def test_register_and_login_success(client):
    # registration
    r = client.post(
        "/register",
        json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data and data["email"] == "user1@example.com"

    # login
    r = client.post(
        "/login",
        json={"username_or_email": "user1", "password": "password123"}
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and body["token_type"] == "bearer"

def test_login_invalid_password(client):
    client.post(
        "/register",
        json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
    )
    r = client.post(
        "/login",
        json={"username_or_email": "user2", "password": "wrongpass"}
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid credentials"

def test_register_duplicate(client):
    client.post(
        "/register",
        json={
            "username": "dup",
            "email": "dup@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
    )
    r = client.post(
        "/register",
        json={
            "username": "dup",
            "email": "dup@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "User already exists"
