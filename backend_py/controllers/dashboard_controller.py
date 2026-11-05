import asyncio
import copy
import math

from fastapi import Request

from middlewares.auth import AuthUser
from models.user import find_by_id, update_platforms
from utils.codechef import fetch_codechef
from utils.codeforces import fetch_codeforces
from utils.common import get_json_body, js_number, json_response
from utils.gfg import fetch_gfg
from utils.leetcode import fetch_leetcode

# ================= FETCH PLATFORM STATS =================


async def fetch_real_time_stats(platforms):
    try:
        stats = copy.deepcopy(platforms)
        tasks = []

        def has_username(key):
            p = stats.get(key)
            return isinstance(p, dict) and p.get("username")

        async def run(name, coro, apply):
            try:
                apply(await coro)
            except Exception as err:  # noqa: BLE001
                print(f"{name} Error:", str(err))

        if has_username("LeetCode"):
            tasks.append(run("LeetCode", fetch_leetcode(stats["LeetCode"]["username"]),
                             lambda res: stats["LeetCode"].update(res)))

        if has_username("Codeforces"):
            tasks.append(run("Codeforces", fetch_codeforces(stats["Codeforces"]["username"]),
                             lambda res: stats["Codeforces"].update(res)))

        if has_username("CodeChef"):
            def apply_cc(res):
                stats["CodeChef"]["solved"] = res.get("solved") or 0
                stats["CodeChef"]["rating"] = res.get("rating") or 0

            tasks.append(run("CodeChef", fetch_codechef(stats["CodeChef"]["username"]), apply_cc))

        if has_username("GFG"):
            tasks.append(run("GFG", fetch_gfg(stats["GFG"]["username"]),
                             lambda res: stats["GFG"].update(res)))

        await asyncio.gather(*tasks, return_exceptions=True)
        return stats

    except Exception as error:  # noqa: BLE001
        print("fetchRealTimeStats Fatal Error:", str(error))
        return platforms


# ================= AGGREGATION =================


def build_dashboard_response(platforms):
    try:
        total_solved = 0
        total_contests = 0
        best_rating = 0
        platform_count = 0

        for key in platforms:
            platform = platforms[key]

            if not (isinstance(platform, dict) and platform.get("username")):
                continue

            platform_count += 1

            total_solved += js_number(platform.get("solved") or 0)
            total_contests += js_number(platform.get("contests") or 0)

            rating = js_number(platform.get("rating") or 0)

            if not (isinstance(rating, float) and math.isnan(rating)):
                best_rating = max(best_rating, rating)

        return {
            "platforms": platforms,
            "totalSolved": total_solved,
            "totalContests": total_contests,
            "bestRating": best_rating,
            "platformCount": platform_count,
        }

    except Exception as error:  # noqa: BLE001
        print("buildDashboardResponse Error:", str(error))
        return {
            "platforms": platforms,
            "totalSolved": 0,
            "totalContests": 0,
            "bestRating": 0,
            "platformCount": 0,
        }


# ================= CONTROLLERS =================


async def getMe(request: Request, user: AuthUser):
    try:
        doc = await find_by_id(user.user_id, include_password=False)
        return json_response(doc)
    except Exception as err:  # noqa: BLE001
        print(err)
        return json_response({"message": "Server Error"}, 500)


async def saveAccounts(request: Request, user: AuthUser):
    try:
        body = await get_json_body(request)
        platforms = body.get("platforms")

        await update_platforms(user.user_id, platforms)

        return json_response({"message": "Saved"})
    except Exception as err:  # noqa: BLE001
        print(err)
        return json_response({"message": "Server Error"}, 500)


async def getDashboard(request: Request, user: AuthUser):
    try:
        doc = await find_by_id(user.user_id)

        if not doc:
            return json_response({"message": "User not found"}, 404)

        live_platforms = await fetch_real_time_stats(doc["platforms"])

        response_data = build_dashboard_response(live_platforms)

        return json_response(response_data)
    except Exception as err:  # noqa: BLE001
        print("Dashboard Error:", err)
        return json_response({"message": "Server Error"}, 500)
