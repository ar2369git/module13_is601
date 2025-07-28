# tests/integration/test_user_endpoints.py
def test_register_and_duplicate(client):
    r1 = client.post(
        "/users/register",
        json={"username": "usr1", "email": "usr1@x.com", "password": "pass1234"},
    )
    assert r1.status_code == 200, r1.text
    r2 = client.post(
        "/users/register",
        json={"username": "usr1", "email": "usr1@x.com", "password": "pass1234"},
    )
    assert r2.status_code == 400


def test_login_success_and_failure(client):
    client.post(
        "/users/register",
        json={"username": "loginuser", "email": "login@x.com", "password": "pass1234"},
    )
    ok = client.post(
        "/users/login",
        json={"username_or_email": "loginuser", "password": "pass1234"},
    )
    assert ok.status_code == 200
    token = ok.json()["token"]
    assert token

    bad = client.post(
        "/users/login",
        json={"username_or_email": "loginuser", "password": "wrong"},
    )
    assert bad.status_code == 400
