"""Guesses what a copied text is: a color, link, email address, code or plain text."""
import re
from urllib.parse import urlparse

_COLOR = re.compile(
    r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})"
    r"|(?:rgb|hsl)a?\(\s*[\d.%,\s/-]+\)"
)
_URL = re.compile(r"^(?:https?|ftp)://\S+$|^www\.\S+\.\S+$", re.I)
_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+(?:\.[\w-]+)+$")
_CODE_WORDS = re.compile(
    r"\b(def|class|function|const|let|var|import|from|return|public|private|"
    r"fn|impl|struct|enum|if|else|elif|for|while)\b|=>|->|</?\w+>|#include|\$\(|::"
)


# Score how code-like the lines are (line endings, indentation, keywords)
def _code_score(lines: list[str]) -> int:
    score = 0
    ends = sum(1 for l in lines if l.rstrip().endswith((";", "{", "}", ":", ")", ",")))
    indented = sum(1 for l in lines if l.startswith(("  ", "\t")))
    words = sum(1 for l in lines if _CODE_WORDS.search(l))
    score += 2 if ends >= max(2, len(lines) // 3) else 0
    score += 2 if indented >= max(2, len(lines) // 4) else 0
    score += 2 if words >= max(2, len(lines) // 3) else 0
    return score


# Return (kind, extra info) for a single-line text
def _classify_single(s: str) -> tuple[str, str]:
    if _COLOR.fullmatch(s):
        return "color", s
    if _URL.match(s):
        host = urlparse(s if "//" in s else "//" + s).netloc
        return "url", host[4:] if host.startswith("www.") else host
    if _EMAIL.fullmatch(s):
        return "email", s.split("@", 1)[1]
    return "text", ""


# Return the text's kind and extra info (domain name, color value and so on)
def classify(text: str) -> tuple[str, str]:
    s = text.strip()
    if "\n" not in s:
        kind, meta = _classify_single(s)
        if kind != "text":
            return kind, meta
    lines = [l for l in s.splitlines() if l.strip()]
    if len(lines) >= 3 and _code_score(lines) >= 4:
        return "code", ""
    return "text", ""
