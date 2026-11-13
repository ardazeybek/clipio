"""Fetches the <title> of a copied web page in the background (only when link_titles is on)."""
import html
import re
import threading
import urllib.request

_TITLE = re.compile(rb"<title[^>]*>(.*?)</title>", re.I | re.S)
MAX_BYTES = 200_000
TIMEOUT = 5


# Download the start of a page and return its title ('' on failure)
def fetch(url: str) -> str:
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Clipio link preview)"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            if "html" not in r.headers.get("Content-Type", ""):
                return ""
            body = r.read(MAX_BYTES)
            charset = r.headers.get_content_charset() or "utf-8"
    except Exception:   # network errors, bad certificates, odd servers: no title
        return ""
    m = _TITLE.search(body)
    if not m:
        return ""
    title = html.unescape(m.group(1).decode(charset, "replace"))
    return " ".join(title.split())[:200]


# Fetch the title in a thread and call done(title) there when one was found
def fetch_async(url: str, done) -> None:
    def work():
        title = fetch(url)
        if title:
            done(title)
    threading.Thread(target=work, daemon=True).start()
