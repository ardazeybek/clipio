"""Builds the state the panel shows (items, pause state, retention) from the database."""
import time

from . import config, db, highlight, paths, template

PREVIEW_CHARS = 600     # most characters shown on a card
SEARCH_CHARS = 2000     # most characters searched


# Turn one database row into a plain dict for the panel (colors: color code cards)
def item(r, colors: bool = True) -> dict:
    text = r["text"] or ""
    image = (paths.image_dir() / r["image_file"]).as_uri() if r["image_file"] else ""
    return {
        "id": r["id"], "kind": r["kind"], "hint": r["hint"], "meta": r["meta"],
        "preview": text[:PREVIEW_CHARS], "search": text[:SEARCH_CHARS].lower(),
        "chars": len(text), "lines": text.count("\n") + 1 if text else 0,
        "image": image, "width": r["width"], "height": r["height"], "size": r["size"],
        "pinned": bool(r["pinned"]), "source": r["source"],
        "tag": r["tag"], "secret": bool(r["secret"]), "title": r["title"],
        "rich": highlight.to_rich(text[:PREVIEW_CHARS]) if colors and r["hint"] == "code" else "",
        "template": bool(r["pinned"]) and template.has_placeholders(text),
        "used": r["used"], "created": r["created"],
    }


# Return the full panel state (ocr_available: the OCR tool is installed)
def build_state(con, cfg: dict | None = None, ocr_available: bool = False) -> dict:
    cfg = cfg or config.load()
    return {
        "now": time.time(), "paused": paths.pause_file().exists(),
        "retention_days": cfg["retention_days"], "panel_keep_minutes": cfg["panel_keep_minutes"],
        "features": {k: cfg[k] for k in config.FEATURES},
        "shortcuts": {a: cfg[f"key_{a}"] for a in config.SHORTCUTS},
        "default_shortcuts": config.SHORTCUTS,
        "secret_minutes": cfg["secret_minutes"], "ignore_apps": cfg["ignore_apps"],
        "tags": db.tags(con), "ocr": ocr_available,
        "total": con.execute("SELECT COUNT(*) FROM items").fetchone()[0],
        "items": [item(r, cfg["code_colors"]) for r in db.list_items(con)],
    }
