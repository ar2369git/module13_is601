# tests/integration/test_calculation_crud.py
import pytest
from app.models.calculation import CalculationType


def register_and_login(client):
    client.post(
        "/users/register",
        json={"username": "u1", "email": "u1@example.com", "password": "password123"},
    )
    r = client.post(
        "/users/login",
        json={"username_or_email": "u1", "password": "password123"},
    )
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_calculation_crud(client):
    headers = register_and_login(client)

    # Create
    r = client.post(
        "/calculations",
        json={"a": 2, "b": 3, "type": "Add"},
        headers=headers,
    )
    assert r.status_code == 200
    calc = r.json()
    assert calc["result"] == 5
    calc_id = calc["id"]

    # List
    r = client.get("/calculations", headers=headers)
    assert r.status_code == 200
    assert any(c["id"] == calc_id for c in r.json())

    # Read
    r = client.get(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == calc_id

    # Update
    r = client.put(
        f"/calculations/{calc_id}",
        json={"a": 10, "b": 5, "type": "Divide"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["result"] == 2

    # Delete
    r = client.delete(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 204

    # Get after delete -> 404
    r = client.get(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 404


def test_divide_by_zero_error(client):
    headers = register_and_login(client)
    r = client.post(
        "/calculations",
        json={"a": 1, "b": 0, "type": "Divide"},
        headers=headers,
    )
    assert r.status_code == 400
    assert "Division by zero" in r.json()["error"]


def test_auth_required(client):
    # No token
    r = client.get("/calculations")
    assert r.status_code == 401
