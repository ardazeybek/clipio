"""Panodaki güncel içeriği okuyup (metin ya da resim) veritabanına kaydeder."""
import hashlib
import struct
from pathlib import Path

from . import clip, classify, db, paths

MIME_EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp",
            "image/gif": "gif", "image/bmp": "bmp", "image/avif": "avif"}


# Parola yöneticisinin "gizli" işaretini taşıyor mu
def is_secret(types: list[str]) -> bool:
    return "x-kde-passwordManagerHint" in types


# Panodaki metin türünü seç (yoksa None)
def _pick_text(types: list[str]) -> str | None:
    return next((t for t in clip.TEXT_TYPES if t in types), None)


# Panodaki resim türünü seç; png öncelikli (yoksa None)
def _pick_image(types: list[str]) -> str | None:
    if "image/png" in types:
        return "image/png"
    return next((t for t in types if t.startswith("image/")), None)


# PNG başlığından genişlik/yükseklik oku (başka format için 0,0)
def _png_size(data: bytes) -> tuple[int, int]:
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    return 0, 0


# Metin içeriğini kaydet
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


# Resim içeriğini diske yazıp kaydet
def _store_image(con, raw: bytes, mime: str, source: str, cfg: dict) -> int | None:
    if not raw or len(raw) > cfg["max_image_mb"] * 1024 * 1024:
        return None
    digest = hashlib.sha256(raw).hexdigest()
    name = f"{digest[:24]}.{MIME_EXT.get(mime, 'img')}"
    target = Path(paths.IMAGE_DIR) / name
    if not target.exists():
        target.write_bytes(raw)
    w, h = _png_size(raw)
    return db.upsert(con, kind="image", hash=digest, image_file=name, mime=mime,
                     width=w, height=h, size=len(raw), source=source)


# Kaydedilmemesi gereken durum mu (duraklatılmış, gizli, yok sayılan uygulama)
def _should_skip(types: list[str], source: str, cfg: dict) -> bool:
    if paths.PAUSE_FILE.exists() or is_secret(types):
        return True
    return source in cfg["ignore_apps"]


# Panoyu oku ve kaydet; yeni/yenilenen öğenin id'sini döndür (kaydedilmediyse None)
def capture(con, cfg: dict) -> int | None:
    types = clip.list_types()
    source = clip.active_class()
    if not types or _should_skip(types, source, cfg):
        return None
    text_t = _pick_text(types)
    if text_t:
        raw = clip.read(text_t)
        return _store_text(con, raw, source, cfg) if raw else None
    img_t = _pick_image(types)
    if img_t:
        raw = clip.read(img_t)
        return _store_image(con, raw, img_t, source, cfg) if raw else None
    return None
