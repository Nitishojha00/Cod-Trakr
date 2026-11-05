"""Small helpers that reproduce JS / Express / Mongoose behaviours."""
import json
import math
import re
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import Request
from fastapi.responses import JSONResponse

_NUM_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_INT_PREFIX_RE = re.compile(r"^\s*([+-]?\d+)")


def js_typeof(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "Array"
    return "Object"


def js_parse_int(value):
    """parseInt(x) -> int or None (NaN)."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return int(value)
    m = _INT_PREFIX_RE.match(str(value))
    return int(m.group(1)) if m else None


def js_number(value):
    """Number(x) -> int/float, or float('nan')."""
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if s == "":
            return 0
        if _NUM_RE.match(s):
            f = float(s)
            return int(f) if f.is_integer() else f
    return float("nan")


def num_to_str(v):
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def iso(dt: datetime) -> str:
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_jsonable(o):
    """ObjectId -> str, datetime -> ISO string (like mongoose toJSON)."""
    if isinstance(o, ObjectId):
        return str(o)
    if isinstance(o, datetime):
        return iso(o)
    if isinstance(o, dict):
        return {k: to_jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_jsonable(v) for v in o]
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    return o


def json_response(content, status_code=200):
    return JSONResponse(content=to_jsonable(content), status_code=status_code)


def dumps(data) -> str:
    return json.dumps(to_jsonable(data))


async def get_json_body(request: Request) -> dict:
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return {}
    return body if isinstance(body, dict) else {}
