"""Kopyalanan metnin türünü (renk, bağlantı, e-posta, kod, düz metin) tahmin eder."""
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


# Satır sonu ; { } ile biten ve girintili satırların oranından kod puanı üret
def _code_score(lines: list[str]) -> int:
    score = 0
    ends = sum(1 for l in lines if l.rstrip().endswith((";", "{", "}", ":", ")", ",")))
    indented = sum(1 for l in lines if l.startswith(("  ", "\t")))
    words = sum(1 for l in lines if _CODE_WORDS.search(l))
    score += 2 if ends >= max(2, len(lines) // 3) else 0
    score += 2 if indented >= max(2, len(lines) // 4) else 0
    score += 2 if words >= max(2, len(lines) // 3) else 0
    return score


# Tek satırlık metin için (tür, ek bilgi) çifti döndür
def _classify_single(s: str) -> tuple[str, str]:
    if _COLOR.fullmatch(s):
        return "color", s
    if _URL.match(s):
        host = urlparse(s if "//" in s else "//" + s).netloc
        return "url", host.removeprefix("www.")
    if _EMAIL.fullmatch(s):
        return "email", s.split("@", 1)[1]
    return "text", ""


# Metnin türünü ve ek bilgisini (alan adı, renk değeri vb.) döndür
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
