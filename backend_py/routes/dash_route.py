from fastapi import APIRouter, Depends, Request

from controllers import dashboard_controller as c
from middlewares.auth import AuthUser, auth

router = APIRouter()


@router.get("/me")
async def me(request: Request, user: AuthUser = Depends(auth)):
    return await c.getMe(request, user)


@router.post("/accounts")
async def accounts(request: Request, user: AuthUser = Depends(auth)):
    return await c.saveAccounts(request, user)


@router.get("/dashboard")
async def dashboard(request: Request, user: AuthUser = Depends(auth)):
    return await c.getDashboard(request, user)
