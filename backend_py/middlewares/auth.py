import os
from dataclasses import dataclass

import jwt
from fastapi import Request

from config.redis_client import redis_client


class Unauthorized(Exception):
    """Rendered as 401 {"message": "Unauthorized"} by the handler in main.py."""


@dataclass
class AuthUser:
    user_id: str
    email: str


async def auth(request: Request) -> AuthUser:
    try:
        token = request.cookies.get("token")
        if not token:
            raise Exception("No token")

        is_blocked = await redis_client.get(f"token:{token}")
        if is_blocked:
            raise Exception("Token blocked")

        decoded = jwt.decode(token, os.environ["JWT_KEY"], algorithms=["HS256"])
        return AuthUser(user_id=decoded["_id"], email=decoded.get("email"))
    except Exception:  # noqa: BLE001
        raise Unauthorized()
