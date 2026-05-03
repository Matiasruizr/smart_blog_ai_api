from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from app.config import SettingsDep
from app.core.auth import create_access_token
from app.core.security import verify_password
from app.schemas.auth import TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: SettingsDep,
) -> TokenResponse:
    credentials_valid = (
        form.username == settings.owner_username
        and settings.owner_password_hash
        and verify_password(form.password, settings.owner_password_hash)
    )
    if not credentials_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        subject=form.username,
        secret=settings.secret_key,
        expire_minutes=settings.access_token_expire_minutes,
    )
    return TokenResponse(access_token=token)
