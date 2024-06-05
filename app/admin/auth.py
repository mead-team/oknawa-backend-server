from datetime import datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqladmin.authentication import AuthenticationBackend

from app.core.setting import settings


class BasicAuthBackend(AuthenticationBackend):
    async def login(self, request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if username == settings.ADMIN_ID and password == settings.ADMIN_PASSWORD:
            access_token = create_access_token({"sub": str(username)})
            request.session.update({"token": access_token})
            return True
        return False

    async def logout(self, request) -> None:
        request.session.clear()
        return True

    async def authenticate(self, request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        try:
            payload = jwt.decode(
                token, settings.OKNAWA_SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWTError",
            )

        expire = payload.get("exp")
        if not expire or (int(expire) < datetime.utcnow().timestamp()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="token expiration",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="token expiration",
            )
        elif user_id != settings.ADMIN_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="token expiration",
            )
        return True


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(days=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.OKNAWA_SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


authentication_backend = BasicAuthBackend(secret_key=settings.OKNAWA_SECRET_KEY)
