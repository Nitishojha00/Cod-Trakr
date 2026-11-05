"""Equivalent of models/Note.js, including mongoose-style casting/validation."""
import json
import re

from bson import ObjectId

from config.db import get_db
from utils.common import js_typeof, now_utc, num_to_str

NOTE_ORDER = [
    "problemId", "problemName", "problemDescription", "problemLink",
    "stars", "tags", "mistake", "notes", "user",
]

STRING_RULES = {
    "problemName": {"lower": True, "min": 3, "max": 100, "required": True},
    "problemDescription": {"max": 200},
    "problemLink": {"max": 200},
    "mistake": {"max": 500},
    "notes": {"max": 1000},
}

_NUM_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_OID_RE = re.compile(r"^[0-9a-fA-F]{24}$")


def notes():
    return get_db()["notes"]


class _Cast(Exception):
    pass


def _repr(v):
    try:
        return json.dumps(v)
    except Exception:  # noqa: BLE001
        return str(v)


def _cast_err(kind, path, v):
    return _Cast(
        f'Cast to {kind} failed for value {_repr(v)} (type {js_typeof(v)}) at path "{path}"'
    )


def _cast_number(path, v):
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return None
        if _NUM_RE.match(s):
            f = float(s)
            return int(f) if f.is_integer() else f
    raise _cast_err("Number", path, v)


def _cast_string(path, v):
    if v is None:
        return None
    if isinstance(v, str):
        return v
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return num_to_str(v)
    raise _cast_err("string", path, v)


def _cast_oid(path, v):
    if v is None:
        return None
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and _OID_RE.match(v):
        return ObjectId(v)
    raise _cast_err("ObjectId", path, v)


def _cast_field(path, raw):
    if path == "problemId":
        return _cast_number(path, raw)
    if path == "stars":
        return _cast_number(path, raw)
    if path == "user":
        return _cast_oid(path, raw)
    if path == "tags":
        if raw is None:
            return None
        items = raw if isinstance(raw, list) else [raw]
        return [_cast_string(path, i) for i in items]
    v = _cast_string(path, raw)
    if v is None:
        return None
    v = v.strip()
    if STRING_RULES.get(path, {}).get("lower"):
        v = v.lower()
    return v


def _validate_field(path, v):
    """Returns an error message or None (one error per path, like mongoose)."""
    if path in STRING_RULES:
        rules = STRING_RULES[path]
        if rules.get("required") and (v is None or v == ""):
            return f"Path `{path}` is required."
        if v is None:
            return None
        if "min" in rules and len(v) < rules["min"]:
            return f"Path `{path}` (`{v}`) is shorter than the minimum allowed length ({rules['min']})."
        if "max" in rules and len(v) > rules["max"]:
            return f"Path `{path}` (`{v}`) is longer than the maximum allowed length ({rules['max']})."
    elif path == "stars":
        if v is not None and v not in (0, 1, 2, 3):
            return f"{num_to_str(v)} is not a valid star rating"
    elif path == "tags":
        if v is not None and len(v) > 10:
            return "You can add maximum 10 tags"
    elif path == "user":
        if v is None:
            return "Path `user` is required."
    return None


def build_for_create(data: dict, **forced):
    """new Note({...data, ...forced}).save() -> document dict (or raises)."""
    merged = {**data, **forced}
    doc, errors = {}, {}
    for path in NOTE_ORDER:
        raw = merged.get(path)
        try:
            val = _cast_field(path, raw) if path in merged else None
        except _Cast as e:
            errors[path] = str(e)
            continue
        if path == "stars" and val is None:
            val = 0
        if path == "tags" and val is None:
            val = []
        err = _validate_field(path, val)
        if err:
            errors[path] = err
            continue
        if val is not None:
            doc[path] = val
    if errors:
        raise Exception(
            "Note validation failed: " + ", ".join(f"{p}: {m}" for p, m in errors.items())
        )
    now = now_utc()
    doc["createdAt"] = now
    doc["updatedAt"] = now
    doc["__v"] = 0
    return doc


def build_for_update(data: dict):
    """Mirror of findOneAndUpdate(..., body, {runValidators:true})."""
    set_doc, errors = {}, {}
    for path in NOTE_ORDER:
        if path not in data:
            continue
        try:
            val = _cast_field(path, data[path])
        except _Cast as e:
            raise Exception(f'{e} for model "Note"')
        err = _validate_field(path, val)
        if err:
            errors[path] = err
            continue
        set_doc[path] = val
    if errors:
        raise Exception(
            "Validation failed: " + ", ".join(f"{p}: {m}" for p, m in errors.items())
        )
    set_doc["updatedAt"] = now_utc()
    return set_doc
