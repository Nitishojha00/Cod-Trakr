import json
import math

from bson import ObjectId
from fastapi import Request
from pymongo.errors import DuplicateKeyError

from config.redis_client import redis_client
from middlewares.auth import AuthUser
from models.note import build_for_create, build_for_update, notes
from utils.common import dumps, get_json_body, js_number, js_parse_int, json_response, to_jsonable

PAGE_LIMIT = 8
LIST_FIELDS = ["problemId", "problemName", "tags", "problemLink", "stars"]


def _dup_message(e):
    return (e.details or {}).get("errmsg") or str(e)


# ==================================================
#    HELPER: SAFE NOTES CACHE INVALIDATION
#    Matches "notes:all", "notes:importance", "note:single" ...
#    ONE function clears EVERYTHING for that user.
# ==================================================
async def clear_user_cache(user_id):
    try:
        if not user_id:
            return

        keys_to_delete = []
        async for key in redis_client.scan_iter(match=f"note*:{user_id}:*", count=100):
            keys_to_delete.append(key)

        if keys_to_delete:
            await redis_client.delete(*keys_to_delete)
    except Exception as err:  # noqa: BLE001
        print("Redis Clear Error:", err)


def _page_from(request: Request):
    return js_parse_int(request.query_params.get("page")) or 1


async def _query_notes(query, sort, projection, skip, limit):
    cursor = notes().find(query, projection).sort(sort).skip(skip).limit(limit)
    items = await cursor.to_list(length=None)
    total = await notes().count_documents(query)
    return items, total


def _paged_response(page, total, items):
    return {
        "success": True,
        "page": page,
        "totalProblems": total,
        "totalPages": math.ceil(total / PAGE_LIMIT),
        "count": len(items),
        "data": items,
    }


# ==================================================
#    HELPER: FETCH & CACHE (Reusable)
# ==================================================
async def fetch_and_cache_notes(query, user_id, page, limit, cache_key):
    try:
        skip = (page - 1) * limit
        projection = {f: 1 for f in ["problemId", "problemName", "tags", "problemLink", "stars"]}
        items, total = await _query_notes(query, [("problemId", 1)], projection, skip, limit)

        response = _paged_response(page, total, items)

        # Cache for 24 hours (SWR strategy)
        await redis_client.set(cache_key, dumps(response), ex=86400)

        return response
    except Exception as error:  # noqa: BLE001
        print("fetchAndCacheNotes Error:", str(error))
        return {
            "success": False,
            "page": page,
            "totalProblems": 0,
            "totalPages": 0,
            "count": 0,
            "data": [],
            "error": str(error),
        }


# ================= CONTROLLERS =================

# 1. CREATE NEW PROBLEM
async def createProblem(request: Request, auth: AuthUser):
    try:
        user_id = auth.user_id
        body = await get_json_body(request)

        raw_name = body.get("problemName")
        if raw_name is None:
            problem_name = None
        elif isinstance(raw_name, str):
            problem_name = raw_name.strip().lower()
        else:
            raise Exception("req.body.problemName?.trim is not a function")

        user_oid = ObjectId(user_id)

        # Check Duplicate
        existing = await notes().find_one({"problemName": problem_name, "user": user_oid})
        if existing:
            return json_response({"success": False, "message": "Problem already exists"}, 409)

        # Generate ID
        last_problem = await notes().find_one(
            {"user": user_oid}, {"problemId": 1}, sort=[("problemId", -1)]
        )
        current_max_id = (last_problem or {}).get("problemId") or 0

        if current_max_id >= 50:
            return json_response({"success": False, "message": "Limit reached (50)"}, 409)

        doc = build_for_create(
            body,
            problemName=problem_name,
            problemId=current_max_id + 1,
            user=user_oid,
        )
        try:
            result = await notes().insert_one(doc)
        except DuplicateKeyError as e:
            raise Exception(_dup_message(e))
        doc["_id"] = result.inserted_id

        # INSTANT UPDATE: Clears "All" AND "Importance" lists
        await clear_user_cache(user_id)

        return json_response({"success": True, "data": doc}, 201)
    except Exception as err:  # noqa: BLE001
        return json_response({"success": False, "message": str(err)}, 400)


# 2. GET ALL PROBLEMS (SWR Cached)
async def getAllProblem(request: Request, auth: AuthUser):
    try:
        user_id = auth.user_id
        page = _page_from(request)
        limit = PAGE_LIMIT

        cache_key = f"notes:all:{user_id}:{page}"

        # 1. Check Cache
        cached = await redis_client.get(cache_key)
        if cached:
            return json_response(json.loads(cached))

        # 2. Fetch & Cache
        query = {"user": ObjectId(user_id)}
        data = await fetch_and_cache_notes(query, user_id, page, limit, cache_key)

        return json_response(data, 200)
    except Exception as err:  # noqa: BLE001
        return json_response({"success": False, "message": str(err)}, 500)


# 3. GET SINGLE PROBLEM (SWR Cached)
async def getSingleProblem(problemId: str, request: Request, auth: AuthUser):
    try:
        user_id = auth.user_id
        problem_id = js_number(problemId)
        if isinstance(problem_id, float) and math.isnan(problem_id):
            return json_response({"success": False, "message": "Invalid ID"}, 400)

        cache_key = f"note:{user_id}:{problem_id}"

        # 1. Check Cache
        cached = await redis_client.get(cache_key)
        if cached:
            return json_response({"success": True, "data": json.loads(cached)})

        # 2. DB Fetch
        note = await notes().find_one({"user": ObjectId(user_id), "problemId": problem_id})
        if not note:
            return json_response({"success": False, "message": "Not found"}, 404)

        # 3. Cache
        await redis_client.set(cache_key, dumps(note), ex=86400)

        return json_response({"success": True, "data": note}, 200)
    except Exception as err:  # noqa: BLE001
        return json_response({"success": False, "message": str(err)}, 500)


