"""Quick text conversions offered in a card's menu (case, JSON, Base64, colors, links)."""
import base64
import binascii
import json
import re
from urllib.parse import quote, unquote

from . import clean

_HEX = re.compile(r"^#?([0-9a-f]{3}|[0-9a-f]{6})$", re.I)
_RGB = re.compile(r"^rgba?\(\s*(\d{1,3})[,\s]+(\d{1,3})[,\s]+(\d{1,3})", re.I)


# Pretty-print JSON (None when the text is not JSON)
def _json_pretty(s: str) -> str | None:
    try:
        return json.dumps(json.loads(s), indent=2, ensure_ascii=False)
    except ValueError:
        return None


# Minify JSON
def _json_min(s: str) -> str | None:
    try:
        return json.dumps(json.loads(s), separators=(",", ":"), ensure_ascii=False)
    except ValueError:
        return None


# Decode Base64 into UTF-8 text
def _b64_decode(s: str) -> str | None:
    try:
        raw = base64.b64decode(s.strip() + "=" * (-len(s.strip()) % 4), validate=True)
        return raw.decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None


# #RRGGBB (or #RGB) -> rgb(r, g, b)
def _hex_to_rgb(s: str) -> str | None:
    m = _HEX.match(s.strip())
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgb({r}, {g}, {b})"


# rgb(r, g, b) -> #RRGGBB
def _rgb_to_hex(s: str) -> str | None:
    m = _RGB.match(s.strip())
    if not m:
        return None
    vals = [min(255, int(v)) for v in m.groups()]
    return "#" + "".join(f"{v:02X}" for v in vals)


# Capitalize each word (Turkish-aware for i/İ is out of scope; uses str.title rules)
def _title(s: str) -> str:
    return re.sub(r"\w+", lambda m: m.group(0)[:1].upper() + m.group(0)[1:].lower(), s)


# name -> conversion; each returns the new text or None when it does not apply
TRANSFORMS = {
    "upper": str.upper,
    "lower": str.lower,
    "title": _title,
    "clean": clean.clean_text,
    "join_lines": clean.join_lines,
    "json_pretty": _json_pretty,
    "json_min": _json_min,
    "base64_encode": lambda s: base64.b64encode(s.encode()).decode(),
    "base64_decode": _b64_decode,
    "url_encode": lambda s: quote(s, safe=""),
    "url_decode": unquote,
    "hex_to_rgb": _hex_to_rgb,
    "rgb_to_hex": _rgb_to_hex,
}


# Run one conversion; None when it is unknown, fails, or changes nothing
def apply(name: str, text: str) -> str | None:
    fn = TRANSFORMS.get(name)
    if fn is None or not text:
        return None
    out = fn(text)
    return out if out and out != text else None


# Names of the conversions that work on this text (shown in the menu)
def available(text: str) -> list[str]:
    return [n for n in TRANSFORMS if apply(n, text[:20000]) is not None]
