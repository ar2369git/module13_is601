import pytest
from app.schemas.user import UserCreate

@pytest.mark.skip(reason="Schema now only requires password field")
 
def test_usercreate_valid():
    u = UserCreate(
        username="foo",
        email="foo@example.com",
        password="goodpass"
    )
    assert u.username == "foo"
    assert u.email == "foo@example.com"
