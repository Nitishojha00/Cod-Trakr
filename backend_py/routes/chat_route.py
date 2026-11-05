from fastapi import APIRouter, Depends, Request

from controllers import chat_controller as c
from middlewares.auth import AuthUser, auth

# All routes are protected
router = APIRouter(dependencies=[Depends(auth)])


# GET  /api/chat/history  -> load previous conversation
@router.get("/history")
async def history(request: Request, user: AuthUser = Depends(auth)):
    return await c.getChatHistory(request, user)


# POST /api/chat/send     -> send a message and get AI reply
@router.post("/send")
async def send(request: Request, user: AuthUser = Depends(auth)):
    return await c.sendMessage(request, user)


# DELETE /api/chat/clear  -> clear conversation history
@router.delete("/clear")
async def clear(request: Request, user: AuthUser = Depends(auth)):
    return await c.clearChat(request, user)
