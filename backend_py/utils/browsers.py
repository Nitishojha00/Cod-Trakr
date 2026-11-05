"""
Headless-browser helpers shared by the CodeChef and GFG scrapers.

Node used two browser libraries (Playwright, then puppeteer-extra + stealth).
Python has no maintained puppeteer-extra, so strategy 3 is Playwright Chromium
with the `playwright-stealth` patches applied (same idea: stealth fallback).
"""
import asyncio

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

STEALTH_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"
)

_pw = None
_playwright_browser = None
_stealth_browser = None
_lock = asyncio.Lock()


async def _get_pw():
    global _pw
    if _pw is None:
        _pw = await async_playwright().start()
    return _pw


async def get_playwright():
    global _playwright_browser
    async with _lock:
        if _playwright_browser is None:
            pw = await _get_pw()
            _playwright_browser = await pw.chromium.launch(headless=True)
        return _playwright_browser


async def get_puppeteer():
    """The 'stealth' browser (was puppeteer-extra in Node)."""
    global _stealth_browser
    async with _lock:
        if _stealth_browser is None:
            pw = await _get_pw()
            _stealth_browser = await pw.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
        return _stealth_browser


async def render_with_playwright(url, wait_ms):
    browser = await get_playwright()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(wait_ms)
        return await page.content()
    finally:
        await page.close()


async def render_with_stealth(url, wait_ms):
    browser = await get_puppeteer()
    context = await browser.new_context(user_agent=STEALTH_UA)
    try:
        await Stealth().apply_stealth_async(context)
        page = await context.new_page()
        # puppeteer's "networkidle2" has no Playwright equivalent; "networkidle" is the closest
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(wait_ms)
        return await page.content()
    finally:
        await context.close()


async def close_browsers():
    global _pw, _playwright_browser, _stealth_browser
    for b in (_playwright_browser, _stealth_browser):
        try:
            if b:
                await b.close()
        except Exception:  # noqa: BLE001
            pass
    _playwright_browser = _stealth_browser = None
    if _pw:
        try:
            await _pw.stop()
        except Exception:  # noqa: BLE001
            pass
        _pw = None
