# tests/integration/test_fastapi_calculator.py

import pytest  # Import the pytest framework for writing and running tests
from fastapi.testclient import TestClient  # Import TestClient for simulating API requests
from main import app  # Import the FastAPI app instance from your main application file

# ---------------------------------------------
# Pytest Fixture: client
# ---------------------------------------------

@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)

def test_add(client):
    r = client.post("/add", json={"a": 5, "b": 3})
    assert r.status_code == 200
    assert r.json() == {"result": 8}

def test_subtract(client):
    r = client.post("/subtract", json={"a": 10, "b": 4})
    assert r.status_code == 200
    assert r.json() == {"result": 6}

def test_multiply(client):
    r = client.post("/multiply", json={"a": 6, "b": 7})
    assert r.status_code == 200
    assert r.json() == {"result": 42}

def test_divide(client):
    r = client.post("/divide", json={"a": 9, "b": 3})
    assert r.status_code == 200
    assert r.json() == {"result": 3.0}

def test_divide_by_zero(client):
    r = client.post("/divide", json={"a": 10, "b": 0})
    assert r.status_code == 400
    body = r.json()
    assert "error" in body
    assert "Cannot divide by zero!" in body["error"]