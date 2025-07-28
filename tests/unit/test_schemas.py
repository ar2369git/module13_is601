import pytest
from app.schemas.user import UserCreate

def test_usercreate_valid():
    u = UserCreate(username="user1", email="u@example.com", password="password123")
    assert u.username == "user1"

def test_usercreate_invalid_email():
    with pytest.raises(ValueError):
        UserCreate(username="user1", email="notanemail", password="password123")
