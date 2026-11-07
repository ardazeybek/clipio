"""Builds the state the panel shows (items, pause state, retention) from the database."""
import time

from . import config, db, paths

PREVIEW_CHARS = 600     # most characters shown on a card
SEARCH_CHARS = 2000     # most characters searched


# Turn one database row into a plain dict for the panel
def item(r) -> dict:
    text = r["text"] or ""
    image = (paths.image_dir() / r["image_file"]).as_uri() if r["image_file"] else ""
    return {
        "id": r["id"], "kind": r["kind"], "hint": r["hint"], "meta": r["meta"],
        "preview": text[:PREVIEW_CHARS], "search": text[:SEARCH_CHARS].lower(),
        "chars": len(text), "lines": text.count("\n") + 1 if text else 0,
        "image": image, "width": r["width"], "height": r["height"], "size": r["size"],
        "pinned": bool(r["pinned"]), "source": r["source"],
        "used": r["used"], "created": r["created"],
    }


# Return the full panel state
def build_state(con, cfg: dict | None = None) -> dict:
    cfg = cfg or config.load()
    return {
        "now": time.time(), "paused": paths.pause_file().exists(),
        "retention_days": cfg["retention_days"],
        "total": con.execute("SELECT COUNT(*) FROM items").fetchone()[0],
        "items": [item(r) for r in db.list_items(con)],
    }
