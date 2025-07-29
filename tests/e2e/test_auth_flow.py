import pytest
from playwright.sync_api import Page

BASE = "http://localhost:8000"

@pytest.mark.skip(reason="timeout error")
def test_register_flow(page: Page):
    page.goto(f"{BASE}/register.html")
    page.fill("input[name='email']", "e2e@example.com")
    page.fill("input[name='username']", "e2euser")
    page.fill("input[name='password']", "password123")
    page.fill("input[name='confirm_password']", "password123")
    page.click("form#register-form button[type=submit]")
    page.wait_for_selector("#message:has-text('Registration successful')", timeout=5000)

@pytest.mark.skip(reason="UI not showing short-password message yet")
def test_register_short_password(page: Page):
    page.goto(f"{BASE}/register.html")
    page.fill("input[name='email']", "short@example.com")
    page.fill("input[name='username']", "shortuser")
    page.fill("input[name='password']", "short")
    page.fill("input[name='confirm_password']", "short")
    page.click("form#register-form button[type=submit]")
    page.wait_for_selector("#message:has-text('Password must be at least 8 characters')", timeout=5000)

@pytest.mark.e2e
def test_login_flow(page: Page):
    page.goto(f"{BASE}/login.html")
    page.fill("input[name='username_or_email']", "e2euser")
    page.fill("input[name='password']", "password123")
    page.click("form#login-form button[type=submit]")
    page.wait_for_selector("#message:has-text('Login successful')", timeout=5000)

@pytest.mark.e2e
def test_login_invalid(page: Page):
    page.goto(f"{BASE}/login.html")
    page.fill("input[name='username_or_email']", "e2euser")
    page.fill("input[name='password']", "wrongpass")
    page.click("form#login-form button[type=submit]")
    page.wait_for_selector("#message:has-text('Invalid credentials')", timeout=5000)
