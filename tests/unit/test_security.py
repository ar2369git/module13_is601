from app.security import hash_password, verify_password

def test_hash_and_verify():
    password = "supersecret"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrongpass", hashed)
