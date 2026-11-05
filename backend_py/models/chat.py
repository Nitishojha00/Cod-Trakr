"""Equivalent of models/Chat.js."""
from bson import ObjectId

from config.db import get_db
from utils.common import now_utc


def chats():
    return get_db()["chats"]


async def find_by_user(user_id):
    return await chats().find_one({"userId": ObjectId(user_id)})


def make_message(role, text):
    # `parts: [{ text }]` is an inline subdocument array, so mongoose gives each part an _id
    return {"role": role, "parts": [{"_id": ObjectId(), "text": text}]}


def snapshot_from_stats(stats):
    """statsSnapshot with the schema defaults applied."""
    if not stats:
        return {"totalSolved": 0, "totalContests": 0, "bestRating": 0, "platforms": {}}
    return {
        "totalSolved": stats.get("totalSolved") or 0,
        "totalContests": stats.get("totalContests") or 0,
        "bestRating": stats.get("bestRating") or 0,
        "platforms": stats.get("platforms") or {},
    }


async def save(chat):
    """chat.save(): insert if new, otherwise persist history."""
    now = now_utc()
    if "_id" not in chat:
        chat["createdAt"] = now
        chat["updatedAt"] = now
        chat["__v"] = 0
        result = await chats().insert_one(chat)
        chat["_id"] = result.inserted_id
    else:
        chat["updatedAt"] = now
        await chats().update_one(
            {"_id": chat["_id"]},
            {"$set": {"history": chat["history"], "updatedAt": now}},
        )
    return chat


async def delete_by_user(user_id):
    await chats().find_one_and_delete({"userId": ObjectId(user_id)})
