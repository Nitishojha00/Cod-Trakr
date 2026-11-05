import os

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

load_dotenv()

_client = None
_db = None


async def main():
    """Equivalent of mongoose.connect(process.env.MONGO_URI)."""
    global _client, _db
    _client = AsyncMongoClient(os.environ["MONGO_URI"])
    # mongoose uses the db named in the URI (falls back to "test")
    _db = _client.get_default_database(default="test")
    await _client.admin.command("ping")
    await ensure_indexes()


def get_db():
    if _db is None:
        raise RuntimeError("MongoDB is not connected")
    return _db


async def ensure_indexes():
    """Same indexes mongoose would auto-create from the schemas."""
    db = get_db()
    try:
        await db["users"].create_index("email", unique=True)
        await db["notes"].create_index("problemName", unique=True)
        await db["chats"].create_index("userId")
    except Exception as err:  # noqa: BLE001
        print("Index creation warning:", err)


async def close():
    if _client is not None:
        await _client.close()
