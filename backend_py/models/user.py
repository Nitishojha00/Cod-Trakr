"""Equivalent of models/User.js (mongoose schema behaviour reproduced by hand)."""
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from config.db import get_db
from utils.common import now_utc

PLATFORM_KEYS = ("LeetCode", "Codeforces", "CodeChef", "GFG")


def users():
    return get_db()["users"]


def normalize_email(email):
    # schema setters (lowercase + trim) also run on query values in mongoose
    return email.strip().lower() if isinstance(email, str) else email


def hydrate(doc):
    """Mongoose applies schema defaults when loading a document:
    every platform defaults to {}."""
    if doc is None:
        return None
    platforms = dict(doc.get("platforms") or {})
    for key in PLATFORM_KEYS:
        platforms.setdefault(key, {})
    doc["platforms"] = platforms
    return doc


async def find_by_id(user_id, include_password=True):
    projection = None if include_password else {"password": 0}
    doc = await users().find_one({"_id": ObjectId(user_id)}, projection)
    return hydrate(doc)


async def find_by_email(email):
    return hydrate(await users().find_one({"email": normalize_email(email)}))


async def create_user(name, email, password):
    errors = []
    email_v = email.strip().lower() if isinstance(email, str) else email
    if not email_v:
        errors.append("email: Path `email` is required.")
    elif len(email_v) < 5:
        errors.append(
            f"email: Path `email` (`{email_v}`) is shorter than the minimum allowed length (5)."
        )
    if not password:
        errors.append("password: Path `password` is required.")
    elif len(password) < 6:
        errors.append(
            f"password: Path `password` (`{password}`) is shorter than the minimum allowed length (6)."
        )
    if errors:
        raise Exception("User validation failed: " + ", ".join(errors))

    now = now_utc()
    doc = {
        "email": email_v,
        "password": password,
        "platforms": {key: {} for key in PLATFORM_KEYS},
        "createdAt": now,
        "updatedAt": now,
        "__v": 0,
    }
    if name is not None:
        doc["name"] = name

    try:
        result = await users().insert_one(doc)
    except DuplicateKeyError as e:
        raise Exception((e.details or {}).get("errmsg") or str(e))
    doc["_id"] = result.inserted_id
    return doc


def cast_platforms(value):
    """Cast req.body.platforms through the (strict) nested platform schema."""
    if not isinstance(value, dict):
        raise Exception("Cast to Embedded failed for platforms")
    out = {}
    for key in PLATFORM_KEYS:
        if key not in value or value[key] is None:
            continue
        sub = value[key]
        if not isinstance(sub, dict):
            raise Exception(f"Cast to Embedded failed for value at path \"platforms.{key}\"")
        cleaned = {}
        for field in ("username", "profile"):
            if field in sub and sub[field] is not None:
                v = sub[field]
                if not isinstance(v, (str, int, float, bool)):
                    raise Exception(f"Cast to string failed at path \"platforms.{key}.{field}\"")
                cleaned[field] = str(v).strip()
        out[key] = cleaned
    return out


async def update_platforms(user_id, platforms):
    set_doc = {"updatedAt": now_utc()}
    if platforms is not None:
        set_doc["platforms"] = cast_platforms(platforms)
    await users().find_one_and_update({"_id": ObjectId(user_id)}, {"$set": set_doc})