# 4. UPDATE PROBLEM
async def updateProblem(problemId: str, request: Request, auth: AuthUser):
    try:
        from pymongo import ReturnDocument

        user_id = auth.user_id
        problem_id = js_number(problemId)
        if isinstance(problem_id, float) and math.isnan(problem_id):
            return json_response({"success": False, "message": "Invalid ID"}, 400)

        body = await get_json_body(request)
        set_doc = build_for_update(body)

        try:
            updated = await notes().find_one_and_update(
                {"user": ObjectId(user_id), "problemId": problem_id},
                {"$set": set_doc},
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError as e:
            raise Exception(_dup_message(e))

        if not updated:
            return json_response({"success": False, "message": "Problem not found"}, 404)

        # INSTANT UPDATE: Clears "All", "Importance", and "Single" caches
        await clear_user_cache(user_id)

        return json_response({"success": True, "data": updated}, 200)
    except Exception as err:  # noqa: BLE001
        return json_response({"success": False, "message": str(err)}, 400)


# 5. DELETE PROBLEM
async def deleteProblem(problemId: str, request: Request, auth: AuthUser):
    try:
        user_id = auth.user_id
        problem_id = js_number(problemId)
        if isinstance(problem_id, float) and math.isnan(problem_id):
            return json_response({"success": False, "message": "Invalid ID"}, 400)

        deleted = await notes().find_one_and_delete(
            {"user": ObjectId(user_id), "problemId": problem_id}
        )
        if not deleted:
            return json_response({"success": False, "message": "Problem not found"}, 404)

        # INSTANT UPDATE: Clears everything so it disappears from lists
        await clear_user_cache(user_id)

        return json_response({"success": True, "message": "Deleted successfully"}, 200)
    except Exception as err:  # noqa: BLE001
        return json_response({"success": False, "message": str(err)}, 500)


# 6. GET BY IMPORTANCE (SWR Cached)
async def getElementByImportance(request: Request, auth: AuthUser):
    try:
        user_id = auth.user_id
        page = _page_from(request)
        limit = PAGE_LIMIT

        cache_key = f"notes:importance:{user_id}:{page}"

        # 1. Check Cache
        cached = await redis_client.get(cache_key)
        if cached:
            return json_response(json.loads(cached))

        # 2. Fetch & Cache
        query = {"user": ObjectId(user_id)}

        skip = (page - 1) * limit
        projection = {f: 1 for f in LIST_FIELDS}
        items, total = await _query_notes(
            query, [("stars", -1), ("problemId", 1)], projection, skip, limit
        )

        response = _paged_response(page, total, items)

        await redis_client.set(cache_key, dumps(response), ex=86400)

        return json_response(response, 200)
    except Exception as err:  # noqa: BLE001
        return json_response({"success": False, "message": str(err)}, 500)


# 7. GET BY TAG (With Pagination & Caching)
async def getElementByTag(tag: str, request: Request, auth: AuthUser):
    try:
        user_id = auth.user_id
        page = _page_from(request)
        limit = PAGE_LIMIT
        skip = (page - 1) * limit

        cache_key = f"notes:tag:{user_id}:{tag}:{page}"

        # 1. Check Cache
        cached = await redis_client.get(cache_key)
        if cached:
            return json_response(json.loads(cached))

        # 2. DB Fetch & Count
        query = {"tags": {"$in": [tag]}, "user": ObjectId(user_id)}

        projection = {f: 1 for f in LIST_FIELDS}
        items, total = await _query_notes(
            query, [("stars", -1), ("problemId", 1)], projection, skip, limit
        )

        response = _paged_response(page, total, items)

        # 3. Cache
        await redis_client.set(cache_key, dumps(response), ex=86400)

        return json_response(response, 200)
    except Exception as err:  # noqa: BLE001
        return json_response({"success": False, "message": str(err)}, 500)


# 8. GET BY SPECIFIC STAR (With Pagination & Caching)
async def getElementBySpecificStar(stars: str, request: Request, auth: AuthUser):
    try:
        user_id = auth.user_id
        stars_n = js_parse_int(stars)
        page = _page_from(request)
        limit = PAGE_LIMIT
        skip = (page - 1) * limit

        cache_key = f"notes:stars:{user_id}:{'NaN' if stars_n is None else stars_n}:{page}"

        # 1. Check Cache
        cached = await redis_client.get(cache_key)
        if cached:
            return json_response(json.loads(cached))

        # 2. DB Fetch & Count
        if stars_n is None:
            raise Exception(
                'Cast to Number failed for value "NaN" (type number) at path "stars" for model "Note"'
            )
        query = {"stars": stars_n, "user": ObjectId(user_id)}

        projection = {f: 1 for f in LIST_FIELDS}
        items, total = await _query_notes(
            query, [("updatedAt", -1)], projection, skip, limit
        )

        response = _paged_response(page, total, items)

        # 3. Cache
        await redis_client.set(cache_key, dumps(response), ex=86400)

        return json_response(response, 200)
    except Exception as err:  # noqa: BLE001
        return json_response({"success": False, "message": str(err)}, 500)
