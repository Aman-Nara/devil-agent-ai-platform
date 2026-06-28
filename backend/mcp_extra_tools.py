"""
Extra MCP tools — pure-compute, no network, no filesystem side effects.
Auto-registered by mcp_module._bootstrap() via the `register_extra_tools` hook.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import random
import re
import string
import time
import uuid
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Any, Dict


async def _t_base64_encode(p: Dict[str, Any]) -> Dict[str, Any]:
    text = str(p.get("text", ""))
    return {"ok": True, "result": base64.b64encode(text.encode("utf-8")).decode("ascii")}


async def _t_base64_decode(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        out = base64.b64decode(str(p.get("text", "")).encode("ascii")).decode("utf-8", errors="replace")
        return {"ok": True, "result": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_url_encode(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "result": urllib.parse.quote(str(p.get("text", "")), safe="")}


async def _t_url_decode(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "result": urllib.parse.unquote(str(p.get("text", "")))}


async def _t_hash_md5(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "result": hashlib.md5(str(p.get("text", "")).encode()).hexdigest()}


async def _t_hash_sha1(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "result": hashlib.sha1(str(p.get("text", "")).encode()).hexdigest()}


async def _t_hash_sha256(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "result": hashlib.sha256(str(p.get("text", "")).encode()).hexdigest()}


async def _t_hash_sha512(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "result": hashlib.sha512(str(p.get("text", "")).encode()).hexdigest()}


async def _t_uuid_gen(p: Dict[str, Any]) -> Dict[str, Any]:
    n = max(1, min(50, int(p.get("count", 1))))
    return {"ok": True, "result": [str(uuid.uuid4()) for _ in range(n)]}


async def _t_timestamp_now(p: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {"ok": True, "result": {"iso": now.isoformat(), "unix": int(now.timestamp()), "unix_ms": int(now.timestamp() * 1000)}}


async def _t_timestamp_parse(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        v = p.get("value")
        if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()):
            ts = float(v)
            if ts > 1e12:
                ts /= 1000.0
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return {"ok": True, "result": {"iso": dt.isoformat(), "unix": int(dt.timestamp()), "year": dt.year, "month": dt.month, "day": dt.day, "weekday": dt.strftime("%A")}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_date_diff(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        d1 = datetime.fromisoformat(str(p.get("from", "")).replace("Z", "+00:00"))
        d2 = datetime.fromisoformat(str(p.get("to", "")).replace("Z", "+00:00"))
        diff = d2 - d1
        return {"ok": True, "result": {"days": diff.days, "seconds": int(diff.total_seconds()), "hours": int(diff.total_seconds() // 3600)}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_age_calc(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        dob = datetime.fromisoformat(str(p.get("dob", "")).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        years = now.year - dob.year - ((now.month, now.day) < (dob.month, dob.day))
        return {"ok": True, "result": {"years": years, "days": (now - dob).days}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_json_format(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        v = p.get("text") if isinstance(p.get("text"), str) else json.dumps(p.get("text"))
        parsed = json.loads(v)
        return {"ok": True, "result": json.dumps(parsed, indent=int(p.get("indent", 2)), ensure_ascii=False)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_json_validate(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        json.loads(str(p.get("text", "")))
        return {"ok": True, "result": {"valid": True}}
    except Exception as e:
        return {"ok": True, "result": {"valid": False, "error": str(e)}}


async def _t_json_minify(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        parsed = json.loads(str(p.get("text", "")))
        return {"ok": True, "result": json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_regex_match(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        pat = re.compile(str(p.get("pattern", "")))
        matches = pat.findall(str(p.get("text", "")))
        return {"ok": True, "result": {"matches": matches, "count": len(matches)}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_regex_replace(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        out = re.sub(str(p.get("pattern", "")), str(p.get("replacement", "")), str(p.get("text", "")))
        return {"ok": True, "result": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_word_count(p: Dict[str, Any]) -> Dict[str, Any]:
    text = str(p.get("text", ""))
    return {"ok": True, "result": {"words": len(text.split()), "chars": len(text), "chars_no_space": len(text.replace(" ", "")), "lines": text.count("\n") + (1 if text else 0)}}


async def _t_text_case(p: Dict[str, Any]) -> Dict[str, Any]:
    text = str(p.get("text", ""))
    return {"ok": True, "result": {"upper": text.upper(), "lower": text.lower(), "title": text.title(), "swapcase": text.swapcase()}}


async def _t_text_reverse(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "result": str(p.get("text", ""))[::-1]}


async def _t_slugify(p: Dict[str, Any]) -> Dict[str, Any]:
    text = str(p.get("text", "")).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return {"ok": True, "result": text}


async def _t_password_gen(p: Dict[str, Any]) -> Dict[str, Any]:
    length = max(4, min(128, int(p.get("length", 16))))
    alphabet = string.ascii_letters + string.digits
    if p.get("symbols", True):
        alphabet += "!@#$%^&*()-_=+[]{}"
    return {"ok": True, "result": "".join(random.SystemRandom().choice(alphabet) for _ in range(length))}


async def _t_lorem_ipsum(p: Dict[str, Any]) -> Dict[str, Any]:
    words = ("lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
             "incididunt ut labore et dolore magna aliqua enim ad minim veniam quis nostrud "
             "exercitation ullamco laboris nisi aliquip ex ea commodo consequat duis aute "
             "irure reprehenderit in voluptate velit esse cillum fugiat nulla pariatur").split()
    n = max(1, min(500, int(p.get("words", 50))))
    return {"ok": True, "result": " ".join(random.choice(words) for _ in range(n)).capitalize() + "."}


async def _t_math_eval(p: Dict[str, Any]) -> Dict[str, Any]:
    expr = str(p.get("expression", ""))
    if not re.fullmatch(r"[\d\s\+\-\*\/\.\(\)\%\^]+", expr):
        return {"ok": False, "error": "Only numbers and + - * / % ^ ( ) allowed"}
    try:
        result = eval(expr.replace("^", "**"), {"__builtins__": {}}, {})
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_calc_percent(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        value = float(p.get("value", 0))
        percent = float(p.get("percent", 0))
        return {"ok": True, "result": {"of": value * percent / 100, "increase": value * (1 + percent / 100), "decrease": value * (1 - percent / 100)}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_calc_tip(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        bill = float(p.get("bill", 0))
        pct = float(p.get("percent", 15))
        people = max(1, int(p.get("people", 1)))
        tip = bill * pct / 100
        total = bill + tip
        return {"ok": True, "result": {"tip": round(tip, 2), "total": round(total, 2), "per_person": round(total / people, 2)}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_dice_roll(p: Dict[str, Any]) -> Dict[str, Any]:
    sides = max(2, min(1000, int(p.get("sides", 6))))
    count = max(1, min(50, int(p.get("count", 1))))
    rolls = [random.randint(1, sides) for _ in range(count)]
    return {"ok": True, "result": {"rolls": rolls, "sum": sum(rolls)}}


async def _t_coin_flip(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "result": random.choice(["heads", "tails"])}


async def _t_random_pick(p: Dict[str, Any]) -> Dict[str, Any]:
    items = p.get("items", [])
    if not isinstance(items, list) or not items:
        return {"ok": False, "error": "items must be a non-empty list"}
    return {"ok": True, "result": random.choice(items)}


async def _t_html_strip(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "result": re.sub(r"<[^>]+>", "", str(p.get("text", "")))}


async def _t_jwt_decode(p: Dict[str, Any]) -> Dict[str, Any]:
    token = str(p.get("token", ""))
    parts = token.split(".")
    if len(parts) < 2:
        return {"ok": False, "error": "Invalid JWT"}
    try:
        pad = lambda s: s + "=" * (-len(s) % 4)
        header = json.loads(base64.urlsafe_b64decode(pad(parts[0])).decode())
        payload = json.loads(base64.urlsafe_b64decode(pad(parts[1])).decode())
        return {"ok": True, "result": {"header": header, "payload": payload}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_color_convert(p: Dict[str, Any]) -> Dict[str, Any]:
    hex_color = str(p.get("hex", "")).lstrip("#")
    if len(hex_color) not in (3, 6):
        return {"ok": False, "error": "hex must be 3 or 6 chars"}
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return {"ok": True, "result": {"hex": f"#{hex_color}", "rgb": f"rgb({r},{g},{b})", "r": r, "g": g, "b": b}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_unit_convert(p: Dict[str, Any]) -> Dict[str, Any]:
    """Simple unit conversions: length, weight, temperature."""
    try:
        value = float(p.get("value", 0))
        kind = str(p.get("kind", "")).lower()
        f, t = str(p.get("from", "")).lower(), str(p.get("to", "")).lower()
        tables = {
            "length": {"m": 1, "km": 1000, "cm": 0.01, "mm": 0.001, "mi": 1609.34, "ft": 0.3048, "in": 0.0254, "yd": 0.9144},
            "weight": {"kg": 1, "g": 0.001, "lb": 0.453592, "oz": 0.0283495, "ton": 1000},
        }
        if kind == "temperature":
            c = value if f == "c" else (value - 32) * 5 / 9 if f == "f" else value - 273.15
            out = c if t == "c" else c * 9 / 5 + 32 if t == "f" else c + 273.15
            return {"ok": True, "result": round(out, 4)}
        if kind in tables and f in tables[kind] and t in tables[kind]:
            return {"ok": True, "result": round(value * tables[kind][f] / tables[kind][t], 6)}
        return {"ok": False, "error": "Unsupported unit/kind"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_bmi_calc(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        h = float(p.get("height_m", 0))
        w = float(p.get("weight_kg", 0))
        bmi = w / (h * h)
        cat = "Underweight" if bmi < 18.5 else "Normal" if bmi < 25 else "Overweight" if bmi < 30 else "Obese"
        return {"ok": True, "result": {"bmi": round(bmi, 2), "category": cat}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_compound_interest(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        principal = float(p.get("principal", 0))
        rate = float(p.get("rate", 0)) / 100
        years = float(p.get("years", 0))
        n = int(p.get("compounds_per_year", 12))
        amount = principal * (1 + rate / n) ** (n * years)
        return {"ok": True, "result": {"final_amount": round(amount, 2), "interest_earned": round(amount - principal, 2)}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _t_csv_to_json(p: Dict[str, Any]) -> Dict[str, Any]:
    try:
        import csv, io
        reader = csv.DictReader(io.StringIO(str(p.get("text", ""))))
        return {"ok": True, "result": list(reader)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


EXTRA_TOOLS = [
    ("base64_encode", "text", "safe", "Encode UTF-8 text to base64.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_base64_encode),
    ("base64_decode", "text", "safe", "Decode base64 to UTF-8 text.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_base64_decode),
    ("url_encode", "text", "safe", "Percent-encode a string for URLs.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_url_encode),
    ("url_decode", "text", "safe", "Decode a percent-encoded URL string.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_url_decode),
    ("hash_md5", "crypto", "safe", "MD5 hash of input text.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_hash_md5),
    ("hash_sha1", "crypto", "safe", "SHA-1 hash of input text.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_hash_sha1),
    ("hash_sha256", "crypto", "safe", "SHA-256 hash of input text.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_hash_sha256),
    ("hash_sha512", "crypto", "safe", "SHA-512 hash of input text.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_hash_sha512),
    ("uuid_gen", "utility", "safe", "Generate UUID v4 values.", {"type": "object", "properties": {"count": {"type": "integer"}}}, _t_uuid_gen),
    ("timestamp_now", "datetime", "safe", "Current UTC timestamp (ISO/unix).", {"type": "object", "properties": {}}, _t_timestamp_now),
    ("timestamp_parse", "datetime", "safe", "Parse ISO or unix timestamp.", {"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"]}, _t_timestamp_parse),
    ("date_diff", "datetime", "safe", "Difference between two ISO datetimes.", {"type": "object", "properties": {"from": {"type": "string"}, "to": {"type": "string"}}, "required": ["from", "to"]}, _t_date_diff),
    ("age_calc", "datetime", "safe", "Calculate age from date of birth (ISO).", {"type": "object", "properties": {"dob": {"type": "string"}}, "required": ["dob"]}, _t_age_calc),
    ("json_format", "text", "safe", "Pretty-print a JSON string.", {"type": "object", "properties": {"text": {"type": "string"}, "indent": {"type": "integer"}}, "required": ["text"]}, _t_json_format),
    ("json_validate", "text", "safe", "Validate a JSON string.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_json_validate),
    ("json_minify", "text", "safe", "Minify a JSON string.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_json_minify),
    ("regex_match", "text", "safe", "Find all regex matches in text.", {"type": "object", "properties": {"pattern": {"type": "string"}, "text": {"type": "string"}}, "required": ["pattern", "text"]}, _t_regex_match),
    ("regex_replace", "text", "safe", "Regex replace in text.", {"type": "object", "properties": {"pattern": {"type": "string"}, "replacement": {"type": "string"}, "text": {"type": "string"}}, "required": ["pattern", "replacement", "text"]}, _t_regex_replace),
    ("word_count", "text", "safe", "Count words, chars, and lines.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_word_count),
    ("text_case", "text", "safe", "Show upper/lower/title/swap variants.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_text_case),
    ("text_reverse", "text", "safe", "Reverse a string.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_text_reverse),
    ("slugify", "text", "safe", "Convert text to URL slug.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_slugify),
    ("password_gen", "crypto", "low", "Generate a strong random password.", {"type": "object", "properties": {"length": {"type": "integer"}, "symbols": {"type": "boolean"}}}, _t_password_gen),
    ("lorem_ipsum", "text", "safe", "Generate Lorem Ipsum filler text.", {"type": "object", "properties": {"words": {"type": "integer"}}}, _t_lorem_ipsum),
    ("math_eval", "math", "safe", "Evaluate a basic numeric expression.", {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}, _t_math_eval),
    ("calc_percent", "math", "safe", "Percentage calculations.", {"type": "object", "properties": {"value": {"type": "number"}, "percent": {"type": "number"}}, "required": ["value", "percent"]}, _t_calc_percent),
    ("calc_tip", "math", "safe", "Tip & split calculator.", {"type": "object", "properties": {"bill": {"type": "number"}, "percent": {"type": "number"}, "people": {"type": "integer"}}, "required": ["bill"]}, _t_calc_tip),
    ("dice_roll", "fun", "safe", "Roll N dice with S sides.", {"type": "object", "properties": {"sides": {"type": "integer"}, "count": {"type": "integer"}}}, _t_dice_roll),
    ("coin_flip", "fun", "safe", "Flip a coin.", {"type": "object", "properties": {}}, _t_coin_flip),
    ("random_pick", "fun", "safe", "Randomly pick from a list.", {"type": "object", "properties": {"items": {"type": "array"}}, "required": ["items"]}, _t_random_pick),
    ("html_strip", "text", "safe", "Strip HTML tags from text.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_html_strip),
    ("jwt_decode", "crypto", "safe", "Decode a JWT (no signature check).", {"type": "object", "properties": {"token": {"type": "string"}}, "required": ["token"]}, _t_jwt_decode),
    ("color_convert", "utility", "safe", "Convert hex color to RGB.", {"type": "object", "properties": {"hex": {"type": "string"}}, "required": ["hex"]}, _t_color_convert),
    ("unit_convert", "utility", "safe", "Length/weight/temperature conversions.", {"type": "object", "properties": {"kind": {"type": "string"}, "from": {"type": "string"}, "to": {"type": "string"}, "value": {"type": "number"}}, "required": ["kind", "from", "to", "value"]}, _t_unit_convert),
    ("bmi_calc", "health", "safe", "BMI from height (m) and weight (kg).", {"type": "object", "properties": {"height_m": {"type": "number"}, "weight_kg": {"type": "number"}}, "required": ["height_m", "weight_kg"]}, _t_bmi_calc),
    ("compound_interest", "finance", "safe", "Compound interest calculator.", {"type": "object", "properties": {"principal": {"type": "number"}, "rate": {"type": "number"}, "years": {"type": "number"}, "compounds_per_year": {"type": "integer"}}, "required": ["principal", "rate", "years"]}, _t_compound_interest),
    ("csv_to_json", "data", "safe", "Convert CSV text to JSON.", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}, _t_csv_to_json),
]
