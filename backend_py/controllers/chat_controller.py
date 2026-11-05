import json
import os

from bson import ObjectId
from fastapi import Request
from google import genai
from google.genai import types

from config.redis_client import redis_client
from middlewares.auth import AuthUser
from models import chat as chat_model
from models.user import find_by_id
from utils.common import get_json_body, json_response

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


# ================= SYSTEM PROMPT BUILDER =================
def build_system_prompt(user, stats):
    platforms = (stats or {}).get("platforms") or {}

    def nz(v):  # JS `??` 0
        return 0 if v is None else v

    platform_details = "\n".join(
        f'  - {name}: username="{p.get("username")}", solved={nz(p.get("solved"))}, '
        f'rating={nz(p.get("rating"))}, contests={nz(p.get("contests"))}, rank={nz(p.get("rank"))}'
        for name, p in platforms.items()
        if isinstance(p, dict) and p.get("username")
    )

    s = stats or {}
    return f"""You are an expert competitive programming coach and mentor integrated into COD TRAKR — a platform that tracks a coder's performance across LeetCode, Codeforces, CodeChef, and GeeksForGeeks.

The user you are helping is:
  Name: {user.get("name") or "Coder"}
  Email: {user.get("email")}

Their current coding stats across platforms:
{platform_details or "  No platforms linked yet."}

Aggregated Stats:
  - Total Problems Solved: {nz(s.get("totalSolved"))}
  - Total Contests Participated: {nz(s.get("totalContests"))}
  - Best Rating: {nz(s.get("bestRating"))}
  - Active Platforms: {nz(s.get("platformCount"))}

Your role:
1. Analyze their current performance based on the stats above.
2. Ask them about their easy/medium/hard split if not provided, and use that to personalize advice.
3. Give specific, actionable improvement plans (topics to study, problem counts, contest frequency).
4. Recommend specific LeetCode patterns (sliding window, DP, graphs, etc.) based on their level.
5. Be encouraging but realistic. Use data to back your recommendations.
6. Keep responses concise and structured (use bullet points and headings where helpful).
7. If they ask unrelated questions, politely redirect to coding improvement topics.

Start by greeting them and asking a key question to understand their current weak areas."""


# ================= GET CHAT HISTORY =================
async def getChatHistory(request: Request, user: AuthUser):
    try:
        chat = await chat_model.find_by_user(user.user_id)

        if not chat:
            return json_response({"history": [], "statsSnapshot": None})

        return json_response(
            {"history": chat.get("history", []), "statsSnapshot": chat.get("statsSnapshot")}
        )
    except Exception as err:  # noqa: BLE001
        print("getChatHistory Error:", err)
        return json_response({"message": "Server Error"}, 500)


# ================= SEND MESSAGE =================
async def sendMessage(request: Request, auth_user: AuthUser):
    try:
        user_id = auth_user.user_id
        body = await get_json_body(request)
        message = body.get("message")

        if not message or not message.strip():
            return json_response({"message": "Message cannot be empty"}, 400)

        # Fetch user data
        user = await find_by_id(user_id, include_password=False)
        if not user:
            return json_response({"message": "User not found"}, 404)

        # Get cached dashboard stats for context
        cached_data = await redis_client.get(f"dashboard:data:{user_id}")
        stats = json.loads(cached_data) if cached_data else None

        # Find or create chat document
        chat = await chat_model.find_by_user(user_id)

        if not chat:
            # First message — save a stats snapshot
            chat = {
                "userId": ObjectId(user_id),
                "statsSnapshot": chat_model.snapshot_from_stats(stats),
                "history": [],
            }

        # Build Gemini chat with system instruction + existing history
        gemini_chat = _get_client().aio.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=build_system_prompt(user, stats)
            ),
            history=[
                types.Content(
                    role=msg["role"],
                    parts=[types.Part(text=p["text"]) for p in msg["parts"]],
                )
                for msg in chat["history"]
            ],
        )

        # Send new message
        result = await gemini_chat.send_message(message)
        response_text = result.text

        # Append both user and model messages to history
        chat["history"].append(chat_model.make_message("user", message))
        chat["history"].append(chat_model.make_message("model", response_text))

        # Keep history max 50 messages to avoid context bloat
        if len(chat["history"]) > 50:
            chat["history"] = chat["history"][len(chat["history"]) - 50:]

        await chat_model.save(chat)

        return json_response({"reply": response_text, "history": chat["history"]})
    except Exception as err:  # noqa: BLE001
        print("sendMessage Error:", err)
        return json_response({"message": "AI service error. Please try again."}, 500)


# ================= CLEAR CHAT =================
async def clearChat(request: Request, user: AuthUser):
    try:
        await chat_model.delete_by_user(user.user_id)
        return json_response({"message": "Chat cleared successfully"})
    except Exception as err:  # noqa: BLE001
        print("clearChat Error:", err)
        return json_response({"message": "Server Error"}, 500)
