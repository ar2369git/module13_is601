import os
import subprocess
import time
import pytest
import requests
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient

# tell our DB layer to use in-memory
os.environ["TESTING"] = "1"

from main import app  # ensures startup event runs init_db

@pytest.fixture(scope="session")
def fastapi_server():
    """Background uvicorn server for e2e tests."""
    p = subprocess.Popen(["uvicorn", "main:app"])
    for _ in range(40):
        try:
            requests.get("http://127.0.0.1:8000")
            break
        except Exception:
            time.sleep(0.25)
    yield
    p.terminate()
    p.wait()

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser, fastapi_server):
    pg = browser.new_page()
    yield pg
    pg.close()

@pytest.fixture
def client():
    # TestClient will trigger startup event -> init_db on in-memory DB
    with TestClient(app) as c:
        yield c
