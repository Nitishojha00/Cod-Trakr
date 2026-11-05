import json
import re

from bs4 import BeautifulSoup

from config.http_client import plain_axios
from config.redis_client import redis_client
from utils.browsers import render_with_playwright, render_with_stealth
from utils.common import js_parse_int

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"


async def _save_and_return(cache_key, result):
    await redis_client.setex(cache_key, 86400, json.dumps(result))  # 1 day
    return result


def _parse(html, result):
    soup = BeautifulSoup(html, "html.parser")

    el = soup.select_one(".rating-number")
    rating_text = el.get_text().strip() if el else ""
    if rating_text:
        result["rating"] = js_parse_int(rating_text) or 0

    body = soup.body or soup
    text = body.get_text()
    match = re.search(r"Total Problems Solved:\s*(\d+)", text, re.I) or re.search(
        r"Fully Solved\s*\((\d+)\)", text, re.I
    )
    if match:
        result["solved"] = int(match.group(1))


async def fetch_codechef(user):
    result = {"solved": 0, "rating": 0}
    url = f"https://www.codechef.com/users/{user}"
    cache_key = f"codechef:{user}"

    # ================= CACHE CHECK =================
    cached = await redis_client.get(cache_key)
    if cached:
        print("⚡ CodeChef served from cache")
        return json.loads(cached)

    print(f"🔍 CODECHEF: Attempting for {user}...")

    # ========== STRATEGY 1: HTTP + BeautifulSoup (was axios + cheerio) ==========
    try:
        async with plain_axios(
            timeout=10,
            headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
        ) as client:
            res = await client.get(url)
            res.raise_for_status()

        _parse(res.text, result)

        if result["rating"] > 0 or result["solved"] > 0:
            print("✅ CODECHEF (Axios success)")
            return await _save_and_return(cache_key, result)
    except Exception:  # noqa: BLE001
        print("Codechef ⚠️ Axios failed, trying Playwright...")

    # ========== STRATEGY 2: PLAYWRIGHT ==========
    try:
        content = await render_with_playwright(url, 4000)
        _parse(content, result)

        if result["rating"] > 0 or result["solved"] > 0:
            print("✅ CODECHEF (Playwright success)")
            return await _save_and_return(cache_key, result)
    except Exception:  # noqa: BLE001
        print("Codechef ⚠️ Playwright failed, trying Puppeteer...")

    # ========== STRATEGY 3: STEALTH BROWSER (was Puppeteer stealth) ==========
    try:
        content = await render_with_stealth(url, 4000)
        _parse(content, result)

        if result["rating"] > 0 or result["solved"] > 0:
            print("✅ CODECHEF (Puppeteer success)")
            return await _save_and_return(cache_key, result)
    except Exception:  # noqa: BLE001
        print("❌ Codechef Puppeteer failed")

    print("❌ Codechef All strategies failed")
    return result
