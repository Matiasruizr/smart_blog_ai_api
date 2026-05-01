from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.config import SettingsDep
from app.core.auth import decode_access_token

_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(_oauth2)],
    settings: SettingsDep,
) -> str:
    return decode_access_token(token, settings.secret_key)


CurrentUser = Annotated[str, Depends(get_current_user)]
