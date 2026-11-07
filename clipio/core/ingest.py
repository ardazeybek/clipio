"""Saves a clipboard snapshot (text or image) from any platform backend to the database."""
import hashlib
import struct
from dataclasses import dataclass, field

from . import classify, db, paths

MIME_EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp",
            "image/gif": "gif", "image/bmp": "bmp", "image/avif": "avif"}

# Markers that password managers put on secret copies (Linux, macOS, Windows)
SECRET_MARKERS = ("x-kde-passwordManagerHint", "org.nspasteboard.ConcealedType",
                  "ExcludeClipboardContentFromMonitorProcessing")


@dataclass
class Snapshot:
    """What was on the clipboard at one moment, as read by a platform backend."""
    formats: list[str] = field(default_factory=list)
    text: bytes | None = None
    image: bytes | None = None
    image_mime: str = "image/png"

    # True when nothing usable is on the clipboard
    def is_empty(self) -> bool:
        return not self.text and not self.image


# True when a password manager marked the copy as secret
def is_secret(formats: list[str]) -> bool:
    return any(m in f for f in formats for m in SECRET_MARKERS)


# Read width and height from a PNG header (0, 0 for other formats)
def png_size(data: bytes) -> tuple[int, int]:
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    return 0, 0


# Save a text item
def _store_text(con, raw: bytes, source: str, cfg: dict) -> int | None:
    if len(raw) > cfg["max_text_kb"] * 1024:
        return None
    text = raw.decode("utf-8", errors="replace")
    if not text.strip():
        return None
    hint, meta = classify.classify(text)
    digest = hashlib.sha256(raw).hexdigest()
    return db.upsert(con, kind="text", hash=digest, text=text, hint=hint, meta=meta,
                     size=len(raw), source=source)


# Write an image to disk and save it
def _store_image(con, raw: bytes, mime: str, source: str, cfg: dict) -> int | None:
    if not raw or len(raw) > cfg["max_image_mb"] * 1024 * 1024:
        return None
    digest = hashlib.sha256(raw).hexdigest()
    name = f"{digest[:24]}.{MIME_EXT.get(mime, 'img')}"
    target = paths.image_dir() / name
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    w, h = png_size(raw)
    return db.upsert(con, kind="image", hash=digest, image_file=name, mime=mime,
                     width=w, height=h, size=len(raw), source=source)


# True when this copy must not be saved (paused, secret or from an ignored app)
def should_skip(snap: Snapshot, source: str, cfg: dict) -> bool:
    if paths.pause_file().exists() or is_secret(snap.formats):
        return True
    ignored = {a.lower() for a in cfg["ignore_apps"]}
    return bool(source) and source.lower() in ignored


# Save a snapshot; return the new or refreshed item id (None when nothing was saved)
def capture(con, snap: Snapshot, source: str, cfg: dict) -> int | None:
    if snap.is_empty() or should_skip(snap, source, cfg):
        return None
    if snap.text:
        return _store_text(con, snap.text, source, cfg)
    return _store_image(con, snap.image, snap.image_mime, source, cfg)
