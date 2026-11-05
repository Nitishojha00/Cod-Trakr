import json
import re

from bs4 import BeautifulSoup

from config.http_client import axios_instance
from config.redis_client import redis_client
from utils.browsers import render_with_playwright, render_with_stealth


async def _save_and_return(cache_key, result):
    await redis_client.setex(cache_key, 86400, json.dumps(result))  # 1 day
    return result


def _parse(html, result):
    soup = BeautifulSoup(html, "html.parser")
    text = (soup.body or soup).get_text()

    solved_match = re.search(r"Problems\s*Solved\s*(\d+)", text, re.I)
    score_match = re.search(r"Coding\s*Score\s*(\d+)", text, re.I)

    if solved_match:
        result["solved"] = int(solved_match.group(1))
    if score_match:
        result["rating"] = int(score_match.group(1))


async def fetch_gfg(username):
    result = {"solved": 0, "rating": 0}
    cache_key = f"gfg:{username}"
    url = f"https://www.geeksforgeeks.org/profile/{username}/?tab=activity"

    # ================= CACHE CHECK =================
    cached = await redis_client.get(cache_key)
    if cached:
        print("⚡ GFG served from cache")
        return json.loads(cached)

    print(f"🔍 GFG: Attempting for {username}...")

    # ========== STRATEGY 1: HTTP + BeautifulSoup (was axios + cheerio) ==========
    try:
        async with axios_instance(timeout=10) as client:
            res = await client.get(url)
            res.raise_for_status()

        _parse(res.text, result)

        if result["solved"] > 0:
            print("✅ GFG (Cheerio success)")
            return await _save_and_return(cache_key, result)
    except Exception:  # noqa: BLE001
        print("GFG ⚠️ Cheerio failed")

    # ========== STRATEGY 2: PLAYWRIGHT ==========
    try:
        content = await render_with_playwright(url, 5000)
        _parse(content, result)

        if result["solved"] > 0:
            print("✅ GFG (Playwright success)")
            return await _save_and_return(cache_key, result)
    except Exception:  # noqa: BLE001
        print("GFG ⚠️ Playwright failed")

    # ========== STRATEGY 3: STEALTH BROWSER (was Puppeteer stealth) ==========
    try:
        content = await render_with_stealth(url, 5000)
        _parse(content, result)

        if result["solved"] > 0:
            print("✅ GFG (Puppeteer success)")
            return await _save_and_return(cache_key, result)
    except Exception:  # noqa: BLE001
        print("GFG ❌ Puppeteer failed")

    print("GFG ❌ All strategies failed")
    return result
