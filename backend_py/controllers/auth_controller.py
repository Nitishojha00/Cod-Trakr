import asyncio
import json
import os
import time
import uuid

import bcrypt
import jwt
from fastapi import Request
from fastapi.responses import PlainTextResponse, Response

from config.redis_client import redis_client as redis
from models.user import create_user, find_by_email, normalize_email, users
from utils.common import get_json_body, js_typeof, json_response
from utils.generate_otp import generate_otp
from utils.send_email import send_email
from utils.validator import validate

limit = 4

COOKIE_OPTIONS = dict(
    httponly=True,
    max_age=60 * 60,  # 1 hour
    samesite="none",  # REQUIRED
    secure=True,      # REQUIRED
    path="/",
)


# ---------- bcrypt helpers (bcryptjs semantics: truncates at 72 bytes) ----------
def _bytes(value):
    return value.encode("utf-8")[:72]


def _check_args(*args):
    if not all(isinstance(a, str) for a in args):
        raise Exception(
            "Illegal arguments: " + ", ".join(js_typeof(a).lower() if js_typeof(a) != "null" else "object" for a in args)
        )


async def bcrypt_hash(value, rounds=10):
    _check_args(value)
    return (await asyncio.to_thread(bcrypt.hashpw, _bytes(value), bcrypt.gensalt(rounds))).decode()


async def bcrypt_compare(value, hashed):
    _check_args(value, hashed)
    return await asyncio.to_thread(bcrypt.checkpw, _bytes(value), hashed.encode())


def sign_token(user_id, email):
    now = int(time.time())
    return jwt.encode(
        {"_id": str(user_id), "email": email, "iat": now, "exp": now + 3600},
        os.environ["JWT_KEY"],
        algorithm="HS256",
    )


def _with_cookie(response: Response, token: str) -> Response:
    response.set_cookie("token", token, **COOKIE_OPTIONS)
    return response


def _error(err):
    return json_response({"success": False, "message": str(err)}, 400)


async def LOGIN(request: Request):
    try:
        body = await get_json_body(request)
        email = body.get("email")
        password = body.get("password")

        validate(email, password)
        user = await find_by_email(email)
        if not user:
            return PlainTextResponse("User not found", status_code=400)

        ok = await bcrypt_compare(password, user.get("password"))
        if not ok:
            return PlainTextResponse("Wrong password", status_code=400)

        token = sign_token(user["_id"], email)
        return _with_cookie(PlainTextResponse("Login successful"), token)
    except Exception as err:  # noqa: BLE001
        return _error(err)


async def signUpGenerateOTP(request: Request):
    try:
        body = await get_json_body(request)
        name = body.get("name")
        email = body.get("email")
        password = body.get("password")

        validate(email, password)
        exists = await find_by_email(email)
        if exists:
            return PlainTextResponse("User already registered", status_code=400)

        # ================= RATE LIMIT (ATOMIC & SAFE) =================
        limit_key = f"otp_limit:{email}"

        count = await redis.incr(limit_key)  # atomic

        if count == 1:
            await redis.expire(limit_key, 3 * 60 * 60)  # 3 hours

        if count > limit:
            return PlainTextResponse(
                "OTP limit exceeded. Try again after 3 hours.", status_code=429
            )

        # ================= OTP GENERATION =================
        otp = generate_otp()
        hashed_password, hashed_otp = await asyncio.gather(
            bcrypt_hash(password), bcrypt_hash(otp)
        )
        signup_id = str(uuid.uuid4())

        # ================= STORE TEMP DATA =================
        payload = {"email": email, "password": hashed_password, "otp": hashed_otp}
        if name is not None:
            payload = {"name": name, **payload}
        await redis.set(f"signup:{signup_id}", json.dumps(payload), ex=5 * 60)  # 5 minutes

        try:
            # ================= SEND EMAIL =================
            await send_email(email, otp)
        except Exception:
            # rollback
            await asyncio.gather(
                redis.decr(limit_key),
                redis.delete(f"signup:{signup_id}"),
                return_exceptions=True,
            )
            raise

        return json_response({"message": "OTP sent", "signupId": signup_id})
    except Exception as err:  # noqa: BLE001
        return _error(err)


async def signUpVerifyOTP(request: Request):
    try:
        body = await get_json_body(request)
        signup_id = body.get("signupId")
        otp = body.get("otp")

        data = await redis.get(f"signup:{signup_id}")
        if not data:
            return PlainTextResponse("OTP expired", status_code=400)

        parsed = json.loads(data)

        is_match = await bcrypt_compare(otp, parsed.get("otp"))
        if not is_match:
            return PlainTextResponse("Invalid OTP", status_code=400)

        user = await create_user(parsed.get("name"), parsed.get("email"), parsed.get("password"))

        # delete redis entry after success
        await redis.delete(f"signup:{signup_id}")

        token = sign_token(user["_id"], user["email"])
        return _with_cookie(PlainTextResponse("Signup successful"), token)
    except Exception as err:  # noqa: BLE001
        return _error(err)
