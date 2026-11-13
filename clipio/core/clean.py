"""Cleans copied text: removes tracking parameters from links and tidies whitespace."""
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Query parameters that only track clicks (exact names)
TRACKING = {
    "fbclid", "gclid", "gclsrc", "dclid", "msclkid", "yclid", "igshid", "mc_cid", "mc_eid",
    "_ga", "_gl", "ref_src", "ref_url", "spm", "si", "mkt_tok", "oly_anon_id", "oly_enc_id",
    "vero_id", "wickedid", "twclid", "ttclid", "li_fat_id", "s_cid", "trk", "trkCampaign",
}
# Query parameter prefixes that only track clicks
TRACKING_PREFIXES = ("utm_", "pk_", "hsa_", "__hs", "mtm_")

_URL = re.compile(r"https?://[^\s<>\"']+", re.I)


# True when a query parameter is a known tracker
def _is_tracker(name: str) -> bool:
    n = name.lower()
    return n in TRACKING or n.startswith(TRACKING_PREFIXES)


# Remove tracking parameters from one link (other parts stay as they were)
def clean_url(url: str) -> str:
    try:
        parts = urlsplit(url)
    except ValueError:
        return url
    if not parts.query:
        return url
    params = parse_qsl(parts.query, keep_blank_values=True)
    kept = [(k, v) for k, v in params if not _is_tracker(k)]
    if len(kept) == len(params):
        return url
    return urlunsplit(parts._replace(query=urlencode(kept, doseq=True)))


# Clean every link inside a text
def clean_links(text: str) -> str:
    return _URL.sub(lambda m: clean_url(m.group(0)), text)


# Tidy whitespace: trim each line, drop trailing spaces, squeeze 3+ blank lines into one
def tidy_whitespace(text: str) -> str:
    lines = [l.rstrip() for l in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return out.strip()


# Join lines broken in the middle of a sentence (copied from PDFs) into one paragraph each
def join_lines(text: str) -> str:
    paragraphs = re.split(r"\n\s*\n", tidy_whitespace(text))
    return "\n\n".join(re.sub(r"\s*\n\s*", " ", p) for p in paragraphs)


# Everything a "clean paste" does: links, whitespace and doubled spaces
def clean_text(text: str) -> str:
    return re.sub(r"[ \t]{2,}", " ", tidy_whitespace(clean_links(text)))
