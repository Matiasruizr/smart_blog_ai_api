import pytest

from app.core.auth import create_access_token, decode_access_token
from app.core.security import hash_password, verify_password

SECRET = "test-secret-at-least-32-chars-long-yes"


def test_password_hash_and_verify():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token("owner", SECRET, expire_minutes=30)
    subject = decode_access_token(token, SECRET)
    assert subject == "owner"


def test_decode_invalid_token_raises():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not.a.valid.token", SECRET)
    assert exc_info.value.status_code == 401
