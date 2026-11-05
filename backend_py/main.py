from dotenv import load_dotenv

load_dotenv()

import os  # noqa: E402
import sys  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from config import db  # noqa: E402
from config.redis_client import redis_client  # noqa: E402
from middlewares.auth import Unauthorized  # noqa: E402
from routes.auth_route import router as auth_route  # noqa: E402
from routes.chat_route import router as chat_route  # noqa: E402
from routes.dash_route import router as dash_router  # noqa: E402
from routes.notes_routes import router as note_router  # noqa: E402
from utils.browsers import close_browsers  # noqa: E402
from utils.common import iso, json_response, now_utc  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== InitializeConnection =====
    try:
        await db.main()
        print("MongoDB Connected")

        # Redis is optional; the server can still start without it.
        try:
            await redis_client.ping()
            print("Redis Connected")
        except Exception as redis_err:  # noqa: BLE001
            print("Redis connection failed:", str(redis_err))

        port = os.getenv("PORT") or 4000
        print(f"Server listening on port {port}")
    except Exception as err:  # noqa: BLE001
        print("Critical startup error:", err)
        sys.exit(1)

    yield

    # ===== shutdown =====
    await close_browsers()
    try:
        await redis_client.aclose()
    except Exception:  # noqa: BLE001
        pass
    await db.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://codtrakr.nitishojha.in",
        "http://127.0.0.1:5500",
        "https://cod-trakr.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "HEAD", "PUT", "PATCH", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.exception_handler(Unauthorized)
async def unauthorized_handler(request, exc):
    return JSONResponse({"message": "Unauthorized"}, status_code=401)


# API routes
app.include_router(auth_route, prefix="/api/auth")
app.include_router(dash_router, prefix="/api/dashboard")
app.include_router(note_router, prefix="/api/notes")
app.include_router(chat_route, prefix="/api/chat")


@app.post("/logout")
async def logout():
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("token", path="/", samesite=None)  # like Express clearCookie("token")
    return response


# Health check for UptimeRobot
@app.get("/health")
async def health():
    status = {
        "server": "ok",
        "mongodb": "unknown",
        "redis": "unknown",
        "timestamp": iso(now_utc()),
    }

    print("Health check requested by UptimeRobot at", status["timestamp"])
    try:
        await db.get_db().command("ping")
        status["mongodb"] = "ok"
    except RuntimeError:
        status["mongodb"] = "disconnected"
    except Exception:  # noqa: BLE001
        status["mongodb"] = "error"

    try:
        await redis_client.ping()
        status["redis"] = "ok"
    except Exception:  # noqa: BLE001
        status["redis"] = "error"

    healthy = status["mongodb"] == "ok" and status["redis"] == "ok"

    return json_response(status, 200 if healthy else 503)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT") or 4000))
