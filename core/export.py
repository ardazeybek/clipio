"""Veritabanından arayüzün okuyacağı state.json anlık görüntüsünü üretir."""
import json
import os
import time

from . import config, db, paths

PREVIEW_CHARS = 600     # kartta gösterilecek en fazla karakter
SEARCH_CHARS = 2000     # aramada taranacak en fazla karakter


# Ayardaki dili çöz (auto ise sistem diline bak)
def _language(cfg: dict) -> str:
    if cfg["language"] != "auto":
        return cfg["language"]
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var, "")
        if val and val != "C.UTF-8":
            return "tr" if val.startswith("tr") else "en"
    return "en"


# Tek satırı arayüz için sözlüğe çevir
def _item(r) -> dict:
    text = r["text"] or ""
    return {
        "id": r["id"], "kind": r["kind"], "hint": r["hint"], "meta": r["meta"],
        "preview": text[:PREVIEW_CHARS], "search": text[:SEARCH_CHARS].lower(),
        "chars": len(text), "lines": text.count("\n") + 1 if text else 0,
        "image": str(paths.IMAGE_DIR / r["image_file"]) if r["image_file"] else "",
        "width": r["width"], "height": r["height"], "size": r["size"],
        "pinned": bool(r["pinned"]), "source": r["source"],
        "used": r["used"], "created": r["created"],
    }


# state.json dosyasını atomik olarak yeniden yaz
def write_state(con) -> None:
    cfg = config.load()
    rows = db.list_items(con)
    state = {
        "now": time.time(), "paused": paths.PAUSE_FILE.exists(),
        "retention_days": cfg["retention_days"], "lang": _language(cfg),
        "total": con.execute("SELECT COUNT(*) FROM items").fetchone()[0],
        "items": [_item(r) for r in rows],
    }
    tmp = paths.STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, paths.STATE_FILE)
