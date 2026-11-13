"""Spots copied secrets (card numbers, API keys, tokens, private keys) so they can be hidden and expire."""
import re

_KEY_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk|pk|rk)_(?:live|test)_[0-9a-zA-Z]{16,}\b"),        # Stripe
    re.compile(r"\bsk-(?:ant-|proj-)?[0-9A-Za-z_-]{20,}\b"),               # OpenAI / Anthropic style
    re.compile(r"\bgh[pousr]_[0-9A-Za-z]{30,}\b"),                          # GitHub
    re.compile(r"\bgithub_pat_[0-9A-Za-z_]{40,}\b"),
    re.compile(r"\bglpat-[0-9A-Za-z_-]{20,}\b"),                            # GitLab
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                                    # AWS access key
    re.compile(r"\bxox[abpors]-[0-9A-Za-z-]{10,}\b"),                       # Slack
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),                               # Google API
    re.compile(r"\beyJ[0-9A-Za-z_-]{8,}\.eyJ[0-9A-Za-z_-]{8,}\.[0-9A-Za-z_-]{8,}\b"),  # JWT
]
_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[0-9A-Z]{4}){3,7}(?: ?[0-9A-Z]{1,4})?\b")


# Luhn checksum used by payment cards
def _luhn(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


# True when the text holds a valid-looking card number
def _has_card(text: str) -> bool:
    for m in _CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn(digits) and len(set(digits)) > 1:
            return True
    return False


# True for a short single word that looks like a generated password
def _looks_like_password(text: str) -> bool:
    s = text.strip()
    if not (10 <= len(s) <= 64) or any(c.isspace() for c in s) or "/" in s or "@" in s:
        return False
    classes = sum([any(c.islower() for c in s), any(c.isupper() for c in s),
                   any(c.isdigit() for c in s), any(not c.isalnum() for c in s)])
    return classes >= 4


# True when a copied text is probably a secret
def is_sensitive(text: str) -> bool:
    if not text or len(text) > 20000:
        return False
    if any(p.search(text) for p in _KEY_PATTERNS):
        return True
    return _has_card(text) or bool(_IBAN.search(text)) or _looks_like_password(text)
