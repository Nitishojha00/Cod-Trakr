from fastapi import APIRouter, Depends, Request

from controllers import note_controller as c
from middlewares.auth import AuthUser, auth

router = APIRouter()


@router.post("/new")
async def new(request: Request, user: AuthUser = Depends(auth)):
    return await c.createProblem(request, user)


@router.get("/problem")
async def problem(request: Request, user: AuthUser = Depends(auth)):
    return await c.getAllProblem(request, user)


@router.get("/problemByImportance")
async def problem_by_importance(request: Request, user: AuthUser = Depends(auth)):
    return await c.getElementByImportance(request, user)


@router.get("/problemById/{problem_id}")
async def problem_by_id(problem_id: str, request: Request, user: AuthUser = Depends(auth)):
    return await c.getSingleProblem(problem_id, request, user)


@router.put("/problem/{problem_id}")
async def update_problem(problem_id: str, request: Request, user: AuthUser = Depends(auth)):
    return await c.updateProblem(problem_id, request, user)


@router.delete("/problem/{problem_id}")
async def delete_problem(problem_id: str, request: Request, user: AuthUser = Depends(auth)):
    return await c.deleteProblem(problem_id, request, user)


# FILTERS
@router.get("/tag/{tag}")
async def by_tag(tag: str, request: Request, user: AuthUser = Depends(auth)):
    return await c.getElementByTag(tag, request, user)


@router.get("/stars/{stars}")
async def by_stars(stars: str, request: Request, user: AuthUser = Depends(auth)):
    return await c.getElementBySpecificStar(stars, request, user)
