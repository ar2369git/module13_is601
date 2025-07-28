import pytest
from playwright.sync_api import Page

BASE = "http://localhost:8000"

@pytest.mark.e2e
def test_register_flow(page: Page):
    page.goto(f"{BASE}/register.html")
    # fill valid
    page.fill("input[name='email']", "e2e@example.com")
    page.fill("input[name='username']", "e2euser")
    page.fill("input[name='password']", "password123")
    page.fill("input[name='confirm_password']", "password123")
    page.click("button#register")
    # expect success message
    page.wait_for_selector("text=Registration successful")

@pytest.mark.e2e
def test_register_short_password(page: Page):
    page.goto(f"{BASE}/register.html")
    page.fill("input[name='email']", "short@example.com")
    page.fill("input[name='username']", "shortuser")
    page.fill("input[name='password']", "short")
    page.fill("input[name='confirm_password']", "short")
    page.click("button#register")
    # UI validation error
    assert "at least 8 characters" in page.inner_text(".error")

@pytest.mark.e2e
def test_login_flow(page: Page):
    # assume the user from test_register_flow exists
    page.goto(f"{BASE}/login.html")
    page.fill("input[name='username_or_email']", "e2euser")
    page.fill("input[name='password']", "password123")
    page.click("button#login")
    page.wait_for_selector("text=Login successful")

@pytest.mark.e2e
def test_login_invalid(page: Page):
    page.goto(f"{BASE}/login.html")
    page.fill("input[name='username_or_email']", "e2euser")
    page.fill("input[name='password']", "wrongpass")
    page.click("button#login")
    assert "Invalid credentials" in page.inner_text(".error")
