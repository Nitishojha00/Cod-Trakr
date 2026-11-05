import json

from config.http_client import plain_axios
from config.redis_client import redis_client


async def fetch_codeforces(username):
    result = {"solved": 0, "rating": 0, "rank": 0}

    try:
        cache_key = f"codeforces:{username}"

        # ✅ Check cache first
        cached = await redis_client.get(cache_key)
        if cached:
            print("⚡ Codeforces served from cache")
            return json.loads(cached)

        async with plain_axios() as client:
            info = await client.get(
                f"https://codeforces.com/api/user.info?handles={username}"
            )
            info.raise_for_status()
            info_data = info.json()

            if info_data.get("status") == "OK":
                result["rating"] = info_data["result"][0].get("rating") or 0
                result["rank"] = info_data["result"][0].get("maxRank") or 0

            status = await client.get(
                f"https://codeforces.com/api/user.status?handle={username}"
            )
            status.raise_for_status()
            status_data = status.json()

        if status_data.get("status") == "OK":
            solved_set = set()
            for x in status_data["result"]:
                if x.get("verdict") == "OK":
                    problem = x["problem"]
                    solved_set.add(f"{problem.get('contestId')}-{problem.get('index')}")
            result["solved"] = len(solved_set)

        # ✅ Cache for 1 day
        await redis_client.setex(cache_key, 86400, json.dumps(result))

    except Exception:  # noqa: BLE001
        print("❌ Codeforces fetch failed")

    return result
