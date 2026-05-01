from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt


def create_access_token(subject: str, secret: str, expire_minutes: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    return jwt.encode({"sub": subject, "exp": expire}, secret, algorithm="HS256")


def decode_access_token(token: str, secret: str) -> str:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        subject: str | None = payload.get("sub")
        if subject is None:
            raise JWTError
        return subject
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
