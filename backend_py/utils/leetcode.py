import json

import httpx

from config.http_client import axios_instance
from config.redis_client import redis_client


async def fetch_leetcode(username):
    result = {"solved": 0, "rating": 0, "rank": 0, "contests": 0}

    try:
        cache_key = f"leetcode:{username}"

        # Cache Check
        cached = await redis_client.get(cache_key)
        if cached:
            print("⚡ LeetCode served from cache")
            return json.loads(cached)

        query = """
      query getUser($username:String!){
        matchedUser(username:$username){
          profile{
            ranking
          }
          submitStats{
            acSubmissionNum{
              difficulty
              count
            }
          }
        }
        userContestRanking(username:$username){
          rating
          attendedContestsCount
        }
      }
    """

        async with axios_instance(timeout=15, headers={"Content-Type": "application/json"}) as client:
            res = await client.post(
                "https://leetcode.com/graphql",
                json={"query": query, "variables": {"username": username}},
            )
            res.raise_for_status()
            data = res.json()

        data_obj = (data or {}).get("data") or {}
        user = data_obj.get("matchedUser")
        contest = data_obj.get("userContestRanking")

        if not user:
            print("❌ Invalid LeetCode username")
            return result

        all_solved = next(
            (
                item
                for item in ((user.get("submitStats") or {}).get("acSubmissionNum") or [])
                if item.get("difficulty") == "All"
            ),
            None,
        )

        result["solved"] = (all_solved or {}).get("count") or 0
        result["rank"] = (user.get("profile") or {}).get("ranking") or 0
        result["rating"] = int((contest or {}).get("rating") or 0)  # Math.floor
        result["contests"] = (contest or {}).get("attendedContestsCount") or 0

        # Cache for 24 hours
        await redis_client.setex(cache_key, 86400, json.dumps(result))

        print("✅ LeetCode fetched & cached")
        return result
    except httpx.HTTPStatusError as err:
        try:
            detail = err.response.json()
        except Exception:  # noqa: BLE001
            detail = err.response.text
        print("❌ LeetCode fetch failed:", detail or str(err))
        return result
    except Exception as err:  # noqa: BLE001
        print("❌ LeetCode fetch failed:", str(err))
        return result
