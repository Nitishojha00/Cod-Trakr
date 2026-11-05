import httpx

# Equivalent of config/axiosConfig.js (shared default browser-like headers)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def axios_instance(timeout=None, headers=None):
    """httpx client that behaves like the axios instance (follows redirects;
    call raise_for_status() to get axios' throw-on-non-2xx behaviour)."""
    merged = dict(DEFAULT_HEADERS)
    if headers:
        merged.update(headers)
    return httpx.AsyncClient(headers=merged, timeout=timeout, follow_redirects=True)


def plain_axios(timeout=None, headers=None):
    """Plain `axios` (no default headers)."""
    return httpx.AsyncClient(headers=headers or {}, timeout=timeout, follow_redirects=True)
